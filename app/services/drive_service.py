import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class GoogleDriveService:
    def __init__(self):
        # Path ke file credentials JSON Google Cloud Console (jika Anda sudah memilikinya)
        self.creds_file = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH', 'credentials.json')
        self.folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '') # ID Folder tujuan di Drive

    def upload_file(self, file_path, mime_type='image/jpeg'):
        """Mengunggah file lokal ke Google Drive"""
        if not os.path.exists(self.creds_file) or not self.folder_id:
            print("Peringatan: Kredensial Google Drive atau Folder ID belum dikonfigurasi. Lewati upload.")
            return None

        try:
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            creds = service_account.Credentials.from_service_account_file(
                self.creds_file, scopes=SCOPES
            )
            service = build('drive', 'v3', credentials=creds)

            file_name = os.path.basename(file_path)
            file_metadata = {
                'name': file_name,
                'parents': [self.folder_id]
            }
            
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()

            return file.get('webViewLink')
        
        except Exception as e:
            print(f"Error mengunggah ke Google Drive: {e}")
            return None