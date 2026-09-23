import os
import json
from flask import Blueprint, render_template, request, url_for, current_app, session as flask_session
from app.models.session_model import PhotoSession

gallery_bp = Blueprint('gallery', __name__, template_folder='../../templates')

def _storage(subfolder):
    """Kembalikan path absolut ke subfolder di private storage."""
    storage_base = current_app.config.get(
        'PRIVATE_STORAGE_PATH',
        os.path.join(current_app.root_path, '..', 'storage')
    )
    return os.path.join(storage_base, subfolder)


@gallery_bp.route('/gallery/<code>')
def view_gallery(code):
    session = PhotoSession.query.filter_by(unique_code=code).first()
    
    if not session:
        return render_template('gallery/404.html', code=code), 404

    # Berikan token otorisasi sesi browser bagi pengunjung galeri ini
    flask_session[f'gallery_access_{code}'] = True
    flask_session['allowed_gallery_code'] = code

    # Ambil data kolase
    collage_filename = session.collage_path
    collage_exists = False
    if collage_filename:
        collage_filepath = os.path.join(_storage('collages'), collage_filename)
        collage_exists = os.path.exists(collage_filepath)

    # Ambil data foto-foto mentah
    raw_photos = []
    if session.raw_photos_json:
        try:
            raw_list = json.loads(session.raw_photos_json)
            for p in raw_list:
                temp_filepath = os.path.join(_storage('temp'), p)
                if os.path.exists(temp_filepath):
                    raw_photos.append(p)
        except Exception:
            raw_photos = []

    # Ambil data GIF animasi
    gif_filename = session.gif_path
    gif_exists = False
    if gif_filename:
        gif_filepath = os.path.join(_storage('gifs'), gif_filename)
        gif_exists = os.path.exists(gif_filepath)

    # Tautan unduh aman (melalui serve_file dengan code otorisasi)
    download_url = url_for('api.serve_file', file_type='collages', filename=collage_filename, code=code, _external=True) if collage_filename else ''
    gallery_share_url = request.base_url

    is_host = (request.args.get('from') == 'host')

    return render_template('gallery/index.html',
                           session=session,
                           code=code,
                           is_host=is_host,
                           collage_filename=collage_filename,
                           collage_exists=collage_exists,
                           gif_filename=gif_filename,
                           gif_exists=gif_exists,
                           raw_photos=raw_photos,
                           download_url=download_url,
                           share_url=gallery_share_url)