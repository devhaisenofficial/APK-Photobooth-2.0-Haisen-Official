import os
import time
from flask import Blueprint, render_template, jsonify, current_app, url_for, session as flask_session

bilboard_bp = Blueprint('bilboard', __name__, template_folder='../../templates')

# Variabel Global untuk menyimpan cache sementara di RAM
IMAGE_CACHE = {
    'data': {},
    'last_updated': 0
}
CACHE_DURATION = 15  # Waktu simpan cache dalam detik (Misal: 15 detik)

@bilboard_bp.route('/')
def index():
    flask_session['bilboard_access'] = True
    return render_template('bilboard/index.html')

@bilboard_bp.route('/api/images')
def get_images():
    current_time = time.time()
    
    # 1. Cek apakah cache masih valid (belum kedaluwarsa)
    if (current_time - IMAGE_CACHE['last_updated'] < CACHE_DURATION) and IMAGE_CACHE['data']:
        # Kembalikan data dari RAM, jangan baca hardisk lagi
        return jsonify(IMAGE_CACHE['data'])
    
    # 2. Jika cache kedaluwarsa, baru kita baca folder (private storage)
    storage_base = current_app.config.get(
        'PRIVATE_STORAGE_PATH',
        os.path.join(current_app.root_path, '..', 'storage')
    )
    directories = {
        'gifs': 'gifs',
        'temp': 'temp',
        'collages': 'collages'
    }
    
    image_data = {}
    
    for key, subfolder in directories.items():
        folder_path = os.path.join(storage_base, subfolder)
        files_list = []
        
        if os.path.exists(folder_path):
            try:
                files = os.listdir(folder_path)
                for filename in files:
                    if not filename.startswith('.'):
                        # Serve melalui endpoint aman (admin sudah login di bilboard)
                        files_list.append(url_for('api.serve_file', file_type=key, filename=filename))
            except Exception as e:
                print(f"Error membaca folder {key}: {e}")
                
        image_data[key] = files_list

    # 3. Perbarui Cache
    IMAGE_CACHE['data'] = image_data
    IMAGE_CACHE['last_updated'] = current_time

    return jsonify(image_data)