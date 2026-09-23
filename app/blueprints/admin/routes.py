import os
import json
import shutil
import time
import zipfile
import io
import re
from datetime import datetime, date
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_required
from extensions import db, socketio
from app.models.session_model import PhotoSession
from app.models.admin_model import AppSetting
from app.services.camera_service import CameraService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../../templates')

# Waktu server mulai (uptime)
_SERVER_START_TIME = time.time()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_ZIP_ITEMS = 60


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_safe_code(code):
    """Pastikan parameter kode hanya alfanumerik bebas path traversal."""
    return bool(code and isinstance(code, str) and re.match(r'^[A-Za-z0-9_-]{1,16}$', code.strip()))


def is_safe_file_in_dir(base_dir, filename):
    """Memastikan file berada tepat di dalam direktori yang diizinkan dan berformat gambar aman."""
    if not filename or not isinstance(filename, str):
        return False
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        return False
    if not allowed_file(safe_name):
        return False
    abs_base = os.path.abspath(base_dir)
    abs_target = os.path.abspath(os.path.join(base_dir, safe_name))
    return abs_target.startswith(abs_base + os.sep) and os.path.exists(abs_target)


def get_setting(key, default=''):
    s = AppSetting.query.filter_by(key=key).first()
    return s.value if s else default


def set_setting(key, value):
    s = AppSetting.query.filter_by(key=key).first()
    if s:
        s.value = value
    else:
        db.session.add(AppSetting(key=key, value=value))
    db.session.commit()


# ─────────────────────────────────────────────
# HALAMAN UTAMA
# ─────────────────────────────────────────────

@admin_bp.route('/', strict_slashes=False)
@login_required
def dashboard():
    total = PhotoSession.query.count()
    active = PhotoSession.query.filter_by(status='connected').count()
    completed = PhotoSession.query.filter_by(status='completed').count()
    waiting = PhotoSession.query.filter_by(status='waiting').count()
    today = PhotoSession.query.filter(
        db.func.date(PhotoSession.created_at) == date.today()
    ).count()
    recent = PhotoSession.query.order_by(PhotoSession.id.desc()).limit(10).all()

    uptime_secs = int(time.time() - _SERVER_START_TIME)
    uptime_h = uptime_secs // 3600
    uptime_m = (uptime_secs % 3600) // 60
    uptime_str = f"{uptime_h}j {uptime_m}m"

    return render_template('admin/dashboard.html',
                           total=total, active=active, completed=completed,
                           waiting=waiting, today=today, recent=recent,
                           uptime=uptime_str,
                           today_date=datetime.now().strftime('%A, %d %B %Y'))


@admin_bp.route('/gallery', strict_slashes=False)
@login_required
def gallery():
    collage_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'collages')
    collages = []
    if os.path.exists(collage_dir):
        for fname in sorted(os.listdir(collage_dir), reverse=True):
            fpath = os.path.join(collage_dir, fname)
            stat = os.stat(fpath)
            # Cari session terkait berdasarkan collage_path
            session = PhotoSession.query.filter(
                PhotoSession.collage_path.like(f'%{fname}%')
            ).first()
            raw_count = 0
            template_name = 'default'
            if session:
                template_name = session.template_name or 'default'
                try:
                    raws = json.loads(session.raw_photos_json or '[]')
                    raw_count = len(raws)
                except Exception:
                    raw_count = 0
            collages.append({
                'filename': fname,
                'size': round(stat.st_size / 1024, 1),
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%d %b %Y %H:%M'),
                'template': template_name,
                'raw_count': raw_count,
                'session_code': session.unique_code if session else '-',
            })
    return render_template('admin/gallery.html', collages=collages)


@admin_bp.route('/gif-gallery', strict_slashes=False)
@login_required
def gif_gallery():
    gif_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'gifs')
    gifs = []
    if os.path.exists(gif_dir):
        for fname in sorted(os.listdir(gif_dir), reverse=True):
            if not fname.lower().endswith('.gif'):
                continue
            fpath = os.path.join(gif_dir, fname)
            stat = os.stat(fpath)
            # Extract session code from filename pattern gif_<code>_<hash>.gif
            parts = fname.replace('.gif', '').split('_')
            session_code = parts[1] if len(parts) >= 2 else '-'
            gif_url = url_for('static', filename=f'uploads/gifs/{fname}', _external=True)
            gifs.append({
                'filename': fname,
                'url': gif_url,
                'size': round(stat.st_size / 1024, 1),
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%d %b %Y %H:%M'),
                'session_code': session_code,
            })
    return render_template('admin/gif_gallery.html', gifs=gifs)


@admin_bp.route('/templates', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def templates():
    template_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'templates')
    os.makedirs(template_dir, exist_ok=True)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'upload':
            file = request.files.get('template_file')
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(template_dir, filename))
                flash(f'Template "{filename}" berhasil diunggah!', 'success')
            else:
                flash('File tidak valid. Gunakan format PNG, JPG, atau WEBP.', 'error')

        elif action == 'set_active':
            selected = request.form.get('active_template', 'default')
            set_setting('active_custom_template', selected)
            flash('Template aktif berhasil diperbarui!', 'success')

        elif action == 'delete':
            fname = request.form.get('filename', '')
            fpath = os.path.join(template_dir, secure_filename(fname))
            if os.path.exists(fpath):
                os.remove(fpath)
                # Reset active template jika yang dihapus adalah template aktif
                if get_setting('active_custom_template') == fname:
                    set_setting('active_custom_template', 'default')
                flash(f'Template "{fname}" dihapus.', 'success')
            else:
                flash('File tidak ditemukan.', 'error')

        return redirect(url_for('admin.templates'))

    uploaded_templates = []
    if os.path.exists(template_dir):
        for fname in sorted(os.listdir(template_dir)):
            fpath = os.path.join(template_dir, fname)
            stat = os.stat(fpath)
            uploaded_templates.append({
                'filename': fname,
                'size': round(stat.st_size / 1024, 1),
            })

    active_template = get_setting('active_custom_template', 'default')
    return render_template('admin/templates.html',
                           templates=uploaded_templates,
                           active_template=active_template)


@admin_bp.route('/editor', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def editor_panel():
    template_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'templates')
    os.makedirs(template_dir, exist_ok=True)
    uploaded_templates = sorted(os.listdir(template_dir)) if os.path.exists(template_dir) else []

    if request.method == 'POST':
        watermark = request.form.get('watermark_text', 'HAISEN OFFICIAL')
        selected_template = request.form.get('editing_template', 'default')
        slots_json = request.form.get('slots_json', '[]')

        set_setting('watermark_text', watermark)
        set_setting('active_custom_template', selected_template)
        set_setting(f'layout_coords_{selected_template}', slots_json)

        flash('Layout slot foto berhasil disimpan!', 'success')
        return redirect(url_for('admin.editor_panel') + f'?tpl={selected_template}')

    selected_tpl = request.args.get('tpl', get_setting('active_custom_template', 'default'))
    coords_key = f'layout_coords_{selected_tpl}'

    context = {
        'watermark_text': get_setting('watermark_text', 'HAISEN OFFICIAL'),
        'editing_template': selected_tpl,
        'saved_coords': get_setting(coords_key, '[]'),
        'templates': uploaded_templates,
        'camera_index': get_setting('camera_index', '0'),
    }
    return render_template('admin/editor.html', **context)


@admin_bp.route('/settings', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def settings():
    if request.method == 'POST':
        cam_index = request.form.get('camera_index', '0')
        gdrive_folder = request.form.get('gdrive_folder_id', '')
        watermark = request.form.get('watermark_text', 'HAISEN OFFICIAL')
        enable_gif = '1' if request.form.get('enable_gif') else '0'
        output_mode = request.form.get('output_mode', 'both')  # photo, template, both

        for k, v in [
            ('camera_index', cam_index),
            ('gdrive_folder_id', gdrive_folder),
            ('watermark_text', watermark),
            ('enable_gif', enable_gif),
            ('output_mode', output_mode),
        ]:
            set_setting(k, v)

        flash('Konfigurasi sistem berhasil disimpan!', 'success')
        return redirect(url_for('admin.settings'))

    return render_template('admin/settings.html',
                           camera_index=get_setting('camera_index', '0'),
                           gdrive_folder_id=get_setting('gdrive_folder_id', ''),
                           watermark_text=get_setting('watermark_text', 'HAISEN OFFICIAL'),
                           enable_gif=get_setting('enable_gif', '0'),
                           output_mode=get_setting('output_mode', 'both'))


# ─────────────────────────────────────────────
# API JSON ENDPOINTS (untuk polling / AJAX)
# ─────────────────────────────────────────────

@admin_bp.route('/api/stats')
@login_required
def api_stats():
    total = PhotoSession.query.count()
    active = PhotoSession.query.filter_by(status='connected').count()
    completed = PhotoSession.query.filter_by(status='completed').count()
    waiting = PhotoSession.query.filter_by(status='waiting').count()
    today = PhotoSession.query.filter(
        db.func.date(PhotoSession.created_at) == date.today()
    ).count()
    uptime_secs = int(time.time() - _SERVER_START_TIME)
    return jsonify({
        'total': total, 'active': active, 'completed': completed,
        'waiting': waiting, 'today': today,
        'uptime_secs': uptime_secs,
        'server_time': datetime.now().strftime('%H:%M:%S'),
    })


@admin_bp.route('/api/recent-sessions')
@login_required
def api_recent_sessions():
    sessions = PhotoSession.query.order_by(PhotoSession.id.desc()).limit(10).all()
    data = []
    for s in sessions:
        data.append({
            'id': s.id,
            'code': s.unique_code,
            'status': s.status,
            'template': s.template_name or 'default',
            'created_at': s.created_at.strftime('%H:%M:%S - %d %b %Y') if s.created_at else '-',
        })
    return jsonify(data)


@admin_bp.route('/api/chart-data')
@login_required
def api_chart_data():
    """Data chart: jumlah sesi per jam hari ini (24 jam terakhir)."""
    from sqlalchemy import func, extract
    results = (
        db.session.query(extract('hour', PhotoSession.created_at).label('hour'), func.count())
        .filter(db.func.date(PhotoSession.created_at) == date.today())
        .group_by('hour')
        .all()
    )
    hours = {int(r[0]): r[1] for r in results}
    labels = [f'{h:02d}:00' for h in range(24)]
    values = [hours.get(h, 0) for h in range(24)]
    return jsonify({'labels': labels, 'values': values})


@admin_bp.route('/api/gallery/<filename>')
@login_required
def api_gallery_detail(filename):
    """Detail satu collage untuk modal."""
    collage_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'collages')
    if not is_safe_file_in_dir(collage_dir, filename):
        return jsonify({'error': 'File tidak valid atau tidak ditemukan'}), 404

    fpath = os.path.join(collage_dir, secure_filename(filename))
    stat = os.stat(fpath)
    session = PhotoSession.query.filter(
        PhotoSession.collage_path.like(f'%{filename}%')
    ).first()

    raw_photos = []
    template_name = 'default'
    session_code = '-'
    created_at = datetime.fromtimestamp(stat.st_mtime).strftime('%d %b %Y %H:%M')

    if session:
        template_name = session.template_name or 'default'
        session_code = session.unique_code
        if session.created_at:
            created_at = session.created_at.strftime('%d %b %Y %H:%M')
        try:
            raw_photos = json.loads(session.raw_photos_json or '[]')
        except Exception:
            raw_photos = []

    download_url = url_for('static', filename=f'uploads/collages/{filename}', _external=True)

    return jsonify({
        'filename': filename,
        'template': template_name,
        'session_code': session_code,
        'raw_count': len(raw_photos),
        'raw_photos': raw_photos,
        'size_kb': round(stat.st_size / 1024, 1),
        'date': created_at,
        'download_url': download_url,
    })


@admin_bp.route('/api/cameras')
@login_required
def api_cameras():
    """Deteksi kamera yang tersedia via OpenCV."""
    try:
        import cv2
        available = []
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                available.append({'index': i, 'label': f'Kamera {i}', 'resolution': f'{w}x{h}'})
                cap.release()
        return jsonify({'cameras': available})
    except Exception as e:
        return jsonify({'cameras': [], 'error': str(e)})


@admin_bp.route('/api/test-camera', methods=['POST'])
@login_required
def api_test_camera():
    """Test apakah kamera dengan index tertentu bisa dibuka."""
    try:
        import cv2
        idx = int(request.json.get('index', 0))
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            return jsonify({'success': True, 'resolution': f'{w}x{h}', 'message': f'Kamera {idx} aktif — {w}x{h}'})
        cap.release()
        return jsonify({'success': False, 'message': f'Kamera {idx} tidak dapat dibuka.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@admin_bp.route('/api/reset-data', methods=['POST'])
@login_required
def api_reset_data():
    """Hapus semua data session dari DB dan semua file upload (collages + temp)."""
    try:
        PhotoSession.query.delete()
        db.session.commit()

        for folder in ['collages', 'temp']:
            fdir = os.path.join(current_app.root_path, 'static', 'uploads', folder)
            if os.path.exists(fdir):
                shutil.rmtree(fdir)
                os.makedirs(fdir, exist_ok=True)

        return jsonify({'success': True, 'message': 'Semua data dan file berhasil dihapus.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@admin_bp.route('/api/templates/<filename>', methods=['DELETE'])
@login_required
def api_delete_template(filename):
    template_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'templates')
    if not is_safe_file_in_dir(template_dir, filename):
        return jsonify({'success': False, 'message': 'File tidak valid atau tidak ditemukan'}), 404

    fpath = os.path.join(template_dir, secure_filename(filename))
    os.remove(fpath)
    if get_setting('active_custom_template') == filename:
        set_setting('active_custom_template', 'default')
    return jsonify({'success': True})


@admin_bp.route('/api/generate-gif/<code>', methods=['POST'])
@login_required
def api_generate_gif(code):
    """Generate atau regenerate animasi GIF dari foto jepretan mentah sesi berdasarkan kode sesi."""
    if not is_safe_code(code):
        return jsonify({'success': False, 'message': 'Kode sesi tidak valid.'}), 400

    from app.services.gif_service import GifService
    import json as _json

    session = PhotoSession.query.filter_by(unique_code=code).first()
    if not session:
        return jsonify({'success': False, 'message': 'Sesi tidak ditemukan.'}), 404

    if not session.raw_photos_json:
        return jsonify({'success': False, 'message': 'Tidak ada foto mentah untuk sesi ini.'}), 400

    try:
        raw_filenames = _json.loads(session.raw_photos_json)
    except Exception:
        return jsonify({'success': False, 'message': 'Data foto mentah tidak valid.'}), 400

    image_paths = []
    for fname in raw_filenames:
        fp = os.path.join(current_app.root_path, 'static', 'uploads', 'temp', fname)
        if os.path.exists(fp):
            image_paths.append(fp)

    if not image_paths:
        return jsonify({'success': False, 'message': 'File foto mentah tidak ditemukan di server.'}), 404

    gif_svc = GifService()
    gif_path, err = gif_svc.create_gif(image_paths, session_code=code)

    if err or not gif_path:
        return jsonify({'success': False, 'message': err or 'Gagal membuat GIF.'}), 500

    gif_filename = os.path.basename(gif_path)
    session.gif_path = gif_filename
    db.session.commit()

    gif_url = url_for('static', filename=f'uploads/gifs/{gif_filename}', _external=True)
    return jsonify({'success': True, 'gif_url': gif_url, 'gif_filename': gif_filename})


@admin_bp.route('/raw-gallery', strict_slashes=False)
@login_required
def raw_gallery():
    """Halaman admin untuk menampilkan semua foto mentah, dikelompokkan per sesi."""
    sessions = PhotoSession.query.filter(
        PhotoSession.raw_photos_json.isnot(None),
        PhotoSession.raw_photos_json != '[]'
    ).order_by(PhotoSession.id.desc()).all()

    temp_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'temp')
    grouped = []
    for s in sessions:
        try:
            raw_files = json.loads(s.raw_photos_json or '[]')
        except Exception:
            continue
        if not raw_files:
            continue

        photos = []
        for fname in raw_files:
            fpath = os.path.join(temp_dir, fname)
            if os.path.exists(fpath):
                stat = os.stat(fpath)
                photos.append({
                    'filename': fname,
                    'url': url_for('static', filename=f'uploads/temp/{fname}', _external=True),
                    'size': round(stat.st_size / 1024, 1),
                })
        if photos:
            grouped.append({
                'code': s.unique_code,
                'template': s.template_name or 'default',
                'created_at': s.created_at.strftime('%d %b %Y %H:%M') if s.created_at else '-',
                'photos': photos,
                'photo_count': len(photos),
            })

    return render_template('admin/raw_gallery.html', grouped=grouped)


@admin_bp.route('/api/download-raw-zip/<code>', methods=['GET'])
def api_download_raw_zip(code):
    """Download semua atau sebagian foto mentah sesi sebagai ZIP (public agar bisa diakses via QR)."""
    if not is_safe_code(code):
        return jsonify({'error': 'Kode sesi tidak valid'}), 400

    temp_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'temp')
    req_files = request.args.get('files')

    if req_files:
        candidate_files = [f.strip() for f in req_files.split(',') if f.strip()][:MAX_ZIP_ITEMS]
        raw_files = [f for f in candidate_files if is_safe_file_in_dir(temp_dir, f)]
    else:
        session_obj = PhotoSession.query.filter_by(unique_code=code).first()
        if not session_obj or not session_obj.raw_photos_json:
            return jsonify({'error': 'Sesi tidak ditemukan'}), 404
        try:
            stored_files = json.loads(session_obj.raw_photos_json)
        except Exception:
            return jsonify({'error': 'Data tidak valid'}), 400
        raw_files = [f for f in stored_files if is_safe_file_in_dir(temp_dir, f)][:MAX_ZIP_ITEMS]

    if not raw_files:
        return jsonify({'error': 'Tidak ada file foto yang valid ditemukan'}), 404

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in raw_files:
            fpath = os.path.join(temp_dir, secure_filename(fname))
            if os.path.exists(fpath):
                zf.write(fpath, os.path.basename(fname))
    buf.seek(0)
    return send_file(buf, mimetype='application/zip',
                     as_attachment=True, download_name=f'raw_photos_{code}.zip')


@admin_bp.route('/api/download-selected-zip', methods=['GET', 'POST'])
def api_download_selected_zip():
    """Download foto mentah terpilih sebagai ZIP (mendukung GET untuk scan QR smartphone)."""
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        candidate_files = data.get('files', [])
        code = data.get('code', 'selected')
    else:
        req_files = request.args.get('files', '')
        candidate_files = [f.strip() for f in req_files.split(',') if f.strip()]
        code = request.args.get('code', 'selected')

    if not is_safe_code(code):
        code = 'selected'

    temp_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'temp')
    valid_files = [f for f in candidate_files if is_safe_file_in_dir(temp_dir, f)][:MAX_ZIP_ITEMS]

    if not valid_files:
        return jsonify({'error': 'Tidak ada file valid yang dipilih'}), 400

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in valid_files:
            fpath = os.path.join(temp_dir, secure_filename(fname))
            if os.path.exists(fpath):
                zf.write(fpath, os.path.basename(fname))
    buf.seek(0)
    return send_file(buf, mimetype='application/zip',
                     as_attachment=True, download_name=f'raw_photos_{code}.zip')


@admin_bp.route('/api/reset-session-pin', methods=['POST'])
@login_required
def api_reset_session_pin():
    """Mereset kode PIN sesi booth secara instan dari Admin dan memancarkannya via WebSocket ke monitor."""
    import random

    # 1. Tandai semua sesi 'waiting' aktif lama sebagai 'expired'
    waiting_sessions = PhotoSession.query.filter_by(status='waiting').all()
    for s in waiting_sessions:
        s.status = 'expired'
    db.session.commit()

    # 2. Buat PIN unik 4 digit baru
    while True:
        new_code = f"{random.randint(1000, 9999)}"
        existing = PhotoSession.query.filter_by(unique_code=new_code).first()
        if not existing:
            break

    new_session = PhotoSession(unique_code=new_code, status='waiting', created_at=datetime.now())
    db.session.add(new_session)
    db.session.commit()

    # 3. Reset preview filter kamera ke 'classic' (Natural)
    try:
        CameraService().set_preview_filter('classic')
    except Exception:
        pass

    # 4. Broadcast event ke layar monitor Host secara realtime
    mobile_url = f"http://{request.host}/mobile?code={new_code}"
    try:
        socketio.emit('session_pin_reset', {
            'code': new_code,
            'mobile_url': mobile_url,
            'timeout_seconds': 180
        })
        socketio.emit('session_updated', {'code': new_code, 'status': 'waiting'})
        socketio.emit('filter_updated', {'filter': 'classic', 'code': new_code})
    except Exception as e:
        print(f"Error emitting socket on pin reset: {e}")

    return jsonify({
        'success': True,
        'message': f'Kode PIN sesi berhasil direset menjadi #{new_code}',
        'code': new_code,
        'mobile_url': mobile_url
    })



