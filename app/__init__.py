import os
import pymysql
from flask import Flask
from config import Config
from extensions import db, socketio, login_manager
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def create_database_if_not_exists():
    """Membuat database MySQL secara otomatis jika belum ada di XAMPP"""
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD')
    if password == 'None' or not password:
        password = ''

    host = os.getenv('DB_HOST', 'localhost')
    if host == 'None':
        host = 'localhost'

    port_env = os.getenv('DB_PORT', '3306')
    port = int(port_env) if port_env and port_env.isdigit() else 3306

    dbname = os.getenv('DB_NAME', 'photobooth_db')
    if dbname == 'None':
        dbname = 'photobooth_db'

    connection = pymysql.connect(host=host, user=user, password=password, port=port)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        connection.commit()
    finally:
        connection.close()


def create_app(config_class=Config):
    try:
        create_database_if_not_exists()
    except Exception as e:
        print(f"Info/Peringatan Koneksi MySQL: {e}")

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inisialisasi Ekstensi
    db.init_app(app)
    socketio.init_app(app)

    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'admin_auth.login'
    login_manager.login_message = 'Silakan login terlebih dahulu.'
    login_manager.login_message_category = 'error'

    from app.models.admin_model import AdminUser

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))

    # ==========================================
    # PENDAFTARAN SEMUA BLUEPRINT APLIKASI
    # ==========================================
    from app.blueprints.host.routes import host_bp
    from app.blueprints.mobile.routes import mobile_bp
    from app.blueprints.api.controllers import api_bp
    from app.blueprints.gallery.routes import gallery_bp
    from app.blueprints.admin.routes import admin_bp
    from app.blueprints.admin.auth import auth_bp
    from app.blueprints.bilboard.routes import bilboard_bp

    app.register_blueprint(host_bp)
    app.register_blueprint(mobile_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(bilboard_bp, url_prefix='/bilboard')

    # ==========================================
    # SECURITY FILTER & BLOCKED ROUTES HANDLER
    # ==========================================
    from flask import render_template, request, abort

    DANGEROUS_PATTERNS = [
        'phpmyadmin', 'pma', 'adminer', 'wp-admin', 'wp-login', '.env', '.git',
        '.sql', 'config.php', 'shell', 'backup', 'eval-stdin', 'cgi-bin',
        'xmlrpc', 'actuator', 'setup.php', 'composer.json', 'vendor',
        'console', 'solr', 'boaform', 'autodiscover'
    ]

    @app.before_request
    def block_dangerous_requests():
        path = request.path.lower()
        # Blokir file tersembunyi seperti /.env, /.git, dll
        if '/.' in path:
            return render_template('errors/error.html',
                                   error_code='403',
                                   title='Akses Ditolak & Diblokir',
                                   message='Akses ke file atau direktori sistem tersembunyi dilarang.'), 403

        for pattern in DANGEROUS_PATTERNS:
            if pattern in path:
                return render_template('errors/error.html',
                                       error_code='403',
                                       title='Akses Ditolak & Diblokir',
                                       message='Aktivitas berbahaya atau probing path yang mencurigakan terdeteksi dan diblokir oleh firewall sistem photobooth.'), 403

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    @app.errorhandler(404)
    def handle_not_found(e):
        return render_template('errors/error.html',
                               error_code='404',
                               title='Halaman Tidak Ditemukan',
                               message='Tautan URL yang Anda tuju tidak terdaftar di sistem. Silakan periksa ejaan atau kembali ke menu photobooth.'), 404

    @app.errorhandler(403)
    def handle_forbidden(e):
        return render_template('errors/error.html',
                               error_code='403',
                               title='Akses Terlarang (Forbidden)',
                               message='Anda tidak memiliki hak akses atau izin untuk membuka direktori atau endpoint ini.'), 403

    @app.errorhandler(500)
    def handle_server_error(e):
        return render_template('errors/error.html',
                               error_code='500',
                               title='Kesalahan Server Internal',
                               message='Terjadi kendala pada sistem server saat memproses permintaan Anda.'), 500

    # Buat tabel database + seed admin default
    with app.app_context():
        db.create_all()
        _seed_admin(app)


    return app


def _seed_admin(app):
    """Buat akun admin default jika belum ada."""
    from app.models.admin_model import AdminUser
    if AdminUser.query.count() == 0:
        admin = AdminUser(username='admin')
        admin.set_password('haisen2024')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin default dibuat: admin / haisen2024")
