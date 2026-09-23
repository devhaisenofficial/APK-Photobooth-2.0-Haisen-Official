from app import create_app
from extensions import socketio

app = create_app()

if __name__ == '__main__':
    # Menggunakan socketio.run agar mendukung fitur real-time web socket
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)




# from app import create_app
# from extensions import socketio, db

# app = create_app()

# with app.app_context():
#     db.create_all()

# if __name__ == '__main__':
#     # Menggunakan socketio.run agar mendukung fitur real-time web socket
#     socketio.run(app, host='0.0.0.0', port=5000, debug=True)