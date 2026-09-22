import os
from dotenv import load_dotenv, find_dotenv

# Memastikan file .env ditemukan dan dimuat secara akurat
load_dotenv(find_dotenv())

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'haisen-photobooth-secret-key-2024'
    
    # Ambil nilai dari .env
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    
    # Validasi pengaman jika variabel bernilai string 'None' atau kosong
    if not DB_USER or DB_USER == 'None':
        DB_USER = 'root'
    if not DB_HOST or DB_HOST == 'None':
        DB_HOST = 'localhost'
    if not DB_PORT or DB_PORT == 'None' or DB_PORT == 'none':
        DB_PORT = '3306'
    if not DB_NAME or DB_NAME == 'None':
        DB_NAME = 'photobooth_db'
        
    # Tangani password jika kosong atau 'None'
    password_str = f":{DB_PASSWORD}" if DB_PASSWORD and DB_PASSWORD != 'None' else ""
    
    # Menggabungkannya menjadi SQLAlchemy URI yang valid
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}{password_str}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False





# import os
# from dotenv import load_dotenv, find_dotenv
# import sys

# # Memastikan file .env ditemukan dan dimuat secara akurat
# load_dotenv(find_dotenv())

# # Menentukan lokasi root folder (agar file database.db berada tepat di sebelah file .exe)
# if getattr(sys, 'frozen', False):
#     # Jika dijalankan sebagai file .exe dari PyInstaller
#     BASE_DIR = os.path.dirname(sys.executable)
# else:
#     # Jika dijalankan sebagai script Python biasa
#     BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# class Config:
#     SECRET_KEY = os.getenv('SECRET_KEY') or 'haisen-photobooth-secret-key-2024'
    
#     # ----------------------------------------------------------------
#     # KODE LAMA (MySQL) - Dikomentari agar tidak hilang jika ingin dikembalikan
#     # ----------------------------------------------------------------
#     # DB_USER = os.getenv('DB_USER') or 'root'
#     # DB_PASSWORD = os.getenv('DB_PASSWORD')
#     # DB_HOST = os.getenv('DB_HOST') or 'localhost'
#     # DB_PORT = os.getenv('DB_PORT') or '3306'
#     # DB_NAME = os.getenv('DB_NAME') or 'photobooth_db'
#     # password_str = f":{DB_PASSWORD}" if DB_PASSWORD and DB_PASSWORD != 'None' else ""
#     # SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}{password_str}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
#     # ----------------------------------------------------------------
#     # KODE BARU (SQLite)
#     # ----------------------------------------------------------------
#     # Nama file database adalah 'photobooth_db.sqlite'
#     # File ini akan terbuat otomatis di sebelah file run.exe
#     SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'photobooth_db.sqlite')
    
#     SQLALCHEMY_TRACK_MODIFICATIONS = False