pyinstaller --onefile --add-data "app;app" --hidden-import engineio.async_drivers.threading --hidden-import engineio.async_drivers.eventlet run.py




bidict==0.24.1
blinker==1.9.0
certifi==2026.7.22
cffi==2.1.1
charset-normalizer==3.5.1
click==8.5.0
cryptography==50.0.1
Flask==3.0.2
Flask-Login==0.6.3
Flask-SocketIO==5.3.6
Flask-SQLAlchemy==3.1.1
google-api-core==2.38.0
google-api-python-client==2.118.0
google-auth==2.58.0
google-auth-httplib2==0.4.2
google-auth-oauthlib==1.2.0
googleapis-common-protos==1.75.3
greenlet==3.5.6
h11==0.16.0
httplib2==0.32.0
idna==3.20
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.3
numpy==2.5.3
oauthlib==3.3.1
opencv-python==5.0.0.93
opentelemetry-api==1.44.0
pillow==12.3.0
proto-plus==1.28.4
protobuf==7.36.2
pyasn1==0.6.4
pyasn1_modules==0.4.2
pycparser==3.0
PyMySQL==1.1.0
pyparsing==3.3.3
python-dotenv==1.0.1
python-engineio==4.14.0
python-socketio==5.17.0
requests==2.34.2
requests-oauthlib==2.0.0
simple-websocket==1.1.0
SQLAlchemy==2.0.54
typing_extensions==4.16.0
uritemplate==4.2.0
urllib3==2.8.0
Werkzeug==3.1.8
wsproto==1.3.2



pip uninstall eventlet
perlu instalasi pip install eventlet atau pip install gevent gevent-websocket