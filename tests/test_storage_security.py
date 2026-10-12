# import sys
# import os

# # Menambahkan direktori root proyek ke dalam sys.path secara dinamis 
# # agar modul 'app' dapat ditemukan saat file test dijalankan langsung.
# current_dir = os.path.dirname(os.path.abspath(__file__))
# root_dir = os.path.dirname(current_dir)
# if root_dir not in sys.path:
#     sys.path.insert(0, root_dir)

# import unittest
# import json
# from app import create_app
# from extensions import db
# from app.models.session_model import PhotoSession

# class StorageSecurityTestCase(unittest.TestCase):
#     def setUp(self):
#         self.app = create_app()
#         self.app.config['TESTING'] = True
#         self.client = self.app.test_client()
#         self.app_context = self.app.app_context()
#         self.app_context.push()

#         # Ambil atau pastikan ada sesi pengujian di database
#         self.session_record = PhotoSession.query.filter(
#             PhotoSession.collage_path.isnot(None)
#         ).order_by(PhotoSession.id.desc()).first()

#         if not self.session_record:
#             # Buat dummy sesi jika database kosong (ditambahkan # type: ignore untuk linter)
#             self.session_record = PhotoSession(  # type: ignore
#                 unique_code='7788',
#                 status='completed',
#                 collage_path='collage_test_7788.jpg',
#                 raw_photos_json=json.dumps(['capture_test_1.jpg'])
#             )
#             db.session.add(self.session_record)
#             db.session.commit()

#             # Buat file dummy fisik di storage agar send_file tidak 404
#             storage_path = self.app.config.get('PRIVATE_STORAGE_PATH')
#             if storage_path:
#                 os.makedirs(os.path.join(storage_path, 'collages'), exist_ok=True)
#                 with open(os.path.join(storage_path, 'collages', 'collage_test_7788.jpg'), 'wb') as f:
#                     f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')

#         self.valid_code = self.session_record.unique_code
#         self.collage_file = self.session_record.collage_path

#     def tearDown(self):
#         self.app_context.pop()

#     def test_01_public_direct_access_blocked(self):
#         """Simulasi 1: Penyerang menembak langsung URL file tanpa sesi galeri aktif."""
#         url = f"/api/files/collages/{self.collage_file}?code={self.valid_code}"
#         res = self.client.get(url)
#         self.assertEqual(res.status_code, 403, "Akses langsung via URL publik tanpa sesi harus ditolak (403).")

#     def test_02_path_traversal_attack_blocked(self):
#         """Simulasi 2: Serangan path traversal (mencoba membaca config/file sistem)."""
#         res = self.client.get("/api/files/collages/../../config.py")
#         self.assertIn(res.status_code, [403, 404], "Serangan path traversal harus dicegat (403/404).")

#     def test_03_wrong_session_pin_blocked(self):
#         """Simulasi 3: Akses dengan PIN / kode yang salah atau acak."""
#         self.client.get("/gallery/999999")
#         res = self.client.get(f"/api/files/collages/{self.collage_file}?code=999999")
#         self.assertEqual(res.status_code, 403, "Akses menggunakan PIN salah harus ditolak (403).")

#     def test_04_session_hijacking_between_users_blocked(self):
#         """Simulasi 4: Klien A mencoba mengintip foto milik Klien B."""
#         fake_code = "1122"
#         self.client.get(f"/gallery/{fake_code}")
#         res = self.client.get(f"/api/files/collages/{self.collage_file}?code={fake_code}")
#         self.assertEqual(res.status_code, 403, "Klien tidak boleh mengakses file sesi lain (403).")

#     def test_05_external_hotlinking_blocked(self):
#         """Simulasi 5: Serangan hotlinking dari domain luar / situs web pihak ketiga."""
#         self.client.get(f"/gallery/{self.valid_code}")
#         res = self.client.get(
#             f"/api/files/collages/{self.collage_file}?code={self.valid_code}",
#             headers={'Referer': 'https://evil-hacker-site.com'}
#         )
#         self.assertEqual(res.status_code, 403, "Hotlinking dari domain luar harus diblokir (403).")

#     def test_06_legitimate_client_gallery_access_success(self):
#         """Simulasi 6: Pengunjung normal membuka galeri resmi dengan PIN yang valid."""
#         res_page = self.client.get(f"/gallery/{self.valid_code}")
#         self.assertEqual(res_page.status_code, 200, "Halaman galeri pengunjung valid harus terbuka (200).")

#         res_file = self.client.get(
#             f"/api/files/collages/{self.collage_file}?code={self.valid_code}",
#             headers={'Referer': f"http://localhost/gallery/{self.valid_code}"}
#         )
#         self.assertEqual(res_file.status_code, 200, "Pengunjung dengan PIN sah harus sukses memuat foto (200).")

#     def test_07_probe_and_suspicious_routes_blocked(self):
#         """Simulasi 7: Bot scanner / serangan probing rute aneh."""
#         strange_endpoints = [
#             '/.env',
#             '/.git/config',
#             '/wp-login.php',
#             '/phpmyadmin',
#             '/admin.php',
#             '/config.php',
#             '/dump.sql',
#             '/shell.sh'
#         ]
#         for route in strange_endpoints:
#             res = self.client.get(route)
#             self.assertEqual(res.status_code, 403, f"Probing rute mencurigakan {route} harus diblokir (403).")

# if __name__ == '__main__':
#     unittest.main()






# import sys
# import os

# # Menambahkan direktori root proyek ke dalam sys.path secara dinamis 
# current_dir = os.path.dirname(os.path.abspath(__file__))
# root_dir = os.path.dirname(current_dir)
# if root_dir not in sys.path:
#     sys.path.insert(0, root_dir)

# import unittest
# import json
# import uuid
# from app import create_app
# from extensions import db
# from app.models.session_model import PhotoSession

# class StorageSecurityTestCase(unittest.TestCase):
#     def setUp(self):
#         self.app = create_app()
#         self.app.config['TESTING'] = True
#         self.client = self.app.test_client()
#         self.app_context = self.app.app_context()
#         self.app_context.push()

#         # Gunakan UUID untuk menjamin unique_code selalu berbeda di setiap test case
#         unique_suffix = uuid.uuid4().hex[:4]
#         self.test_code = f"7{unique_suffix}"
#         self.test_collage = f"collage_test_{self.test_code}.jpg"

#         # Buat dummy sesi pengujian di database untuk setiap test method
#         self.session_record = PhotoSession(  # type: ignore
#             unique_code=self.test_code,
#             status='completed',
#             collage_path=self.test_collage,
#             raw_photos_json=json.dumps(['capture_test_1.jpg'])
#         )
#         db.session.add(self.session_record)
#         db.session.commit()

#         # Buat file dummy fisik di berbagai kemungkinan path storage agar aman dari 404
#         storage_path = self.app.config.get('PRIVATE_STORAGE_PATH')
#         paths_to_create = []
#         if storage_path:
#             paths_to_create.append(os.path.join(storage_path, 'collages'))
        
#         # Fallback direktori lokal proyek
#         paths_to_create.append(os.path.join(root_dir, 'storage', 'collages'))

#         for p in paths_to_create:
#             try:
#                 os.makedirs(p, exist_ok=True)
#                 with open(os.path.join(p, self.test_collage), 'wb') as f:
#                     f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')
#             except Exception:
#                 pass

#         self.valid_code = self.session_record.unique_code
#         self.collage_file = self.session_record.collage_path

#     def tearDown(self):
#         self.app_context.pop()

#     def test_01_public_direct_access_blocked(self):
#         """Simulasi 1: Penyerang menembak langsung URL file tanpa sesi galeri aktif."""
#         url = f"/api/files/collages/{self.collage_file}?code={self.valid_code}"
#         res = self.client.get(url)
#         self.assertEqual(res.status_code, 403, "Akses langsung via URL publik tanpa sesi harus ditolak (403).")

#     def test_02_path_traversal_attack_blocked(self):
#         """Simulasi 2: Serangan path traversal (mencoba membaca config/file sistem)."""
#         res = self.client.get("/api/files/collages/../../config.py")
#         self.assertIn(res.status_code, [403, 404], "Serangan path traversal harus dicegat (403/404).")

#     def test_03_wrong_session_pin_blocked(self):
#         """Simulasi 3: Akses dengan PIN / kode yang salah atau acak."""
#         self.client.get("/gallery/999999")
#         res = self.client.get(f"/api/files/collages/{self.collage_file}?code=999999")
#         self.assertEqual(res.status_code, 403, "Akses menggunakan PIN salah harus ditolak (403).")

#     def test_04_session_hijacking_between_users_blocked(self):
#         """Simulasi 4: Klien A mencoba mengintip foto milik Klien B."""
#         fake_code = "1122"
#         self.client.get(f"/gallery/{fake_code}")
#         res = self.client.get(f"/api/files/collages/{self.collage_file}?code={fake_code}")
#         self.assertEqual(res.status_code, 403, "Klien tidak boleh mengakses file sesi lain (403).")

#     def test_05_external_hotlinking_blocked(self):
#         """Simulasi 5: Serangan hotlinking dari domain luar / situs web pihak ketiga."""
#         self.client.get(f"/gallery/{self.valid_code}")
#         res = self.client.get(
#             f"/api/files/collages/{self.collage_file}?code={self.valid_code}",
#             headers={'Referer': 'https://evil-hacker-site.com'}
#         )
#         self.assertEqual(res.status_code, 403, "Hotlinking dari domain luar harus diblokir (403).")

#     def test_06_legitimate_client_gallery_access_success(self):
#         """Simulasi 6: Pengunjung normal membuka galeri resmi dengan PIN yang valid."""
#         res_page = self.client.get(f"/gallery/{self.valid_code}")
#         self.assertEqual(res_page.status_code, 200, "Halaman galeri pengunjung valid harus terbuka (200).")
#         _ = res_page.data

#         res_file = self.client.get(
#             f"/api/files/collages/{self.collage_file}?code={self.valid_code}",
#             headers={'Referer': f"http://localhost/gallery/{self.valid_code}"}
#         )
#         self.assertEqual(res_file.status_code, 200, "Pengunjung dengan PIN sah harus sukses memuat foto (200).")
#         _ = res_file.data

#     def test_07_probe_and_suspicious_routes_blocked(self):
#         """Simulasi 7: Bot scanner / serangan probing rute aneh."""
#         strange_endpoints = [
#             '/.env',
#             '/.git/config',
#             '/wp-login.php',
#             '/phpmyadmin',
#             '/admin.php',
#             '/config.php',
#             '/dump.sql',
#             '/shell.sh'
#         ]
#         for route in strange_endpoints:
#             res = self.client.get(route)
#             self.assertEqual(res.status_code, 403, f"Probing rute mencurigakan {route} harus diblokir (403).")

#     def test_08_open_gallery_after_session_completion(self):
#         """Simulasi 8: Pengguna membuka halaman galeri tepat setelah sesi foto selesai."""
#         unique_suffix_2 = uuid.uuid4().hex[:4]
#         code_2 = f"8{unique_suffix_2}"
#         collage_2 = f"collage_test_{code_2}.jpg"

#         completed_session = PhotoSession(  # type: ignore
#             unique_code=code_2,
#             status='completed',
#             collage_path=collage_2,
#             raw_photos_json=json.dumps(['capture_2_1.jpg', 'capture_2_2.jpg'])
#         )
#         db.session.add(completed_session)
#         db.session.commit()

#         res = self.client.get(f"/gallery/{completed_session.unique_code}")
#         self.assertEqual(res.status_code, 200, "Halaman galeri setelah sesi selesai harus terbuka dengan sukses (200).")
        
#         response_text = res.data.decode('utf-8')
#         self.assertTrue(
#             completed_session.unique_code in response_text or completed_session.collage_path in response_text,
#             "Halaman galeri harus memuat informasi sesi atau file terkait."
#         )

# if __name__ == '__main__':
#     unittest.main()