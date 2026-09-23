import os
import json
from PIL import Image, ImageOps, ImageDraw, ImageFont
from datetime import datetime
from app.models.admin_model import AppSetting

# Base dir project (root folder tempat run.py berada)
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class CollageService:
    def __init__(self):
        self.output_dir = os.path.join(_BASE_DIR, 'storage', 'collages')
        self.template_dir = os.path.join(_BASE_DIR, 'storage', 'templates')
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.template_dir, exist_ok=True)


    def _get_setting(self, key, default=''):
        try:
            setting = AppSetting.query.filter_by(key=key).first()
            return setting.value if setting and setting.value is not None else default
        except Exception:
            return default

    def _parse_coords(self, coords_json):
        """
        Mem-parsing format koordinat dari database.
        Mendukung format objek baru {base_width, base_height, slots} dan format list lama [{x, y, w, h}].
        """
        if not coords_json:
            return None, 1200, 1800

        try:
            data = json.loads(coords_json)
            if isinstance(data, dict) and 'slots' in data:
                slots = data.get('slots', [])
                base_w = int(data.get('base_width', 1200))
                base_h = int(data.get('base_height', 1800))
                return slots, base_w, base_h
            elif isinstance(data, list):
                return data, 1200, 1800
        except Exception:
            pass
        return None, 1200, 1800

    def get_template_slot_count(self, template_name='default'):
        """Menghitung berapa banyak foto kamera yang dibutuhkan oleh template."""
        if not template_name or template_name == 'default':
            template_name = self._get_setting('active_custom_template', 'default')

        coord_key = f"layout_coords_{template_name}"
        coords_json = self._get_setting(coord_key, None)
        slots, _, _ = self._parse_coords(coords_json)

        if slots and len(slots) > 0:
            return len(slots)

        return 4  # Standar 4 jepretan jika belum pernah diatur koordinatnya

    def create_collage(self, image_paths, template_name=None):
        """
        Menggabungkan foto hasil jepretan kamera dengan template sesuai koordinat Admin Editor.
        Mendeteksi secara cerdas apakah template berupa Overlay Transparan (PNG RGBA)
        ataukah Background Solid (JPG/PNG RGB poster) sehingga foto menempel presisi.
        """
        if not image_paths:
            return None, "Tidak ada foto untuk digabungkan."

        try:
            if not template_name or template_name == 'default':
                template_name = self._get_setting('active_custom_template', 'default')

            # 1. Ambil koordinat kustom dari database
            coord_key = f"layout_coords_{template_name}"
            coords_json = self._get_setting(coord_key, None)
            slots, base_w, base_h = self._parse_coords(coords_json)

            # 2. Cek ketersediaan file template kustom
            custom_template_path = os.path.join(self.template_dir, template_name) if template_name != 'default' else None
            custom_frame = None
            has_transparency = False

            if custom_template_path and os.path.exists(custom_template_path):
                raw_img = Image.open(custom_template_path)
                canvas_width, canvas_height = raw_img.size

                # Periksa apakah gambar memiliki piksel transparan nyata untuk lubang foto
                if raw_img.mode in ('RGBA', 'LA') or (raw_img.mode == 'P' and 'transparency' in raw_img.info):
                    custom_frame = raw_img.convert('RGBA')
                    alpha = custom_frame.split()[-1]
                    min_alpha, _ = alpha.getextrema()
                    if min_alpha < 240:  # Memiliki area transparan nyata
                        has_transparency = True
                else:
                    custom_frame = raw_img.convert('RGBA')
                    has_transparency = False
            else:
                canvas_width, canvas_height = base_w, base_h

            # 3. Hitung rasio penskalaan koordinat jika kanvas berbeda ukuran dengan basis saat editor
            scale_x = canvas_width / float(base_w) if base_w > 0 else 1.0
            scale_y = canvas_height / float(base_h) if base_h > 0 else 1.0

            # 4. Siapkan Kanvas dan Layering
            if custom_frame and not has_transparency:
                # KASUS A: Template Solid / Poster Latar Belakang (RGB)
                # Template ditaruh sebagai layer dasar, foto kamera ditempel DI ATASNYA sesuai koordinat
                collage = custom_frame.copy()
            else:
                # KASUS B: Template Transparan (RGBA) atau Template Default
                # Kanvas dasar putih, foto kamera ditempel di layer bawah
                collage = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 255))

            # 5. Tempel Foto-foto Kamera Sesuai Koordinat Slot
            if slots and len(slots) > 0:
                for i, slot in enumerate(slots):
                    if i < len(image_paths) and os.path.exists(image_paths[i]):
                        img = Image.open(image_paths[i]).convert('RGBA')

                        # Hitung posisi dan ukuran target slot secara presisi 1:1
                        sw = max(10, int(round(float(slot['w']) * scale_x)))
                        sh = max(10, int(round(float(slot['h']) * scale_y)))
                        sx = int(round(float(slot['x']) * scale_x))
                        sy = int(round(float(slot['y']) * scale_y))

                        # Crop dan fit foto kamera agar proporsional di lubang slot
                        fitted_img = ImageOps.fit(img, (sw, sh), centering=(0.5, 0.5))
                        collage.paste(fitted_img, (sx, sy))
            else:
                # Fallback otomatis jika slot koordinat belum pernah diedit
                num_photos = len(image_paths)
                padding = int(round(canvas_width * 0.05))
                footer_space = int(round(canvas_height * 0.12)) if not custom_frame else padding
                available_height = canvas_height - footer_space - (padding * (num_photos + 1))
                slot_height = max(100, available_height // num_photos)
                slot_width = canvas_width - (padding * 2)

                y_offset = padding
                for path in image_paths:
                    if os.path.exists(path):
                        img = Image.open(path).convert('RGBA')
                        fitted_img = ImageOps.fit(img, (slot_width, slot_height), centering=(0.5, 0.5))
                        collage.paste(fitted_img, (padding, y_offset))
                        y_offset += slot_height + padding

            # 6. Jika Template Memiliki Transparansi (Overlay Frame)
            if custom_frame and has_transparency:
                # Tempel bingkai di atas foto kamera dengan alpha mask
                collage.paste(custom_frame, (0, 0), mask=custom_frame)
            elif not custom_frame:
                # Watermark teks jika menggunakan template standar bawaan
                watermark_text = self._get_setting('watermark_text', 'HAISEN OFFICIAL')
                draw = ImageDraw.Draw(collage)
                try:
                    font_title = ImageFont.truetype("arial.ttf", int(canvas_height * 0.022))
                    font_sub = ImageFont.truetype("arial.ttf", int(canvas_height * 0.013))
                except Exception:
                    font_title = ImageFont.load_default()
                    font_sub = ImageFont.load_default()

                text_y1 = canvas_height - int(canvas_height * 0.065)
                text_y2 = canvas_height - int(canvas_height * 0.035)
                draw.text((canvas_width / 2, text_y1), watermark_text.upper(), fill="#1F2937", anchor="mm", font=font_title)
                draw.text((canvas_width / 2, text_y2), datetime.now().strftime("%d %B %Y • Self Photo"), fill="#9CA3AF", anchor="mm", font=font_sub)

            # 7. Konversi ke JPEG Kualitas Tinggi
            final_collage = collage.convert('RGB')
            filename = f"collage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            final_collage.save(filepath, format='JPEG', quality=96)

            return filepath, None

        except Exception as e:
            return None, f"Gagal merangkai kolase: {str(e)}"