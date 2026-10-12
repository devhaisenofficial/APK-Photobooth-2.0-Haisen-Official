# WAJIB DI BARIS PALING ATAS
from gevent import monkey
monkey.patch_all()

import socket
import urllib.request
from app import create_app
from extensions import socketio
from werkzeug.middleware.proxy_fix import ProxyFix  

app = create_app()

from app.services.camera_service import CameraService
CameraService().app = app

# <-- TAMBAHAN 2: Konfigurasi ProxyFix untuk Cloudflare Tunnel -->
# Ini memaksa Flask untuk menggunakan "https://" saat merender gambar/aset
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

def get_local_ip():
    """Mengambil IP Lokal (LAN/WiFi) komputer saat ini."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Tidak benar-benar melakukan koneksi internet, hanya memancing rute IP lokal
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_public_ip():
    """Mengambil IP Public dari provider internet."""
    try:
        # Mengambil IP dari layanan ipify dengan batas waktu 3 detik
        return urllib.request.urlopen('https://api.ipify.org', timeout=3).read().decode('utf8')
    except Exception:
        return "Tidak terdeteksi (Cek koneksi internet)"

if __name__ == '__main__':
    port = 5000
    local_ip = get_local_ip()
    
    # Hanya cetak banner jika ini adalah proses utama (mencegah cetak ganda dari reloader Flask)
    import os
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        public_ip = get_public_ip()
        print("\n" + "="*55)
        print(" 🚀 HAISEN PHOTOBOOTH SERVER BERJALAN ")
        print("="*55)
        print(f" * Localhost (PC ini) : http://localhost:{port}")
        print(f" * Network/LAN (WiFi) : http://{local_ip}:{port}")
        print(f" * Public IP (Internet): http://{public_ip}:{port}")
        print("="*55 + "\n")

    # Jalankan server
    # Tambahkan log_output=True untuk memaksa terminal menampilkan log aktivitas klien
    socketio.run(app, host='0.0.0.0', port=port, debug=True, use_reloader=False, log_output=True)
    