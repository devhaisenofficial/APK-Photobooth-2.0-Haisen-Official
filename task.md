# Photobooth Haisen Official 2.0 — Master Task Tracker

## FASE 1 — Backend & Admin Middleware [SELESAI]
- [x] 1.1 Model `AdminUser` & update `AppSetting`
- [x] 1.2 Model `PhotoSession` (kolom `template_name`, `collage_path`, `raw_photos_json`, `completed_at`)
- [x] 1.3 Inisialisasi `LoginManager` di `extensions.py`
- [x] 1.4 Modul Autentikasi `app/blueprints/admin/auth.py`
- [x] 1.5 Registrasi `login_manager` & seeding default admin (`admin` / `haisen2024`) di `app/__init__.py`
- [x] 1.6 Proteksi `@login_required` & endpoint API realtime di `app/blueprints/admin/routes.py`

## FASE 2 — Admin Panel Templates [SELESAI]
- [x] 2.1 `login.html` — Tampilan login modern dengan pesan error
- [x] 2.2 `layout.html` — Sidebar SVG, server uptime, jam realtime, dan logout
- [x] 2.3 `dashboard.html` — 5 metrik card, Chart.js per-jam realtime, tabel sesi live polling
- [x] 2.4 `gallery.html` — Grid kolase, modal detail template & foto mentah, generator QR code
- [x] 2.5 `templates.html` — Grid minimalis, tombol upload (+), popup modal live preview
- [x] 2.6 `editor.html` — Canvas editor dinamis sesuai kamera aktif, snap aspect ratio, resize handle
- [x] 2.7 `settings.html` — Scanner kamera OpenCV, live test, mode output, toggle GIF, GDrive ID, reset data

## FASE 3 — Verifikasi Admin [SELESAI]
- [x] 3.1 Install dependency `flask-login` & konfigurasi `SECRET_KEY` fallback
- [x] 3.2 Uji login, proteksi rute, dan endpoint API (semua 200 OK)

---

## FASE 4 — Host Display Realtime (`app/blueprints/host` & `host/index.html`) [SELESAI]
- [x] 4.1 **Live Video Feed & OpenCV Integration**: Terhubung ke kamera aktif dari DB dengan fallback visual yang aman
- [x] 4.2 **Tampilan Standby / Waiting Screen**: Generate 4 digit PIN unik, QR code remote dinamis, indikator status WebSocket
- [x] 4.3 **Layar Live Capture & Countdown Realtime**: Overlay countdown raksasa, audio beep synthesizer, efek kilat flash jepretan, dan layar render kolase
- [x] 4.4 **Transisi Otomatis ke Halaman Galeri**: Menerima event `session_finished` dan otomatis mengarahkan monitor booth ke `/gallery/<code>`

## FASE 5 — Mobile Remote Control (`app/blueprints/mobile` & `mobile/index.html`) [SELESAI]
- [x] 5.1 **Auto-Pairing & Manual PIN**: Pairing otomatis via parameter QR scan `?code=XXXX` atau form input PIN manual ke `/api/pair`
- [x] 5.2 **Daftar Template Visual Dinamis**: Menampilkan kartu visual gambar bingkai asli template (bukan hanya judul teks) dengan rasio photostrip dan badge aktif
- [x] 5.3 **Kontrol Filter & Timer Shutter**: Pilihan filter (Natural, B&W, Vintage), timer (3s, 5s, 10s), tombol shutter interaktif dengan haptic feedback getar
- [x] 5.4 **Sinkronisasi Selesai & Proteksi Expired**: Layar remote otomatis menampilkan "ID Remote Ini Sudah Kadaluarsa" saat sesi selesai atau dibuka kembali, disertai tombol akses galeri hasil foto

## FASE 6 — Galeri Pelanggan Realtime (`app/blueprints/gallery` & `gallery/index.html`) [SELESAI]
- [x] 6.1 **Query Data Nyata Database**: Membaca data sesi asli (`collage_path`, `raw_photos_json`, template, waktu sesi) dari MySQL
- [x] 6.2 **Pemisahan Tampilan Galeri Host vs Mobile**:
  - **Layar Host (Kios Booth)**: Desain layar besar, foto kolase besar di tengah, countdown timer 25s auto-return, dan QR Code besar 180px untuk scan download
  - **Layar Mobile (Pelanggan)**: Desain mobile-first, tombol unduh High-Res ke galeri HP, tombol Web Share, dan grid foto jepretan mentah (Raw Shots)
- [x] 6.3 **Aksi Download & QR Code Sesi**: Tombol unduh file High-Res langsung, tombol unduh foto mentah satuan, generator QR code untuk scan & download di ponsel, serta Web Share API
- [x] 6.4 **Auto-Return ke Layar Host**: Monitor booth otomatis kembali ke menu standby awal (`/`) setelah 25 detik atau melalui tombol reset untuk melayani pelanggan berikutnya

## FASE 7 — Backend Controller & Engine Kolase (`app/blueprints/api/controllers.py`) [SELESAI]
- [x] 7.1 **Update Status & Penyimpanan File ke Database**: Handler capture otomatis menyimpan `collage_path`, `raw_photos_json`, `template_name`, dan status `completed` ke database
- [x] 7.2 **Integrasi Layout Slot Dinamis & Overlay Photobooth**: `CollageService` menempelkan foto kamera di layer bawah sesuai koordinat Admin Editor dan meng-overlay bingkai transparan di layer atas dengan mask alpha
- [x] 7.3 **Pengujian End-to-End Flow**: Pengujian alur penuh Host -> Mobile -> Kamera -> Database -> Galeri lolos 100%

---

## FASE 8 — Presisi Koordinat Template & Format Jepretan Kamera [SELESAI]
- [x] 8.1 **Kunci Ukuran Kanvas ke Dimensi Asli File Template**:
  - Ukuran kanvas editor dan kolase selalu menggunakan 100% dimensi asli file template yang diunggah (misal 3375x4219 px)
  - Untuk template default: kanvas menggunakan basis standar 1200x1800 px (2:3)
  - Kanvas terkunci 1:1 agar koordinat `(x, y, w, h)` selalu akurat dan tidak bergeser
- [x] 8.2 **Format Rasio Jepretan Kamera untuk Slot Foto**:
  - Kontrol "Format Ukuran Kanvas" diubah menjadi "Format Rasio Jepretan Kamera (Ukuran Slot Foto)"
  - Opsi: Rasio Kamera Aktif (misal 16:9 atau 4:3), 4:3 Standar, 16:9 Landscape, 3:2 DSLR, 1:1 Square, 9:16 Potret
  - Menerapkan aspek rasio kamera ke ukuran slot foto (panjang/tinggi slot) tanpa mengubah ukuran kanvas template
- [x] 8.3 **Deteksi Tipe Template (Overlay Transparan vs Background Solid)**:
  - Cek otomatis apakah template memiliki alpha transparan (`has_transparency`)
  - Jika template transparan (PNG RGBA): Foto kamera diletakkan di layer bawah, bingkai di-overlay di atas dengan mask alpha
  - Jika template solid / poster (RGB): Template diletakkan sebagai background dasar, dan foto kamera ditempel presisi di atas koordinat lubang yang sudah diatur
- [x] 8.4 **Kalkulasi & Verifikasi Skala Pixel-Perfect di CollageService**:
  - Normalisasi koordinat slot terhadap resolusi kanvas asli template
  - Uji penggabungan foto kamera dengan file template yang ada (`Biru_Modern_Promo_Akhir_Tahun_Instagram_Post_5.png`) lolos 100%

---

## FASE 9 — Desain Host Screen Frameless & Background Video Sinematik [SELESAI]
- [x] 9.1 **Background Video Looping & Blur**: Integrasi `<video autoplay loop muted playsinline>` menggunakan file `app/static/video/20260922-0728-41.0298756.mp4` dengan efek blur lembut (`filter: blur(14px) brightness(0.62)`), vignette radial, dan scanlines sinematik
- [x] 9.2 **Redesain UI Standby Tanpa Box Kaku (Frameless & Sleek)**:
  - Menghilangkan panel box modal putih kaku
  - Layout hero frameless dengan tipografi *Outfit* neon glow modern, badge nirkabel, PIN raksasa elegan (`Space Grotesk`), dan floating QR card semi-transparan dengan aura ambient glow halus
- [x] 9.3 **Redesain Layar Live Camera Tanpa Box Kaku**:
  - Live preview kamera fullscreen borderless terintegrasi mulus
  - Status bar floating glassmorphism di atas, hitung mundur raksasa beraksen drop shadow putih, dan overlay flash sinematik
- [x] 9.4 **Pengujian & Verifikasi Tampilan Host**: Verifikasi pemutaran video berulang dan responsivitas layar host selesai 100%

---

## FASE 10 — Perbaikan Stream Kamera Realtime (Bebas Lag/Stuck) & Selaras UI Galeri + Mobile [SELESAI]
- [x] 10.1 **Perbaikan Arsitektur Kamera (Anti Stuck & Realtime Streaming)**:
  - Redesain `CameraService` dengan Threaded Singleton & non-blocking background capture worker
  - Frame streaming MJPEG dan `capture_frame()` menggunakan shared memory buffer aktif yang sama tanpa membuka & menutup `cv2.VideoCapture` berulang kali
  - Mengeliminasi total masalah freeze/stuck saat jepretan ke-2, ke-3, dst
- [x] 10.2 **Harmonisasi Estetika UI Galeri (`app/templates/gallery/index.html`)**:
  - Tampilan Host Kios: Menggunakan background video looping blur berulang (`20260922-0728-41.0298756.mp4`), tipografi *Outfit* & *Space Grotesk*, frameless floating collage showcase dengan neon glow indigo, floating QR card modern, dan status bar sinematik
  - Tampilan Mobile Client: Tema dark luxury modern yang konsisten, floating glassmorphism, tombol download High-Res bercahaya, dan grid raw shots yang estetik
- [x] 10.3 **Harmonisasi Estetika UI Mobile Remote (`app/templates/mobile/index.html`)**:
  - Redesain mobile remote dengan tema modern sleek dark luxury selaras dengan host
  - Pilihan bingkai/template visual floating cards dengan preview gambar asli beraksen neon border
  - Filter & Timer segmented buttons yang responsif dan haptic feedback
  - Layar "ID Remote Ini Sudah Kadaluarsa" dan form PIN yang elegan, modern, dan bebas kotak kaku
- [x] 10.4 **Verifikasi & Pengujian Integrasi**: Multi-shot test capture dan pengecekan sintaks rendering template berjalan sukses 100%
## FASE 11 — Firewall Rute Berbahaya & Halaman Error 404/403/500 Sinematik [SELESAI]
- [x] 11.1 **Security Firewall Before-Request**:
  - Filter otomatis URL berbahaya dan probing exploit bot (`phpmyadmin`, `pma`, `adminer`, `wp-admin`, `wp-login`, `.env`, `.git`, `.sql`, `config.php`, `shell`, `backup`, `eval-stdin`, dll)
  - Otomatis menolak dan mengalihkan akses ke respons HTTP 403 Forbidden dengan halaman blokir keamanan
- [x] 11.2 **Custom Error Handler (404, 403, 500)**:
  - Menggantikan tampilan teks putih polos bawaan server (*Not Found The requested URL was not found on the server*)
  - Menerapkan template terpadu `app/templates/errors/error.html`
- [x] 11.3 **Desain Halaman Error Sinematik & Selaras**:
  - Menggunakan background video looping blur berulang (`20260922-0728-41.0298756.mp4`), vignette, dan scanlines
  - Status badge *BLOCKED ACCESS*, kode error raksasa neon glow, indikator target path & action taken, serta tombol cepat *Kembali ke Layar Booth* dan *Login Operator*
- [x] 11.4 **Pengujian & Verifikasi**: Pengujian test client untuk 404, probing `.env`, dan path `phpmyadmin` lolos 100%
- [x] 12.1 **Halaman Admin GIF Gallery (`/admin/gif-gallery`)**: Grid visual semua file GIF photobooth, modal preview ukuran penuh, tombol download langsung, dan QR code dinamis per GIF yang bisa di-zoom untuk scan download di HP
- [x] 12.2 **Halaman Admin Foto Mentah (`/admin/raw-gallery`)**: Menampilkan semua foto jepretan mentah yang dikelompokkan per sesi/ID
- [x] 12.3 **Download Sepaket Per Sesi via QR & ZIP**: Fitur tombol "QR Semua" dan endpoint `/admin/api/download-raw-zip/<code>` untuk mengunduh seluruh foto mentah sesi tersebut dalam format ZIP melalui scan QR smartphone
- [x] 12.4 **Pilih Foto Mentah Tertentu & Download via QR**: Fitur interaktif centang foto, sticky action bar, quick QR per foto, dan endpoint `/admin/api/download-selected-zip` dengan dukungan GET query params agar smartphone dapat langsung mengunduh foto yang dipilih via scan QR
- [x] 13.1 **Perapihan Struktur Template Admin**: Mengonsolidasi library `qrcodejs` dan styling modal global ke `layout.html`, membersihkan duplikasi tag skrip di `gallery.html`, `gif_gallery.html`, dan `raw_gallery.html`
- [x] 13.2 **Audit & Pengamanan API / Mencegah Kebocoran Data**:
  - Validasi ketat kode sesi (`is_safe_code`)
  - Pencegahan 100% path traversal (`is_safe_file_in_dir`) dan pembatasan ekstensi gambar aman (`.jpg`, `.jpeg`, `.png`, `.webp`)
  - Pembatasan kuota zip items (`MAX_ZIP_ITEMS = 60`) untuk mencegah kehabisan memori server
  - Penambahan security response headers (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`)
  - Firewall blokir file/direktori sistem tersembunyi (`/.env`, `/.git`, dll)
- [x] 13.3 **Desain Responsif Admin Panel (`layout.html`)**:
  - Off-canvas drawer navigasi di perangkat mobile & tablet dengan tombol hamburger dan tombol close
  - Overlay backdrop dengan efek blur lembut yang menutup sidebar saat diklik
  - Layout topbar adaptif dengan penataan jam, uptime, dan judul halaman yang rapi di berbagai ukuran layar
  - Peningkatan padding responsif (`p-4 sm:p-6 lg:p-8`) dan scrollbar modern
## FASE 14 — Sistem Siklus PIN Sesi, Auto-Expire 3 Menit, Reset PIN Admin, & Auto-Reset Filter [SELESAI]
- [x] 14.1 **Auto-Reset Filter Kamera ke Natural**:
  - Filter kamera dan live stream otomatis di-reset ke `classic` (Natural) setiap kali sesi selesai (`session_finished`) atau monitor kembali ke standby (`/`).
  - Remote HP otomatis menginisialisasi filter awal ke `classic` saat pairing berhasil.
- [x] 14.2 **Siklus Hidup Kode PIN Sesi (Anti-Ganti Sembarangan)**:
  - Kode PIN sesi dipertahankan selama belum digunakan dan berumur ≤ 3 menit (180 detik).
  - Refresh browser di monitor booth tidak lagi mengganti kode PIN yang sedang aktif.
  - Kode PIN otomatis diganti jika sesi standby sudah menganggur lebih dari 3 menit tanpa digunakan.
- [x] 14.3 **Timer Auto-Refresh Standby 3 Menit di Layar Booth**:
  - Monitor booth (`host/index.html`) memantau durasi standby dan otomatis merefresh PIN + QR Code setelah 3 menit tanpa reload manual.
- [x] 14.4 **Fitur Reset PIN Sesi Baru dari Admin Panel**:
  - Endpoint `POST /admin/api/reset-session-pin` dengan autentikasi `@login_required`.
  - Tombol aksi "Reset PIN Sesi" di topbar Admin (`layout.html`) yang dapat diakses dari halaman admin mana saja.
  - Sinyal WebSocket `session_pin_reset` memperbarui nomor PIN dan QR Code di monitor booth secara instan tanpa perlu reload manual.

---

## FASE 15 — Sistem Penyimpanan Aman (Private Storage) & Otorisasi Akses File [SELESAI]
- [x] 15.1 **Struktur Private Storage di Luar Folder Web Publik**:
  - Direktori `storage/` dibuat di root project terisolasi dari jangkauan web server publik (`storage/collages/`, `storage/gifs/`, `storage/temp/`, `storage/templates/`).
  - `.gitignore` dikonfigurasi agar file pengunjung tidak masuk ke git.
  - `config.py` dikonfigurasi dengan `PRIVATE_STORAGE_PATH`.
- [x] 15.2 **Pembaruan Layanan & Generator File**:
  - `CollageService` (`collage_service.py`): output kolase dan template frame dipindahkan ke `storage/`.
  - `GifService` (`gif_service.py`): animasi GIF dipindahkan ke `storage/gifs/`.
  - `CameraService` (`camera_service.py`): foto mentah disimpan ke `storage/temp/`.
- [x] 15.3 **Endpoint Secure File Serving (`/api/files/<file_type>/<filename>`)**:
  - Validasi ketat nama file (anti-path traversal dengan `secure_filename` + prefix check) dan whitelist ekstensi (`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`).
  - Otorisasi berlapis: Admin dapat mengakses semua file; Pengunjung/smartphone hanya dapat mengakses file milik sesi mereka via parameter `?code=<code>` yang divalidasi ke database `PhotoSession`; Akses tanpa izin otomatis diblokir `403 Forbidden`.
  - Dukungan URL alias `/files/<file_type>/<filename>`.
- [x] 15.4 **Migrasi URL & Template Semua Halaman**:
  - Template Galeri Pengunjung (`gallery/index.html`): Kolase, foto mentah, animasi GIF, dan batch download ZIP/direct beralih ke `serve_file` dengan token `code`.
  - Template Admin Galeri Kolase (`admin/gallery.html`): Thumbnail kolase dan modal foto mentah diperbarui ke `serve_file`.
  - Template Admin GIF Galeri (`admin/gif_gallery.html`): Thumbnail GIF dan modal download diperbarui ke `serve_file`.
  - Template Admin Galeri Foto Mentah (`admin/raw_gallery.html`): Thumbnail, quick preview, dan single QR scan diperbarui ke `serve_file` dengan otorisasi kode sesi.
  - Template Admin Template Bingkai (`admin/templates.html` & `admin/editor.html`): Thumbnail dan kanvas fabric/editor beralih ke `serve_file`.
  - Template Mobile Remote (`mobile/index.html` & `mobile/routes.py`): Pilihan frame template membaca dan me-render dari private storage via `serve_file`.
  - Bilboard Screen (`bilboard/routes.py`): Membaca cache dan menyajikan gambar via `serve_file`.
- [x] 15.5 **Migrasi Data & Pengujian Integrasi 100%**:
  - Script `migrate_storage.py` berhasil memindahkan 157 file media lama ke private storage.
  - Pengujian unauthorized access (403), valid session owner access (200), anti-path traversal (403), dan rendering 9 halaman utama aplikasi photobooth berhasil 100%.
