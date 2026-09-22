from extensions import db
from datetime import datetime


class PhotoSession(db.Model):
    __tablename__ = 'photo_sessions'

    id = db.Column(db.Integer, primary_key=True)
    unique_code = db.Column(db.String(4), unique=True, nullable=False)
    status = db.Column(db.String(20), default='waiting')  # waiting, connected, completed
    template_name = db.Column(db.String(100), nullable=True, default='default')
    collage_path = db.Column(db.String(500), nullable=True)
    gif_path = db.Column(db.String(500), nullable=True)
    raw_photos_json = db.Column(db.Text, nullable=True)   # JSON array of raw photo paths
    created_at = db.Column(db.DateTime, default=datetime.now)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Session {self.unique_code} - Status: {self.status}>'