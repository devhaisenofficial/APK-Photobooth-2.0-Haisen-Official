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
        self.preview_filter = 'classic'

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

        # CACHE FALLBACK IMAGE DI LUAR LOOP (Mencegah Memory Leak & Alokasi Berulang)
        fallback = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.putText(fallback, "Menghubungkan Kamera...", (370, 340),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
        _, cached_fallback_encoded = cv2.imencode('.jpg', fallback, [cv2.IMWRITE_JPEG_QUALITY, 75])
        cached_fallback_bytes = cached_fallback_encoded.tobytes() if cached_fallback_encoded is not None else b""

        while self.is_running:
            # 1. Jika kamera fisik terhubung dan terbuka, ambil frame secara kontinu
            if cap is not None and cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    fail_count = 0
                    # Mirror horizontal untuk standar selfie photobooth
                    frame_mirrored = cv2.flip(frame, 1)
                    
                    # Terapkan filter preview yang dipilih pengunjung di remote secara realtime
                    curr_filter = self.preview_filter
                    if curr_filter and curr_filter != 'classic':
                        try:
                            stream_frame = self._apply_filter(frame_mirrored, curr_filter)
                        except Exception:
                            stream_frame = frame_mirrored
                    else:
                        stream_frame = frame_mirrored

                    # Encode jpeg ringan untuk streaming real-time
                    ret_enc, buffer = cv2.imencode('.jpg', stream_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    
                    with self.thread_lock:
                        # Raw frame tetap bersih untuk resolusi penuh/akurat
                        self.latest_raw_frame = frame_mirrored
                        if ret_enc:
                            self.latest_encoded_frame = buffer.tobytes()
                    
                    time.sleep(0.02) # ~45 FPS
                    continue
                else:
                    fail_count += 1
                    if fail_count > 8:
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

            # 3. Gunakan Fallback Cached (Aman dari alokasi memori NumPy berlebih)
            with self.thread_lock:
                self.latest_raw_frame = fallback
                self.latest_encoded_frame = cached_fallback_bytes
            
            time.sleep(0.1)

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

    def set_preview_filter(self, filter_name='classic'):
        """Mengatur filter yang sedang aktif pada live preview stream"""
        self.preview_filter = filter_name if filter_name else 'classic'

    def capture_frame(self, filter_type='classic'):
        """
        Mengambil satu frame kualitas tinggi langsung dari buffer thread aktif.
        Tidak pernah membuka/menutup kamera ulang, sehingga jepretan ke-2, ke-3, dst
        berjalan instan tanpa stuck atau freeze.
        """
        self._ensure_camera_running()
        temp_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')), 'storage', 'temp')
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

        elif filter_type == 'dreamy':
            # Efek Ethereal Dreamy / K-Drama Soft Glow yang Magis
            
            # 1. Haluskan kulit/wajah dengan Bilateral Filter (Menjaga garis tepi tetap tajam)
            smooth = cv2.bilateralFilter(frame, d=9, sigmaColor=75, sigmaSpace=75)
            
            # 2. Buat Bloom Effect (Cahaya lembut berpendar dari area terang)
            gray = cv2.cvtColor(smooth, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)
            
            # Blur sangat besar untuk menghasilkan pendaran cahaya impian
            glow = cv2.GaussianBlur(smooth, (51, 51), 0)
            
            # 3. Campurkan gambar halus dengan pendaran cahaya (Bloom)
            dream_base = cv2.addWeighted(smooth, 0.75, glow, 0.35, 10)
            
            # 4. Sentuhan Warna Pastel & Magis (Warm/Pinkish Haze)
            hsv = cv2.cvtColor(dream_base, cv2.COLOR_BGR2HSV).astype(np.float32)
            
            # Geser sedikit Hue ke arah nuansa magenta/pink lembut
            hsv[:, :, 0] = (hsv[:, :, 0] - 4) % 180 
            
            # Turunkan sedikit saturasi agar mendapatkan kesan "Pastel" yang lembut
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 0.92, 0, 255) 
            
            # Naikkan sedikit kecerahan (brightness) agar terasa seperti bermandikan cahaya surga
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.08 + 15, 0, 255) 
            
            return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        elif filter_type == 'glitch':
            h, w = frame.shape[:2]
            # 1. Perbesar jarak Chromatic Aberration
            shift = max(15, int(w * 0.03)) 
            res = frame.copy()
            
            # Geser channel Biru (0) ke kiri, Merah (2) ke kanan
            res[:, :-shift, 0] = frame[:, shift:, 0]  # Bayangan Biru
            res[:, shift:, 2] = frame[:, :-shift, 2]  # Bayangan Merah
            
            # 2. Horizontal Tearing (Garis patah-patah acak)
            num_tears = np.random.randint(4, 10)
            for _ in range(num_tears):
                y = np.random.randint(0, h - 5)
                height = np.random.randint(3, 20) # Ketebalan garis patah
                x_shift = np.random.randint(-shift*2, shift*2) # Jarak geser
                
                y_end = min(y + height, h)
                if x_shift > 0:
                    res[y:y_end, x_shift:] = res[y:y_end, :-x_shift]
                elif x_shift < 0:
                    res[y:y_end, :x_shift] = res[y:y_end, -x_shift:]
                    
            # 3. Aksen Blok Biru dan Merah (Color Boost)
            for _ in range(2): # 2 blok aksen merah
                y_r = np.random.randint(0, h - 20)
                h_r = np.random.randint(5, 15)
                y_rend = min(y_r + h_r, h)
                res[y_r:y_rend, :, 2] = cv2.add(res[y_r:y_rend, :, 2], 70) 
                
            for _ in range(2): # 2 blok aksen biru
                y_b = np.random.randint(0, h - 20)
                h_b = np.random.randint(5, 15)
                y_bend = min(y_b + h_b, h)
                res[y_b:y_bend, :, 0] = cv2.add(res[y_b:y_bend, :, 0], 70) 
                
            return res

        elif filter_type == 'warm':
            # Efek Golden Hour (Sunset/Warm Cinematic)
            b, g, r = cv2.split(frame)
            
            # Membuat kurva warna (Non-linear Gamma Correction)
            # Nilai power < 1 akan mencerahkan channel, > 1 akan menggelapkan
            x = np.arange(256, dtype=np.float32) / 255.0
            lut_r = np.clip(np.power(x, 0.8) * 255.0, 0, 255).astype(np.uint8) # Boost Merah
            lut_g = np.clip(np.power(x, 0.9) * 255.0, 0, 255).astype(np.uint8) # Boost Hijau (Membentuk Kuning/Emas)
            lut_b = np.clip(np.power(x, 1.2) * 255.0, 0, 255).astype(np.uint8) # Kurangi Biru
            
            r = cv2.LUT(r, lut_r)
            g = cv2.LUT(g, lut_g)
            b = cv2.LUT(b, lut_b)
            
            warm_img = cv2.merge([b, g, r])
            
            # Boost saturasi dan beri sedikit efek "Glow" cahaya
            hsv = cv2.cvtColor(warm_img, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.15, 0, 255) # Saturasi naik 15%
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.05, 0, 255) # Kecerahan naik 5%
            return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        elif filter_type == 'cool':
            # Efek Cinematic Moody Blue / Teal (Nuansa film misteri/malam hari)
            b, g, r = cv2.split(frame)
            
            # Membuat kurva warna dingin
            x = np.arange(256, dtype=np.float32) / 255.0
            lut_b = np.clip(np.power(x, 0.7) * 255.0, 0, 255).astype(np.uint8) # Boost Kuat pada Biru
            lut_g = np.clip(np.power(x, 0.85) * 255.0, 0, 255).astype(np.uint8) # Boost Hijau (Membentuk Cyan/Teal)
            lut_r = np.clip(np.power(x, 1.3) * 255.0, 0, 255).astype(np.uint8) # Kurangi Merah
            
            r = cv2.LUT(r, lut_r)
            g = cv2.LUT(g, lut_g)
            b = cv2.LUT(b, lut_b)
            
            cool_img = cv2.merge([b, g, r])
            
            # Turunkan saturasi agar kesan dingin dan dramatis lebih terasa (Desaturated Look)
            hsv = cv2.cvtColor(cool_img, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 0.8, 0, 255) # Saturasi turun 20%
            return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        elif filter_type == 'cartoon':
            # 1. Tingkatkan Kecerahan dan Saturasi (Warna lebih pop & lucu)
            # Ubah ke HSV untuk memanipulasi warna dan cahaya
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.int16)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.4, 0, 255) # Saturasi naik 40% (lebih cerah)
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] + 20, 0, 255)  # Kecerahan naik
            boosted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

            # 2. Kurangi Detail (Image Pyramid + Bilateral Filter)
            # Mengecilkan gambar dulu membuat filter lebih cepat & efek halusnya lebih maksimal
            small = cv2.pyrDown(boosted)
            for _ in range(2): # Ulangi filter 2x agar wajah/kulit terlihat mulus seperti kartun
                small = cv2.bilateralFilter(small, d=9, sigmaColor=20, sigmaSpace=7)
            color = cv2.pyrUp(small)
            
            # Pastikan resolusinya pas kembali ke frame awal
            color = cv2.resize(color, (frame.shape[1], frame.shape[0]))

            # 3. Posterize (Kurangi gradasi warna agar terlihat seperti blok komik flat)
            # Angka 24 mengatur tingkat 'flat'. (Bisa diubah ke 32 atau 48 jika ingin lebih flat)
            color = (color // 24) * 24

            # 4. Garis Tepi (Outline) yang lebih bersih dan tebal
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 7) # Blur lebih kuat (7) untuk menghilangkan noise/garis kerutan
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                          cv2.THRESH_BINARY, blockSize=9, C=10)
            
            # Menebalkan garis hitam agar terlihat seperti digambar dengan spidol (marker)
            kernel = np.ones((2,2), np.uint8)
            edges = cv2.erode(edges, kernel, iterations=1)
            edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

            # 5. Gabungkan warna kartun dan garis luarnya
            return cv2.bitwise_and(color, edges_bgr)

        elif filter_type == 'sketch':
            # Efek coretan sketsa pensil realistis (Gabungan Shading & Outlines)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 1. Base Shading (Efek arsiran pensil halus)
            inv = cv2.bitwise_not(gray)
            blur = cv2.GaussianBlur(inv, (21, 21), 0)
            base_sketch = cv2.divide(gray, 255 - blur, scale=256)
            
            # 2. Strong Outlines (Garis tepi pensil yang tegas)
            # Median blur digunakan agar tekstur kecil (noise/jerawat) tidak ikut tergaris
            gray_blur = cv2.medianBlur(gray, 5) 
            edges = cv2.adaptiveThreshold(gray_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                          cv2.THRESH_BINARY, blockSize=9, C=5)
            
            # 3. Gabungkan arsiran halus dengan garis tegas
            # Karena latar belakang putih (255) dan garis hitam (0), kita pakai bitwise_and
            combined_sketch = cv2.bitwise_and(base_sketch, edges)
            
            # 4. Naikkan kontras agar goresan pensil terlihat lebih hitam/pekat (seperti pensil 4B)
            # alpha = kontras, beta = kecerahan (dikurangi agar tidak terlalu silau)
            final_sketch = cv2.convertScaleAbs(combined_sketch, alpha=1.1, beta=-15)
            
            return cv2.cvtColor(final_sketch, cv2.COLOR_GRAY2BGR)

        elif filter_type == 'pixel':
            # Efek Pixel Art dengan ukuran kotak piksel yang besar
            h, w = frame.shape[:2]
            
            # 1. Haluskan gambar agar warna menyatu dalam blok besar
            smooth = cv2.bilateralFilter(frame, d=9, sigmaColor=75, sigmaSpace=75)
            
            # 2. Ubah block_size menjadi lebih besar (misal 18 atau 24) agar kotak piksel terlihat besar
            block_size = 18
            small = cv2.resize(smooth, (w // block_size, h // block_size), interpolation=cv2.INTER_AREA)
            
            # 3. Boost Saturasi & Kecerahan ala game retro
            hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV).astype(np.int16)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.5, 0, 255) 
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.2, 0, 255) 
            small_boost = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
            
            # 4. Color Quantization (Batasi warna agar kotak piksel terlihat padat/solid)
            levels = 5 
            factor = 256 / levels
            small_quantized = np.clip(np.round(small_boost / factor) * factor, 0, 255).astype(np.uint8)
            
            # 5. Upscale kembali ke ukuran asli dengan INTER_NEAREST
            return cv2.resize(small_quantized, (w, h), interpolation=cv2.INTER_NEAREST)

        elif filter_type == 'vignette':
            # Efek gelap di keempat sudut foto
            rows, cols = frame.shape[:2]
            X_kernel = cv2.getGaussianKernel(cols, cols / 2)
            Y_kernel = cv2.getGaussianKernel(rows, rows / 2)
            kernel = Y_kernel * X_kernel.T
            mask = kernel / kernel.max()
            vignette = frame.copy()
            for i in range(3):
                vignette[:, :, i] = vignette[:, :, i] * mask
            return np.clip(vignette, 0, 255).astype(np.uint8)

        elif filter_type == 'negative':
            # Efek klise foto jadul
            return cv2.bitwise_not(frame)

        elif filter_type == 'cyberpunk':
            # Efek Cyberpunk Neon Profesional (Nuansa Ungu, Magenta, & Biru Cyan)
            b, g, r = cv2.split(frame)
            
            # 1. Manipulasi Channel Warna (Tingkatkan Biru & Merah, kurangi Hijau)
            # Mengurangi hijau ampuh menghilangkan warna kulit aneh/pucat
            b = cv2.add(b, 50)     # Dominasi warna biru/cyan di bayangan
            g = cv2.subtract(g, 40) # Tekan warna hijau
            r = cv2.add(r, 40)     # Dominasi warna magenta/pink di highlight
            
            cyber_base = cv2.merge([b, g, r])
            
            # 2. Tingkatkan kontras agar suasana malam kota futuristik lebih terasa
            cyber_base = cv2.convertScaleAbs(cyber_base, alpha=1.25, beta=5)
            
            # 3. Neon Bloom / Pendaran Cahaya Halus (Tanpa bercak putih/kuning kasar)
            gray = cv2.cvtColor(cyber_base, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)
            glow_areas = cv2.bitwise_and(cyber_base, cyber_base, mask=mask)
            
            # Blur secukupnya agar pendaran neonnya terasa lembut di mata
            blur_glow = cv2.GaussianBlur(glow_areas, (25, 25), 0)
            
            # 4. Satukan gambar utama dengan pendaran cahaya neon
            return cv2.addWeighted(cyber_base, 0.8, blur_glow, 0.4, 0)
            
        elif filter_type == 'high_contrast':
            # Efek Cinematic HDR Dramatis dengan Kulit Cerah & Glowing
            
            # 1. Unsharp Masking (Pertajam gambar agar pori-pori dan detail pakaian jelas)
            blur = cv2.GaussianBlur(frame, (0, 0), 3)
            sharp = cv2.addWeighted(frame, 1.4, blur, -0.4, 0)

            # 2. LAB Color Space untuk mengontrol kontras dan kecerahan kulit
            lab = cv2.cvtColor(sharp, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Terapkan CLAHE pada channel cahaya (Lightness)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            
            # TAMBAHAN: Mencerahkan channel Lightness secara keseluruhan (Membuat kulit jadi lebih putih bersih/glowing)
            # Menggunakan np.clip agar tidak terlalu silau (overexposed)
            cl = np.clip(cl.astype(np.float32) * 1.12 + 15, 0, 255).astype(np.uint8)
            
            # Gabungkan kembali warna dan cahayanya
            merged_lab = cv2.merge((cl, a, b))
            dramatic = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2BGR)

            # 3. Boost Saturasi & Sedikit Warmth agar kulit tetap terlihat sehat (tidak pucat/pasi)
            hsv = cv2.cvtColor(dramatic, cv2.COLOR_BGR2HSV).astype(np.int16)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.1, 0, 255) # Saturasi dijaga agar tetap natural
            return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

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