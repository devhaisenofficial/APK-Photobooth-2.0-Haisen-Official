import os
import time
from flask import Blueprint, render_template, jsonify, current_app, url_for

bilboard_bp = Blueprint('bilboard', __name__, template_folder='../../templates')

# Variabel Global untuk menyimpan cache sementara di RAM
IMAGE_CACHE = {
    'data': {},
    'last_updated': 0
}
CACHE_DURATION = 15  # Waktu simpan cache dalam detik (Misal: 15 detik)

@bilboard_bp.route('/')
def index():
    return render_template('bilboard/index.html')

@bilboard_bp.route('/api/images')
def get_images():
    current_time = time.time()
    
    # 1. Cek apakah cache masih valid (belum kedaluwarsa)
    if (current_time - IMAGE_CACHE['last_updated'] < CACHE_DURATION) and IMAGE_CACHE['data']:
        # Kembalikan data dari RAM, jangan baca hardisk lagi
        return jsonify(IMAGE_CACHE['data'])
    
    # 2. Jika cache kedaluwarsa, baru kita baca folder (Hardisk)
    static_folder = current_app.static_folder
    directories = {
        'gifs': 'uploads/gifs',
        'temp': 'uploads/temp',
        'collages': 'uploads/collages'
    }
    
    image_data = {}
    
    for key, rel_path in directories.items():
        folder_path = os.path.join(static_folder, rel_path)
        files_list = []
        
        if os.path.exists(folder_path):
            try:
                # Ambil daftar file
                files = os.listdir(folder_path)
                
                # Opsional: Batasi hanya mengambil 50-100 gambar terbaru agar payload tidak terlalu besar
                # Urutkan berdasarkan waktu modifikasi terbaru jika perlu
                # Untuk performa dasar, kita filter yang bukan file tersembunyi
                for filename in files:
                    if not filename.startswith('.'):
                        files_list.append(url_for('static', filename=f"{rel_path}/{filename}"))
            except Exception as e:
                print(f"Error membaca folder {key}: {e}")
                
        image_data[key] = files_list

    # 3. Perbarui Cache
    IMAGE_CACHE['data'] = image_data
    IMAGE_CACHE['last_updated'] = current_time

    return jsonify(image_data)