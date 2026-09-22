from flask import Blueprint, render_template, request, Response
from extensions import db, socketio
from app.models.session_model import PhotoSession
from app.services.camera_service import CameraService
from datetime import datetime
import random

host_bp = Blueprint('host', __name__, template_folder='../../templates')

# Singleton kamera — dibuat saat pertama kali /video_feed dipanggil
# (bukan saat module di-import) agar Flask app context sudah tersedia.
_camera = None

def get_camera():
    global _camera
    if _camera is None:
        _camera = CameraService()
    return _camera


@host_bp.route('/')
def index():
    # Generate kode unik 4 digit random (1000 - 9999)
    while True:
        code = f"{random.randint(1000, 9999)}"
        existing = PhotoSession.query.filter_by(unique_code=code, status='waiting').first()
        if not existing:
            break

    # Simpan sesi baru ke database dengan waktu lokal hari ini & jam akurat
    new_session = PhotoSession(unique_code=code, status='waiting', created_at=datetime.now())
    db.session.add(new_session)
    db.session.commit()

    # Emit socket event agar admin dashboard langsung ter-update realtime
    try:
        socketio.emit('session_updated', {'code': code, 'status': 'waiting'})
    except Exception:
        pass

    mobile_url = f"http://{request.host}/mobile?code={code}"

    return render_template('host/index.html', code=code, mobile_url=mobile_url)


@host_bp.route('/video_feed')
def video_feed():
    """Endpoint route untuk menyalurkan stream real-time webcam"""
    return Response(
        get_camera().get_frame_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )