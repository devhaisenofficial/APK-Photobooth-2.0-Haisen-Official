from flask import Blueprint, render_template, request, Response, jsonify
from extensions import db, socketio
from app.models.session_model import PhotoSession
from app.services.camera_service import CameraService
from datetime import datetime
import random

host_bp = Blueprint('host', __name__, template_folder='../../templates')

_camera = None

def get_camera():
    global _camera
    if _camera is None:
        _camera = CameraService()
    return _camera


SESSION_TIMEOUT_SECONDS = 180  # 3 Menit


def get_or_create_waiting_session():
    """
    Mengambil sesi waiting yang masih aktif (belum expired & berumur <= 3 menit)
    atau membuat sesi baru jika tidak ada / sudah expired.
    Mencegah kode PIN berganti setiap kali halaman di-refresh sebelum digunakan.
    """
    waiting = PhotoSession.query.filter_by(status='waiting').order_by(PhotoSession.created_at.desc()).first()

    if waiting:
        elapsed = (datetime.now() - waiting.created_at).total_seconds() if waiting.created_at else 9999
        if elapsed < SESSION_TIMEOUT_SECONDS:
            # Sesi masih valid dalam rentang 3 menit dan belum dipakai -> gunakan kembali PIN ini
            return waiting, False
        else:
            # Sesi sudah lebih dari 3 menit tanpa dipakai -> tandai expired
            waiting.status = 'expired'
            db.session.commit()

    # Generate PIN 4 digit baru yang unik
    while True:
        code = f"{random.randint(1000, 9999)}"
        existing = PhotoSession.query.filter_by(unique_code=code).first()
        if not existing:
            break

    new_session = PhotoSession(unique_code=code, status='waiting', created_at=datetime.now())
    db.session.add(new_session)
    db.session.commit()
    return new_session, True


@host_bp.route('/')
def index():
    # Pastikan filter preview kamera selalu kembali ke 'classic' (Natural) saat di standby
    try:
        get_camera().set_preview_filter('classic')
    except Exception:
        pass

    session, is_new = get_or_create_waiting_session()
    code = session.unique_code

    if is_new:
        try:
            socketio.emit('session_updated', {'code': code, 'status': 'waiting'})
        except Exception:
            pass

    mobile_url = f"http://{request.host}/mobile?code={code}"

    # Sisa detik sebelum sesi 3 menit kedaluwarsa
    elapsed = int((datetime.now() - session.created_at).total_seconds()) if session.created_at else 0
    timeout_seconds = max(1, SESSION_TIMEOUT_SECONDS - elapsed)

    return render_template('host/index.html', code=code, mobile_url=mobile_url, timeout_seconds=timeout_seconds)


@host_bp.route('/api/request-new-pin', methods=['POST'])
def api_request_new_pin():
    """Dipanggil otomatis oleh monitor booth ketika timer 3 menit habis tanpa ada koneksi."""
    # Tandai sesi lama sebagai expired
    old_sessions = PhotoSession.query.filter_by(status='waiting').all()
    for s in old_sessions:
        s.status = 'expired'
    db.session.commit()

    session, is_new = get_or_create_waiting_session()
    code = session.unique_code
    mobile_url = f"http://{request.host}/mobile?code={code}"

    try:
        socketio.emit('session_updated', {'code': code, 'status': 'waiting'})
        get_camera().set_preview_filter('classic')
    except Exception:
        pass

    return jsonify({
        'code': code,
        'mobile_url': mobile_url,
        'timeout_seconds': SESSION_TIMEOUT_SECONDS
    })


@host_bp.route('/video_feed')
def video_feed():
    """Endpoint route untuk menyalurkan stream real-time webcam"""
    return Response(
        get_camera().get_frame_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )