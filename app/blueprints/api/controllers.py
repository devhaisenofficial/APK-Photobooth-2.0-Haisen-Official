import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from extensions import db, socketio
from app.models.session_model import PhotoSession
from app.models.admin_model import AppSetting
from app.services.camera_service import CameraService
from app.services.collage_service import CollageService
from app.services.drive_service import GoogleDriveService
from app.services.gif_service import GifService

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Lazy singletons — tidak di-init di level modul
_camera_service = None
collage_service = CollageService()
drive_service = GoogleDriveService()
gif_service = GifService()

def get_camera():
    global _camera_service
    if _camera_service is None:
        _camera_service = CameraService()
    return _camera_service


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
    template_dir = os.path.join('app', 'static', 'uploads', 'templates')
    custom_templates = []
    if os.path.exists(template_dir):
        custom_templates = [f for f in sorted(os.listdir(template_dir)) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]

    setting_active = AppSetting.query.filter_by(key='active_custom_template').first()
    active_tpl = setting_active.value if setting_active else 'default'

    return jsonify({
        'active_template': active_tpl,
        'custom_templates': custom_templates,
    })


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