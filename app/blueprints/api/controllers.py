import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, session, send_file, abort, current_app
from extensions import db, socketio
from app.models.session_model import PhotoSession
from app.models.admin_model import AppSetting
from app.services.camera_service import CameraService
from app.services.collage_service import CollageService
from app.services.drive_service import GoogleDriveService
from app.services.gif_service import GifService
from werkzeug.utils import secure_filename

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Lazy singletons — tidak di-init di level modul
_camera_service = None
collage_service = CollageService()
drive_service = GoogleDriveService()
gif_service = GifService()

# Folder-folder yang diizinkan untuk serve_file
_ALLOWED_FILE_TYPES = {'collages', 'gifs', 'temp', 'templates'}
# Extension yang diizinkan untuk di-serve
_ALLOWED_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

def get_camera():
    global _camera_service
    if _camera_service is None:
        _camera_service = CameraService()
    return _camera_service


def _get_storage_path():
    """Kembalikan path absolut ke folder storage private."""
    return current_app.config.get(
        'PRIVATE_STORAGE_PATH',
        os.path.join(current_app.root_path, '..', 'storage')
    )


@api_bp.route('/files/<file_type>/<filename>')
def serve_file(file_type, filename):
    """
    Endpoint aman untuk menyajikan file dari private storage.
    Akses publik langsung via URL bar atau hotlinking DILARANG TOTAL (403 Forbidden).
    Hanya klien dengan otorisasi aktif (Admin, Host Kios, Bilboard, atau sesi Galeri aktif)
    yang diizinkan mengakses file.
    """
    # Validasi file_type
    if file_type not in _ALLOWED_FILE_TYPES:
        abort(403)

    # Sanitasi nama file — cegah path traversal
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        abort(403)

    # Validasi ekstensi
    _, ext = os.path.splitext(safe_name.lower())
    if ext not in _ALLOWED_EXTS:
        abort(403)

    # Cek otorisasi klien
    is_admin = session.get('admin_logged_in', False)
    is_host = session.get('host_access', False)
    is_bilboard = session.get('bilboard_access', False)

    # Validasi Referer jika ada (mencegah hotlinking dari domain luar)
    referrer = request.referrer or ''
    host_url = request.host_url.rstrip('/')
    if referrer and not referrer.startswith(host_url):
        abort(403)

    if file_type == 'templates':
        # Template bingkai hanya boleh diakses oleh Admin, Host Kios, atau Remote HP yang aktif
        has_mobile_access = session.get('mobile_access', False)
        if not is_admin and not is_host and not has_mobile_access:
            abort(403)

    elif not is_admin and not is_host and not is_bilboard:
        # Untuk collages, gifs, dan temp (foto mentah):
        # Mencegah akses publik URL langsung tanpa melalui halaman galeri resmi
        code = request.args.get('code', '').strip()
        if not code:
            abort(403)

        # Wajib memiliki otorisasi sesi browser yang valid untuk kode ini
        has_gallery_auth = (
            session.get(f'gallery_access_{code}') is True or
            session.get('allowed_gallery_code') == code
        )
        if not has_gallery_auth:
            # Akses publik langsung tanpa session galeri ditolak!
            abort(403)

        photo_session = PhotoSession.query.filter_by(unique_code=code).first()
        if not photo_session:
            abort(403)

        # Pastikan file memang milik sesi ini
        if file_type == 'collages' and photo_session.collage_path != safe_name:
            abort(403)
        elif file_type == 'gifs' and photo_session.gif_path != safe_name:
            abort(403)
        elif file_type == 'temp':
            try:
                raw_list = json.loads(photo_session.raw_photos_json or '[]')
            except Exception:
                raw_list = []
            if safe_name not in raw_list:
                abort(403)

    # Build path absolut dan verifikasi file ada
    storage_path = _get_storage_path()
    file_path = os.path.abspath(os.path.join(storage_path, file_type, safe_name))
    base_dir = os.path.abspath(os.path.join(storage_path, file_type))

    # Cegah path traversal: pastikan file benar-benar di dalam base_dir
    if not file_path.startswith(base_dir + os.sep):
        abort(403)

    if not os.path.exists(file_path):
        abort(404)

    return send_file(file_path)


@api_bp.route('/pair', methods=['POST'])
def pair_device():
    data = request.get_json() or {}
    code = data.get('code')

    if not code:
        return jsonify({'success': False, 'message': 'Kode unik diperlukan.'}), 400

    # Cari sesi berdasarkan kode unik yang statusnya waiting atau connected
    session = PhotoSession.query.filter_by(unique_code=code).first()

    if session and session.status in ['waiting', 'connected']:
        session.status = 'connected'
        db.session.commit()

        # Kirim sinyal broadcast via WebSocket ke layar Host
        socketio.emit('device_paired', {'code': code})

        return jsonify({'success': True, 'message': 'Berhasil terhubung ke Booth!'}), 200
    else:
        return jsonify({'success': False, 'message': 'Kode unik tidak valid atau sesi sudah selesai.'}), 400


@api_bp.route('/session-options', methods=['GET'])
def get_session_options():
    """Mengembalikan opsi template nyata dari database & filesystem untuk Mobile Remote."""
    storage_path = _get_storage_path()
    template_dir = os.path.join(storage_path, 'templates')
    custom_templates = []
    if os.path.exists(template_dir):
        custom_templates = [f for f in sorted(os.listdir(template_dir)) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]

    setting_active = AppSetting.query.filter_by(key='active_custom_template').first()
    active_tpl = setting_active.value if setting_active else 'default'

    return jsonify({
        'active_template': active_tpl,
        'custom_templates': custom_templates,
    })


@socketio.on('preview_filter_change')
def handle_preview_filter_change(data):
    filter_name = data.get('filter', 'classic')
    code = data.get('code')
    get_camera().set_preview_filter(filter_name)
    socketio.emit('filter_updated', {'filter': filter_name, 'code': code})


@socketio.on('session_disconnect')
def handle_session_disconnect(data):
    """Dipanggil ketika pengguna meninggalkan halaman mobile remote.
    PIN sesi langsung diexpired agar tidak bisa dipakai ulang.
    """
    import random
    code = data.get('code')
    if not code:
        return

    session = PhotoSession.query.filter_by(unique_code=code, status='connected').first()
    if not session:
        # Juga tangani status waiting (belum pernah capture)
        session = PhotoSession.query.filter_by(unique_code=code, status='waiting').first()
    if session:
        session.status = 'expired'
        db.session.commit()

    # Reset filter kamera ke natural
    try:
        get_camera().set_preview_filter('classic')
    except Exception:
        pass

    # Broadcast ke monitor agar langsung buat PIN baru
    socketio.emit('session_expired_by_remote', {'old_code': code})


@socketio.on('start_capture_session')
def handle_capture(data):
    code = data.get('code')
    filter_type = data.get('filter', 'classic')
    timer = int(data.get('timer', 3))
    template_name = data.get('template', 'default')

    session = PhotoSession.query.filter_by(unique_code=code).first()
    if not session:
        socketio.emit('capture_error', {'message': 'Sesi tidak ditemukan di database.', 'code': code})
        return

    # Hitung jumlah jepretan yang dibutuhkan oleh template ini
    total_shots = collage_service.get_template_slot_count(template_name)
    captured_images = []

    for i in range(total_shots):
        # 1. Kirim sinyal hitung mundur ke Host dan Mobile
        socketio.emit('trigger_countdown', {
            'shot': i + 1,
            'total': total_shots,
            'timer': timer,
            'code': code
        })
        socketio.sleep(timer)

        # 2. Ambil foto definitif via OpenCV Camera Service
        filepath, error = get_camera().capture_frame(filter_type)
        if error or not filepath:
            socketio.emit('capture_error', {'message': error or 'Gagal mengambil foto.', 'code': code})
            return

        captured_images.append(filepath)

        # 3. Beritahu Host untuk memicu kilat flash dan status
        socketio.emit('shot_completed', {
            'shot': i + 1,
            'total': total_shots,
            'code': code
        })
        socketio.sleep(1.5)

    # 4. Render kolase foto akhir
    socketio.emit('processing_collage', {'code': code, 'message': 'Sedang merangkai kolase foto Anda...'})
    collage_path, collage_error = collage_service.create_collage(captured_images, template_name=template_name)

    if collage_error or not collage_path:
        socketio.emit('capture_error', {'message': collage_error or 'Gagal merender kolase.', 'code': code})
        return

    # 4b. Buat Animasi GIF jika fitur GIF diaktifkan di Admin Settings
    gif_filename = None
    try:
        setting_gif = AppSetting.query.filter_by(key='enable_gif').first()
        is_gif_enabled = (setting_gif.value == '1') if setting_gif else True
        if is_gif_enabled:
            gif_path, gif_error = gif_service.create_gif(captured_images, session_code=code)
            if gif_path:
                gif_filename = os.path.basename(gif_path)
    except Exception as e:
        print(f"Peringatan pembuatan GIF: {e}")

    # 5. SIMPAN KE DATABASE SECARA REALTIME
    try:
        session.status = 'completed'
        session.template_name = template_name
        session.collage_path = os.path.basename(collage_path)
        session.gif_path = gif_filename
        session.raw_photos_json = json.dumps([os.path.basename(p) for p in captured_images])
        session.completed_at = datetime.now()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving completed session to DB: {e}")

    # 6. Upload Google Drive (jika ada konfigurasi)
    drive_link = None
    try:
        drive_link = drive_service.upload_file(collage_path)
    except Exception:
        drive_link = None

    # 7. Sinyal Selesai -> Redirect Host dan Mobile secara serempak ke Galeri
    redirect_url = f"/gallery/{code}"
    socketio.emit('session_finished', {
        'code': code,
        'redirect_url': redirect_url,
        'drive_link': drive_link
    })

    # Reset filter preview kamera kembali ke standar/classic untuk pelanggan berikutnya
    try:
        get_camera().set_preview_filter('classic')
        socketio.emit('filter_updated', {'filter': 'classic', 'code': code})
    except Exception:
        pass