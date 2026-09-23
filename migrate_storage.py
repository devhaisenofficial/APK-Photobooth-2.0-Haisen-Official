import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OLD_UPLOADS = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
NEW_STORAGE = os.path.join(BASE_DIR, 'storage')

SUBFOLDERS = ['collages', 'gifs', 'temp', 'templates']

def migrate():
    print("=== Memulai Migrasi Storage ===")
    total_copied = 0
    total_skipped = 0

    for sub in SUBFOLDERS:
        src_dir = os.path.join(OLD_UPLOADS, sub)
        dst_dir = os.path.join(NEW_STORAGE, sub)
        os.makedirs(dst_dir, exist_ok=True)

        if not os.path.exists(src_dir):
            print(f"[-] Folder {sub} di static/uploads tidak ditemukan, dilewati.")
            continue

        files = os.listdir(src_dir)
        print(f"\n[*] Memeriksa folder '{sub}': {len(files)} file ditemukan.")

        for f in files:
            src_file = os.path.join(src_dir, f)
            dst_file = os.path.join(dst_dir, f)

            if os.path.isfile(src_file):
                if not os.path.exists(dst_file):
                    shutil.copy2(src_file, dst_file)
                    print(f"  [+] Disalin: {f}")
                    total_copied += 1
                else:
                    total_skipped += 1

    print(f"\n=== Migrasi Selesai! ===")
    print(f"Total file baru disalin: {total_copied}")
    print(f"Total file sudah ada (dilewati): {total_skipped}")

if __name__ == '__main__':
    migrate()
