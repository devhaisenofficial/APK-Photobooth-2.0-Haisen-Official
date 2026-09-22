import cv2
import os
import time
import threading
import numpy as np
from datetime import datetime
from app.models.admin_model import AppSetting

class CameraService:
    """
    Singleton Camera Service:
    Mengelola 1 instansi cv2.VideoCapture aktif di background thread
    sehingga streaming MJPEG dan pengambilan foto (capture_frame)
    berjalan simultan tanpa konflik resource hardware, tanpa freeze,
    dan tidak stuck pada jepretan ke-2 maupun seterusnya.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        self._initialized = True
        self.cap = None
        self.current_camera_index = -1
        self.latest_raw_frame = None
        self.latest_encoded_frame = None
        self.is_running = False
        self.thread = None
        self.thread_lock = threading.Lock()
        self.last_access_time = time.time()

        # Inisialisasi background loop
        self._ensure_camera_running()

    def _get_configured_camera_index(self):
        try:
            setting = AppSetting.query.filter_by(key='camera_index').first()
            return int(setting.value) if setting and setting.value and setting.value.isdigit() else 0
        except Exception:
            return 0

    def _open_camera(self, idx):
        """Membuka hardware kamera dengan backend Windows (CAP_DSHOW atau default) secara optimal"""
        for backend in [cv2.CAP_DSHOW, None]:
            try:
                cap = cv2.VideoCapture(idx, backend) if backend is not None else cv2.VideoCapture(idx)
                if cap and cap.isOpened():
                    try:
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                    except Exception:
                        pass
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

                    # Tes baca beberapa frame awal
                    for _ in range(5):
                        ret, test_frame = cap.read()
                        if ret and test_frame is not None:
                            return cap
                        time.sleep(0.04)

                    # Fallback ke resolusi standar jika 720p gagal
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    for _ in range(5):
                        ret, test_frame = cap.read()
                        if ret and test_frame is not None:
                            return cap
                        time.sleep(0.04)

                    cap.release()
            except Exception as e:
                print(f"[CameraService] Gagal inisialisasi backend {backend}: {e}")
        return None

    def _ensure_camera_running(self):
        desired_idx = self._get_configured_camera_index()
        
        # Jika kamera sudah berjalan di thread aktif, perbarui timestamp akses
        if self.is_running and self.current_camera_index == desired_idx and self.thread and self.thread.is_alive():
            self.last_access_time = time.time()
            return

        # Buka kamera baru jika belum ada atau index berubah
        self.stop()
        self.current_camera_index = desired_idx
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.thread.start()

    def _capture_worker(self):
        """Background thread yang terus membaca frame dari kamera dengan auto-reconnect cerdas"""
        idx = self.current_camera_index
        cap = self._open_camera(idx)
        self.cap = cap
        last_reconnect_time = time.time()
        fail_count = 0

        while self.is_running:
            # 1. Jika kamera fisik terhubung dan terbuka, ambil frame secara kontinu
            if cap is not None and cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    fail_count = 0
                    # Mirror horizontal untuk standar selfie photobooth
                    frame_mirrored = cv2.flip(frame, 1)
                    
                    # Encode jpeg ringan untuk streaming real-time
                    ret_enc, buffer = cv2.imencode('.jpg', frame_mirrored, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    
                    with self.thread_lock:
                        self.latest_raw_frame = frame_mirrored.copy()
                        if ret_enc:
                            self.latest_encoded_frame = buffer.tobytes()
                    time.sleep(0.02) # ~45 FPS
                    continue
                else:
                    fail_count += 1
                    if fail_count > 8:
                        # Kamera terputus atau frame drop terus menerus
                        try:
                            cap.release()
                        except Exception:
                            pass
                        cap = None
                        self.cap = None

            # 2. Auto-reconnect: Coba hubungkan kembali ke kamera fisik setiap 1.5 detik
            now = time.time()
            if (cap is None or not cap.isOpened()) and (now - last_reconnect_time > 1.5):
                last_reconnect_time = now
                idx = self._get_configured_camera_index()
                self.current_camera_index = idx
                cap = self._open_camera(idx)
                self.cap = cap
                if cap is not None and cap.isOpened():
                    fail_count = 0
                    continue

            # 3. Fallback visual saat kamera sedang inisialisasi / menghubungkan
            fallback = np.zeros((720, 1280, 3), dtype=np.uint8)
            cv2.putText(fallback, f"Menghubungkan Kamera [{idx}]...", (370, 340),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(fallback, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (470, 390),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (129, 140, 248), 2, cv2.LINE_AA)
            
            ret_enc, buffer = cv2.imencode('.jpg', fallback, [cv2.IMWRITE_JPEG_QUALITY, 75])
            with self.thread_lock:
                self.latest_raw_frame = fallback.copy()
                if ret_enc:
                    self.latest_encoded_frame = buffer.tobytes()
            
            time.sleep(0.08)

        if cap is not None and cap.isOpened():
            cap.release()

    def get_frame_stream(self):
        """Generator streaming MJPEG realtime langsung dari buffer memori aktif (tanpa lag/stuck)"""
        self._ensure_camera_running()

        # Tunggu hingga frame pertama tersedia (max 8 detik)
        deadline = time.time() + 8.0
        while self.latest_encoded_frame is None and time.time() < deadline:
            time.sleep(0.05)

        while True:
            with self.thread_lock:
                frame_bytes = self.latest_encoded_frame

            if frame_bytes is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # Kamera belum siap, kirim blank frame hitam agar koneksi tidak putus
                import numpy as np
                blank = np.zeros((480, 640, 3), dtype=np.uint8)
                _, buf = cv2.imencode('.jpg', blank)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')

            time.sleep(0.033)  # 30 FPS stream

    def capture_frame(self, filter_type='classic'):
        """
        Mengambil satu frame kualitas tinggi langsung dari buffer thread aktif.
        Tidak pernah membuka/menutup kamera ulang, sehingga jepretan ke-2, ke-3, dst
        berjalan instan tanpa stuck atau freeze.
        """
        self._ensure_camera_running()
        temp_dir = os.path.join('app', 'static', 'uploads', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
        filepath = os.path.join(temp_dir, filename)

        with self.thread_lock:
            if self.latest_raw_frame is not None:
                frame = self.latest_raw_frame.copy()
            else:
                frame = np.ones((1080, 1920, 3), dtype=np.uint8) * 40
                cv2.putText(frame, "HAISEN PHOTOBOOTH", (600, 540),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)

        # Terapkan filter kamera yang dipilih pengunjung di remote
        processed = self._apply_filter(frame, filter_type)
        cv2.imwrite(filepath, processed, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return filepath, None

    def _apply_filter(self, frame, filter_type):
        if filter_type == 'bw':
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif filter_type == 'vintage':
            kernel = np.array([[0.272, 0.534, 0.131],
                               [0.349, 0.686, 0.168],
                               [0.393, 0.769, 0.189]])
            sepia = cv2.transform(frame, kernel)
            return np.clip(sepia, 0, 255).astype(np.uint8)
        else:
            return frame

    def stop(self):
        """Menghentikan thread dan merilis kamera jika ada reload konfigurasi"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None