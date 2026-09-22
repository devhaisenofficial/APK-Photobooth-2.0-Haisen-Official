import os
from PIL import Image

class GifService:
    """
    Layanan pembuatan animasi GIF photobooth dari foto-foto jepretan mentah
    sesuai target kode sesi (PIN / Session ID).
    """
    def __init__(self):
        self.output_dir = os.path.join('app', 'static', 'uploads', 'gifs')
        os.makedirs(self.output_dir, exist_ok=True)

    def create_gif(self, image_paths, session_code, duration=450, max_width=720):
        """
        Menggabungkan daftar foto jepretan mentah menjadi satu animasi GIF berulang.
        :param image_paths: list path foto (misal: ['app/static/uploads/temp/capture_1.jpg', ...])
        :param session_code: kode unik sesi booth (misal: '5760')
        :param duration: durasi per frame dalam milidetik (default 450ms)
        :param max_width: resolusi lebar maksimum untuk optimasi ukuran file GIF
        :return: (gif_filepath, error_message)
        """
        if not image_paths or len(image_paths) == 0:
            return None, "Daftar foto kosong, tidak dapat membuat animasi GIF."

        frames = []
        try:
            for p in image_paths:
                if os.path.exists(p):
                    img = Image.open(p)
                    # Konversi ke RGB (jika RGBA/lainnya)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # Resize proporsional agar ukuran GIF ringan dan cepat dimuat di mobile/web
                    w, h = img.size
                    if w > max_width:
                        new_h = int(h * (max_width / w))
                        img = img.resize((max_width, new_h), Image.Resampling.LANCZOS)

                    frames.append(img)

            if not frames:
                return None, "Tidak ada file foto mentah yang valid ditemukan."

            filename = f"gif_{session_code}_{os.urandom(4).hex()}.gif"
            out_path = os.path.join(self.output_dir, filename)

            # Simpan sebagai GIF looping animasi tak hingga (loop=0)
            frames[0].save(
                out_path,
                format='GIF',
                save_all=True,
                append_images=frames[1:],
                duration=duration,
                loop=0,
                optimize=True
            )

            return out_path, None

        except Exception as e:
            return None, f"Gagal membuat animasi GIF: {str(e)}"
