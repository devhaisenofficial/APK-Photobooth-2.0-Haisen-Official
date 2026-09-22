# Admin Panel — Full Rebuild Plan

## Ringkasan

Membangun ulang semua halaman admin (`dashboard`, `gallery`, `templates`, `editor`, `settings`) agar benar-benar terhubung ke database, realtime via SocketIO, dengan middleware autentikasi login, dan UI profesional tanpa data dummy.

---

## TODO List (Urutan Eksekusi)

### FASE 1 — Backend & Middleware

- [ ] **1.1** Tambah model `AdminUser` ke `app/models/admin_model.py` (username, hashed password)
- [ ] **1.2** Tambah model `PhotoResult` ke `app/models/session_model.py` (link ke PhotoSession, simpan path raw photos, path collage, template name)
- [ ] **1.3** Tambah kolom `template_name`, `raw_photos` ke model PhotoSession atau buat relasi
- [ ] **1.4** Buat `app/blueprints/admin/auth.py` — route login/logout dengan `flask_login`
- [ ] **1.5** Tambah `flask_login` ke `extensions.py` dan `__init__.py`
- [ ] **1.6** Tambah `login_manager` + `@login_required` decorator di semua admin routes
- [ ] **1.7** Perbarui `admin/routes.py`:
  - Dashboard: kirim stats realtime (total, active, completed, today, uptime)
  - Gallery: baca DB + filesystem (collages dengan metadata)
  - Templates: full CRUD, delete template, set active
  - Editor: load koordinat per template, save ke DB
  - Settings: kamera list dinamis, watermark, toggle GIF, hapus semua data
- [ ] **1.8** Tambah API endpoints JSON untuk polling realtime dashboard:
  - `GET /admin/api/stats` → stats terbaru
  - `GET /admin/api/gallery/<filename>` → detail collage
  - `DELETE /admin/api/templates/<filename>` → hapus template
  - `POST /admin/api/reset-data` → hapus semua data + file
  - `GET /admin/api/cameras` → detect available cameras (OpenCV)
  - `POST /admin/api/test-camera` → test kamera aktif
  - `GET /admin/api/uptime` → uptime sistem

### FASE 2 — Templates HTML

- [ ] **2.1** `admin/login.html` — halaman login bersih, minimal
- [ ] **2.2** `admin/layout.html` — sidebar dengan ikon Lucide SVG, nav aktif, logout, status server realtime, uptime display
- [ ] **2.3** `admin/dashboard.html` — stat cards, grafik Chart.js realtime via polling, recent sessions table, uptime + tanggal hari ini
- [ ] **2.4** `admin/gallery.html` — grid foto, klik → modal detail (template, raw count, QR download, tanggal, path)
- [ ] **2.5** `admin/templates.html` — grid template minimalis, tombol + popup upload, preview, delete, set active
- [ ] **2.6** `admin/editor.html` — canvas dinamis, deteksi resolusi kamera, resize slot, save ke DB per template
- [ ] **2.7** `admin/settings.html` — pilih kamera (dropdown populated dari OpenCV detect), test kamera, watermark input, toggle GIF/foto, Google Drive ID, hapus semua data (konfirmasi modal)

### FASE 3 — Verifikasi & Polish

- [ ] **3.1** Jalankan app, pastikan login redirect bekerja
- [ ] **3.2** Test setiap halaman end-to-end
- [ ] **3.3** Pastikan tidak ada data dummy

---

## Proposed Changes

---

### Model Layer

#### [MODIFY] [admin_model.py](file:///d:/APLIKASI%20PHOTOBOOTH%20SELF%20PHOTO%20HAISEN%20OFFICIAL%202.0/app/models/admin_model.py)
- Tambah class `AdminUser(db.Model, UserMixin)` dengan `id, username, password_hash`
- Tambah method `set_password`, `check_password`

#### [MODIFY] [session_model.py](file:///d:/APLIKASI%20PHOTOBOOTH%20SELF%20PHOTO%20HAISEN%20OFFICIAL%202.0/app/models/session_model.py)
- Tambah kolom `template_name`, `collage_path`, `raw_photos_json` ke `PhotoSession`
- Tambah `completed_at`

---

### Auth Layer

#### [NEW] app/blueprints/admin/auth.py
- `GET/POST /admin/login` — form login
- `GET /admin/logout` — clear session

#### [MODIFY] extensions.py
- Tambah `LoginManager`

#### [MODIFY] app/__init__.py
- Register `login_manager`, set `login_view = 'admin.login'`
- Seed admin user default jika belum ada

---

### Routes Layer

#### [MODIFY] [routes.py](file:///d:/APLIKASI%20PHOTOBOOTH%20SELF%20PHOTO%20HAISEN%20OFFICIAL%202.0/app/blueprints/admin/routes.py)
- Semua route dilindungi `@login_required`
- Dashboard: kirim `uptime`, `today_count`, `total_photos`, `stats_by_status`
- Gallery: baca collages dari filesystem + enrich dengan metadata DB
- Templates: tambah route DELETE, pastikan preview path benar
- Settings: detect cameras via OpenCV, save semua toggle ke `AppSetting`
- Tambah semua API JSON endpoints

---

### Template Layer

#### [MODIFY] layout.html
- Ikon SVG inline per nav item
- Logout link dengan konfirmasi
- Uptime + clock realtime via JS
- Status badge realtime

#### [NEW/MODIFY] semua halaman admin (6 file)

---

## Open Questions

> [!IMPORTANT]
> **Admin credentials default**: Akan dibuat user admin default `admin` / `haisen2024` yang di-seed saat pertama kali app dijalankan. Apakah Anda ingin menggunakan password berbeda?

> [!IMPORTANT]
> **QR Code library**: Untuk QR download di gallery, akan menggunakan library `qrcode` Python + generate QR sebagai data URL inline. Perlu install `qrcode[pil]` ke requirements.txt.

> [!NOTE]
> **Realtime dashboard**: Menggunakan polling `setInterval` setiap 5 detik ke API JSON (bukan push SocketIO) karena lebih stabil untuk admin panel yang tidak terhubung ke WebSocket session foto.

## Verification Plan

- Jalankan `python run.py` → akses `/admin` → redirect ke login
- Login dengan credentials default → masuk dashboard
- Cek setiap halaman berfungsi (gallery kosong OK, templates kosong OK)
- Test upload template, set active, editor save
- Test settings: detect kamera, watermark save, delete data (dengan data dummy manual)
