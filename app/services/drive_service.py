import os
import time
import socket
import threading
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. PERPANJANG TIMEOUT GLOBAL: Mencegah error 10054 karena upload terputus di internet lambat
socket.setdefaulttimeout(300.0)

# 2. SAMAKAN BASE DIR: Mundur 2 tingkat ke root folder project (seperti di CollageService)
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class GoogleDriveService:
    # 3. THREAD LOCK: Mengamankan file token dari kerusakan jika diakses bersamaan oleh banyak user
    _token_lock = threading.Lock()

    def __init__(self):
        # Arahkan ke root folder agar file kredensial selalu ditemukan
        self.client_secret_file = os.path.join(_BASE_DIR, 'client_secret.json')
        self.token_file = os.path.join(_BASE_DIR, 'token.json')
        
        self.folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')
        self.scopes = ['https://www.googleapis.com/auth/drive.file']

    def get_credentials(self):
        """Menangani proses login ke akun Google dengan aman (Thread-Safe)"""
        creds = None
        
        with self._token_lock:
            # Cek apakah sudah pernah login sebelumnya
            if os.path.exists(self.token_file):
                try:
                    creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
                except Exception as e:
                    print(f"[DriveService] Token rusak/invalid, akan meminta ulang. Error: {e}")
                    creds = None
            
            # Jika belum login / token kadaluarsa, minta login
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        print(f"[DriveService] Gagal refresh token, silakan hapus token.json: {e}")
                        return None
                else:
                    if not os.path.exists(self.client_secret_file):
                        print(f"[DriveService] Error Fatal: File {self.client_secret_file} tidak ditemukan!")
                        print("Pastikan Anda sudah meletakkan client_secret.json di root folder project Anda.")
                        return None
                    
                    # Membuka browser otomatis untuk meminta izin
                    flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, self.scopes)
                    creds = flow.run_local_server(port=0)
                
                # Simpan token baru agar tidak perlu login berulang kali
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                    
        return creds

    def upload_file(self, file_path, mime_type='image/jpeg'):
        """Mengunggah file ke Google Drive dengan fitur Resumable & Auto-Retry untuk internet lambat"""
        if not self.folder_id:
            print("[DriveService] Peringatan: GOOGLE_DRIVE_FOLDER_ID belum dikonfigurasi di file .env.")
            return None

        if not os.path.exists(file_path):
            print(f"[DriveService] Error: File yang akan diupload tidak ditemukan di {file_path}")
            return None

        try:
            creds = self.get_credentials()
            if not creds: 
                return None
            
            service = build('drive', 'v3', credentials=creds)

            file_name = os.path.basename(file_path)
            file_metadata = {
                'name': file_name,
                'parents': [self.folder_id]
            }
            
            # 4. RESUMABLE & CHUNK SIZE: Mengirim file per 1MB agar tidak time-out sekaligus
            media = MediaFileUpload(
                file_path, 
                mimetype=mime_type, 
                resumable=True, 
                chunksize=1024 * 1024 
            )
            
            request = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            )

            # 5. AUTO-RETRY LOGIC: Eksponensial Backoff untuk menangkal jaringan berkedip/putus sesaat
            MAX_RETRIES = 3
            for attempt in range(MAX_RETRIES):
                try:
                    file = request.execute()
                    return file.get('webViewLink')
                
                except Exception as e:
                    if attempt == MAX_RETRIES - 1:
                        print(f"[DriveService] Gagal permanen mengunggah {file_name} setelah {MAX_RETRIES} percobaan: {e}")
                        break
                    
                    print(f"[DriveService] Koneksi putus. Mencoba ulang upload {file_name}... ({attempt + 1}/{MAX_RETRIES})")
                    time.sleep(2 ** attempt) # Tidur sejenak: 1 detik, lalu 2 detik, lalu 4 detik
                    
            return None
        
        except Exception as e:
            print(f"[DriveService] Error sistem saat inisiasi Google Drive: {e}")
            return None