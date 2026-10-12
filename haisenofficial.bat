@REM @echo off
@REM title HAISEN OFFICIAL PHOTOBOOTH v2.0 [PRODUCTION ENGINE]
@REM color 0A
@REM mode con: cols=90 lines=38
@REM cd /d "%~dp0"
@REM cls

@REM echo.
@REM echo  ==========================================================================================
@REM echo    _    _          _____  _____ ______ _   _   _____ _______ _    _ _____ _____ ____
@REM echo   ^| ^|  ^| ^|   /\   ^|_   _^|/ ____^|  ____^| \ ^| ^| / ____^|__   __^| ^|  ^| ^|  __ \_   _/ __ \
@REM echo   ^| ^|__^| ^|  /  \    ^| ^| ^| (___ ^| ^|__  ^|  \^| ^|^| (___    ^| ^|  ^| ^|  ^| ^| ^|  ^| ^|^| ^|^| ^|  ^| ^|
@REM echo   ^|  __  ^| / /\ \   ^| ^|  \___ \^|  __^| ^| . ` ^| \___ \   ^| ^|  ^| ^|  ^| ^| ^|  ^| ^|^| ^|^| ^|  ^| ^|
@REM echo   ^| ^|  ^| ^|/ ____ \ _^| ^|_ ____) ^| ^|____^| ^|\  ^| ____) ^|  ^| ^|  ^| ^|__^| ^| ^|__^| _^| ^|_^| ^|__^| ^|
@REM echo   ^|_^|  ^|_/_/    \_\_____^|_____/^|______^|_^| \_^|^|_____/   ^|_^|   \______/^|_____(_)_____^|____/
@REM echo  ==========================================================================================
@REM echo                                SELF-PHOTO STUDIO ENGINE v2.0
@REM echo  ==========================================================================================
@REM echo.

@REM REM ─────────────────────────────────────────────────────────────────
@REM REM  STEP 1: CEK DAN JALANKAN XAMPP (MySQL + Apache)
@REM REM ─────────────────────────────────────────────────────────────────
@REM echo   [1/4] Memeriksa status XAMPP (MySQL + Apache)...

@REM tasklist /FI "IMAGENAME eq mysqld.exe" 2>NUL | find /I "mysqld.exe" >NUL
@REM if "%ERRORLEVEL%"=="0" (
@REM     echo         [OK] MySQL sudah berjalan. Skip start XAMPP.
@REM     goto :CHECK_DB
@REM )

@REM set XAMPP_DIR=
@REM if exist "C:\xampp\xampp-control.exe"       set XAMPP_DIR=C:\xampp
@REM if exist "C:\XAMPP\xampp-control.exe"       set XAMPP_DIR=C:\XAMPP
@REM if exist "D:\xampp\xampp-control.exe"       set XAMPP_DIR=D:\xampp
@REM if exist "D:\XAMPP\xampp-control.exe"       set XAMPP_DIR=D:\XAMPP
@REM if exist "E:\xampp\xampp-control.exe"       set XAMPP_DIR=E:\xampp

@REM if "%XAMPP_DIR%"=="" (
@REM     echo         [WARN] XAMPP tidak ditemukan! Pastikan XAMPP terinstall.
@REM     echo         Tekan sembarang tombol untuk lanjut tanpa XAMPP...
@REM     pause > nul
@REM     goto :CHECK_DB
@REM )

@REM echo         [*] Memulai MySQL via XAMPP di %XAMPP_DIR%...
@REM "%XAMPP_DIR%\mysql\bin\mysqld.exe" --standalone --console >nul 2>&1 &

@REM set /a RETRY=0
@REM :WAIT_MYSQL
@REM timeout /t 2 /nobreak >nul
@REM tasklist /FI "IMAGENAME eq mysqld.exe" 2>NUL | find /I "mysqld.exe" >NUL
@REM if "%ERRORLEVEL%"=="0" goto :MYSQL_READY
@REM set /a RETRY+=1
@REM if %RETRY% lss 10 goto :WAIT_MYSQL
@REM echo         [WARN] MySQL belum siap setelah 20 detik, lanjut saja...
@REM goto :CHECK_DB

@REM :MYSQL_READY
@REM echo         [OK] MySQL berhasil dinyalakan.

@REM REM ─────────────────────────────────────────────────────────────────
@REM REM  STEP 2: CEK DAN BUAT DATABASE JIKA BELUM ADA
@REM REM ─────────────────────────────────────────────────────────────────
@REM :CHECK_DB
@REM echo.
@REM echo   [2/4] Memeriksa database photobooth_db...

@REM set MYSQL_BIN=
@REM if exist "C:\xampp\mysql\bin\mysql.exe"  set MYSQL_BIN=C:\xampp\mysql\bin\mysql.exe
@REM if exist "C:\XAMPP\mysql\bin\mysql.exe"  set MYSQL_BIN=C:\XAMPP\mysql\bin\mysql.exe
@REM if exist "D:\xampp\mysql\bin\mysql.exe"  set MYSQL_BIN=D:\xampp\mysql\bin\mysql.exe
@REM if exist "D:\XAMPP\mysql\bin\mysql.exe"  set MYSQL_BIN=D:\XAMPP\mysql\bin\mysql.exe
@REM if exist "E:\xampp\mysql\bin\mysql.exe"  set MYSQL_BIN=E:\xampp\mysql\bin\mysql.exe

@REM if "%MYSQL_BIN%"=="" (
@REM     echo         [SKIP] mysql.exe tidak ditemukan. Lewati cek database.
@REM     goto :START_VENV
@REM )

@REM set DB_USER=root
@REM set DB_PASS=
@REM set DB_NAME=photobooth_db
@REM set DB_HOST=localhost
@REM set DB_PORT=3306

@REM if exist ".env" (
@REM     for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
@REM         if "%%a"=="DB_USER"     set DB_USER=%%b
@REM         if "%%a"=="DB_PASSWORD" set DB_PASS=%%b
@REM         if "%%a"=="DB_NAME"     set DB_NAME=%%b
@REM         if "%%a"=="DB_HOST"     set DB_HOST=%%b
@REM         if "%%a"=="DB_PORT"     set DB_PORT=%%b
@REM     )
@REM )

@REM set MYSQL_ARGS=-u%DB_USER% -h%DB_HOST% -P%DB_PORT% --connect-timeout=5
@REM if not "%DB_PASS%"=="" set MYSQL_ARGS=%MYSQL_ARGS% -p%DB_PASS%

@REM "%MYSQL_BIN%" %MYSQL_ARGS% -e "USE %DB_NAME%;" 2>NUL
@REM if "%ERRORLEVEL%"=="0" (
@REM     echo         [OK] Database '%DB_NAME%' sudah ada.
@REM     goto :START_VENV
@REM )

@REM echo         [*] Database '%DB_NAME%' belum ada. Membuat database baru...

@REM "%MYSQL_BIN%" %MYSQL_ARGS% -e ^
@REM "CREATE DATABASE IF NOT EXISTS %DB_NAME% CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; ^
@REM USE %DB_NAME%; ^
@REM CREATE TABLE IF NOT EXISTS admin_users ( ^
@REM     id INT AUTO_INCREMENT PRIMARY KEY, ^
@REM     username VARCHAR(80) NOT NULL UNIQUE, ^
@REM     password_hash VARCHAR(256) NOT NULL, ^
@REM     created_at DATETIME DEFAULT CURRENT_TIMESTAMP ^
@REM ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; ^
@REM CREATE TABLE IF NOT EXISTS app_settings ( ^
@REM     id INT AUTO_INCREMENT PRIMARY KEY, ^
@REM     key VARCHAR(100) NOT NULL UNIQUE, ^
@REM     value TEXT, ^
@REM     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP ^
@REM ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; ^
@REM CREATE TABLE IF NOT EXISTS photo_sessions ( ^
@REM     id INT AUTO_INCREMENT PRIMARY KEY, ^
@REM     unique_code VARCHAR(16) NOT NULL UNIQUE, ^
@REM     template_name VARCHAR(120), ^
@REM     collage_path VARCHAR(512), ^
@REM     raw_photos_json TEXT, ^
@REM     gif_path VARCHAR(512), ^
@REM     completed TINYINT(1) DEFAULT 0, ^
@REM     completed_at DATETIME, ^
@REM     created_at DATETIME DEFAULT CURRENT_TIMESTAMP ^
@REM ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;" 2>NUL

@REM if "%ERRORLEVEL%"=="0" (
@REM     echo         [OK] Database '%DB_NAME%' dan tabel berhasil dibuat!
@REM ) else (
@REM     echo         [WARN] Gagal membuat database. Cek koneksi MySQL.
@REM )

@REM REM ─────────────────────────────────────────────────────────────────
@REM REM  STEP 2.5: JALANKAN CLOUDFLARE TUNNEL (Terminal Terpisah)
@REM REM ─────────────────────────────────────────────────────────────────
@REM echo.
@REM echo   [2.5/4] Menjalankan Cloudflare Tunnel...

@REM where cloudflared >nul 2>&1
@REM if "%ERRORLEVEL%"=="0" (
@REM     start "Cloudflare Tunnel" cmd /k "title Cloudflare Tunnel - api.haisen.my.id && color 0B && echo. && echo  [CLOUDFLARE TUNNEL] Menghubungkan ke api.haisen.my.id... && echo. && cloudflared tunnel run"
@REM     echo         [OK] Cloudflare Tunnel berjalan di terminal terpisah.
@REM     timeout /t 2 /nobreak >nul
@REM ) else (
@REM     set CF_EXE=
@REM     if exist "C:\Program Files\cloudflared\cloudflared.exe"       set CF_EXE=C:\Program Files\cloudflared\cloudflared.exe
@REM     if exist "C:\cloudflared\cloudflared.exe"                     set CF_EXE=C:\cloudflared\cloudflared.exe
@REM     if exist "%USERPROFILE%\.cloudflared\cloudflared.exe"         set CF_EXE=%USERPROFILE%\.cloudflared\cloudflared.exe
@REM     if exist "%~dp0cloudflared.exe"                               set CF_EXE=%~dp0cloudflared.exe

@REM     if not "%CF_EXE%"=="" (
@REM         start "Cloudflare Tunnel" cmd /k "title Cloudflare Tunnel - api.haisen.my.id && color 0B && echo. && echo  [CLOUDFLARE TUNNEL] Menghubungkan ke api.haisen.my.id... && echo. && \"%CF_EXE%\" tunnel run"
@REM         echo         [OK] Cloudflare Tunnel berjalan di terminal terpisah.
@REM         timeout /t 2 /nobreak >nul
@REM     ) else (
@REM         echo         [WARN] cloudflared tidak ditemukan. Tunnel tidak dijalankan.
@REM         echo                Install: https://developers.cloudflare.com/cloudflared/install
@REM     )
@REM )

@REM REM ─────────────────────────────────────────────────────────────────
@REM REM  STEP 3: AKTIFKAN VENV DAN JALANKAN SERVER FLASK
@REM REM ─────────────────────────────────────────────────────────────────
@REM :START_VENV
@REM echo.
@REM echo   [3/4] Mengaktifkan Virtual Environment dan menjalankan server...
@REM echo.
@REM echo  ------------------------------------------------------------------------------------------
@REM echo   [!] ENDPOINTS SISTEM:
@REM echo       - KIOSK BOOTH     : http://localhost:5000   ^|  http://127.0.0.1:5000
@REM echo       - ADMIN PANEL     : http://localhost:5000/admin
@REM echo       - CREDENTIALS     : admin / haisen2024
@REM echo       - DOMAIN PUBLIK   : https://api.haisen.my.id
@REM echo  ------------------------------------------------------------------------------------------
@REM echo   [!] Tekan CTRL+C untuk mematikan server
@REM echo  ------------------------------------------------------------------------------------------
@REM echo.

@REM call venv\Scripts\activate

@REM REM ─────────────────────────────────────────────────────────────────
@REM REM  STEP 4: BUKA CHROME KE DOMAIN + FULLSCREEN F11 (TANPA TAB)
@REM REM ─────────────────────────────────────────────────────────────────
@REM echo   [4/4] Membuka Chrome ke http://localhost:5000 ...

@REM REM Tunggu server sedikit agar flask siap
@REM timeout /t 3 /nobreak >nul

@REM REM Cari instalasi Chrome
@REM set "CHROME_EXE="
@REM if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe"      set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
@REM if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
@REM if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe"      set "CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"

@REM if "%CHROME_EXE%"=="" goto CHROME_NOT_FOUND

@REM REM Jika Chrome Ditemukan:
@REM REM Menggunakan parameter --app (menghilangkan tab & address bar) 
@REM REM ditambah --start-fullscreen (otomatis menekan F11)
@REM start "" "%CHROME_EXE%" --app="http://localhost:5000" --start-fullscreen
@REM echo         [OK] Chrome dibuka dalam mode Layar Penuh (F11) tanpa Tab.
@REM goto CHROME_DONE

@REM :CHROME_NOT_FOUND
@REM echo         [WARN] Google Chrome tidak ditemukan. Buka browser manual.
@REM start "" "http://localhost:5000"

@REM :CHROME_DONE
@REM echo.
@REM python run.py

@REM echo.
@REM echo  ==========================================================================================
@REM echo   [!] SERVER BERHENTI DENGAN AMAN. Tekan sembarang tombol untuk keluar.
@REM echo  ==========================================================================================
@REM pause


@echo off
title HAISEN OFFICIAL PHOTOBOOTH v2.0 [PRODUCTION ENGINE]
color 0A
mode con: cols=90 lines=38
cd /d "%~dp0"
cls

echo.
echo  ==========================================================================================
echo    _    _          _____  _____ ______ _   _   _____ _______ _    _ _____ _____ ____
echo   ^| ^|  ^| ^|   /\   ^|_   _^|/ ____^|  ____^| \ ^| ^| / ____^|__   __^| ^|  ^| ^|  __ \_   _/ __ \
echo   ^| ^|__^| ^|  /  \    ^| ^| ^| (___ ^| ^|__  ^|  \^| ^|^| (___    ^| ^|  ^| ^|  ^| ^| ^|  ^| ^|^| ^|^| ^|  ^| ^|
echo   ^|  __  ^| / /\ \   ^| ^|  \___ \^|  __^| ^| . ` ^| \___ \   ^| ^|  ^| ^|  ^| ^| ^|  ^| ^|^| ^|^| ^|  ^| ^|
echo   ^| ^|  ^| ^|/ ____ \ _^| ^|_ ____) ^| ^|____^| ^|\  ^| ____) ^|  ^| ^|  ^| ^|__^| ^| ^|__^| _^| ^|_^| ^|__^| ^|
echo   ^|_^|  ^|_/_/    \_\_____^|_____/^|______^|_^| \_^|^|_____/   ^|_^|   \______/^|_____(_)_____^|____/
echo  ==========================================================================================
echo                                SELF-PHOTO STUDIO ENGINE v2.0
echo  ==========================================================================================
echo.

REM ─────────────────────────────────────────────────────────────────
REM  STEP 1: CEK DAN JALANKAN XAMPP (MySQL + Apache)
REM ─────────────────────────────────────────────────────────────────
echo   [1/4] Memeriksa status XAMPP (MySQL)...

tasklist /FI "IMAGENAME eq mysqld.exe" 2>NUL | find /I "mysqld.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo         [OK] MySQL sudah berjalan. Skip start XAMPP.
    goto :CHECK_DB
)

set XAMPP_DIR=
if exist "C:\xampp\xampp-control.exe"       set XAMPP_DIR=C:\xampp
if exist "C:\XAMPP\xampp-control.exe"       set XAMPP_DIR=C:\XAMPP
if exist "D:\xampp\xampp-control.exe"       set XAMPP_DIR=D:\xampp
if exist "D:\XAMPP\xampp-control.exe"       set XAMPP_DIR=D:\XAMPP
if exist "E:\xampp\xampp-control.exe"       set XAMPP_DIR=E:\xampp

if "%XAMPP_DIR%"=="" (
    echo         [WARN] XAMPP tidak ditemukan! Pastikan XAMPP terinstall.
    echo         Tekan sembarang tombol untuk lanjut tanpa XAMPP...
    pause > nul
    goto :CHECK_DB
)

echo         [*] Memulai MySQL via XAMPP di %XAMPP_DIR%...
REM [PERBAIKAN] Gunakan start /B agar proses tidak macet/nyangkut di sini
start /B "" "%XAMPP_DIR%\mysql\bin\mysqld.exe" --standalone --console >nul 2>&1

set /a RETRY=0
:WAIT_MYSQL
timeout /t 2 /nobreak >nul
tasklist /FI "IMAGENAME eq mysqld.exe" 2>NUL | find /I "mysqld.exe" >NUL
if "%ERRORLEVEL%"=="0" goto :MYSQL_READY
set /a RETRY+=1
if %RETRY% lss 10 goto :WAIT_MYSQL
echo         [WARN] MySQL belum siap setelah 20 detik, lanjut saja...
goto :CHECK_DB

:MYSQL_READY
echo         [OK] MySQL berhasil dinyalakan.

REM ─────────────────────────────────────────────────────────────────
REM  STEP 2: CEK DAN BUAT DATABASE JIKA BELUM ADA
REM ─────────────────────────────────────────────────────────────────
:CHECK_DB
echo.
echo   [2/4] Memeriksa database photobooth_db...

set MYSQL_BIN=
if exist "C:\xampp\mysql\bin\mysql.exe"  set MYSQL_BIN=C:\xampp\mysql\bin\mysql.exe
if exist "C:\XAMPP\mysql\bin\mysql.exe"  set MYSQL_BIN=C:\XAMPP\mysql\bin\mysql.exe
if exist "D:\xampp\mysql\bin\mysql.exe"  set MYSQL_BIN=D:\xampp\mysql\bin\mysql.exe
if exist "D:\XAMPP\mysql\bin\mysql.exe"  set MYSQL_BIN=D:\XAMPP\mysql\bin\mysql.exe
if exist "E:\xampp\mysql\bin\mysql.exe"  set MYSQL_BIN=E:\xampp\mysql\bin\mysql.exe

if "%MYSQL_BIN%"=="" (
    echo         [SKIP] mysql.exe tidak ditemukan. Lewati cek database.
    goto :START_VENV
)

set DB_USER=root
set DB_PASS=
set DB_NAME=photobooth_db
set DB_HOST=localhost
set DB_PORT=3306

if exist ".env" (
    for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
        if "%%a"=="DB_USER"     set DB_USER=%%b
        if "%%a"=="DB_PASSWORD" set DB_PASS=%%b
        if "%%a"=="DB_NAME"     set DB_NAME=%%b
        if "%%a"=="DB_HOST"     set DB_HOST=%%b
        if "%%a"=="DB_PORT"     set DB_PORT=%%b
    )
)

set MYSQL_ARGS=-u%DB_USER% -h%DB_HOST% -P%DB_PORT% --connect-timeout=5
if not "%DB_PASS%"=="" set MYSQL_ARGS=%MYSQL_ARGS% -p%DB_PASS%

"%MYSQL_BIN%" %MYSQL_ARGS% -e "USE %DB_NAME%;" 2>NUL
if "%ERRORLEVEL%"=="0" (
    echo         [OK] Database '%DB_NAME%' sudah ada.
    goto :START_TUNNEL
)

echo         [*] Database '%DB_NAME%' belum ada. Membuat database baru...

REM [PERBAIKAN] Tulis ke file temporer agar syntax aman dan rapi
echo CREATE DATABASE IF NOT EXISTS %DB_NAME% CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; > temp_db.sql
echo USE %DB_NAME%; >> temp_db.sql
echo CREATE TABLE IF NOT EXISTS admin_users ( id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(80) NOT NULL UNIQUE, password_hash VARCHAR(256) NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; >> temp_db.sql
echo CREATE TABLE IF NOT EXISTS app_settings ( id INT AUTO_INCREMENT PRIMARY KEY, key_name VARCHAR(100) NOT NULL UNIQUE, value TEXT, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; >> temp_db.sql
echo CREATE TABLE IF NOT EXISTS photo_sessions ( id INT AUTO_INCREMENT PRIMARY KEY, unique_code VARCHAR(16) NOT NULL UNIQUE, template_name VARCHAR(120), collage_path VARCHAR(512), raw_photos_json TEXT, gif_path VARCHAR(512), completed TINYINT(1) DEFAULT 0, completed_at DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; >> temp_db.sql

"%MYSQL_BIN%" %MYSQL_ARGS% < temp_db.sql 2>NUL

if "%ERRORLEVEL%"=="0" (
    echo         [OK] Database '%DB_NAME%' dan tabel berhasil dibuat!
) else (
    echo         [WARN] Gagal membuat database. Cek koneksi MySQL.
)
del temp_db.sql >nul 2>&1

REM ─────────────────────────────────────────────────────────────────
REM  STEP 2.5: JALANKAN CLOUDFLARE TUNNEL (Terminal Terpisah)
REM ─────────────────────────────────────────────────────────────────
:START_TUNNEL
echo.
echo   [2.5/4] Menjalankan Cloudflare Tunnel...

where cloudflared >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    start "Cloudflare Tunnel" cmd /k "title Cloudflare Tunnel - api.haisen.my.id && color 0B && echo. && echo  [CLOUDFLARE TUNNEL] Menghubungkan ke api.haisen.my.id... && echo. && cloudflared tunnel run"
    echo         [OK] Cloudflare Tunnel berjalan di terminal terpisah.
    timeout /t 2 /nobreak >nul
) else (
    set CF_EXE=
    if exist "C:\Program Files\cloudflared\cloudflared.exe"       set CF_EXE=C:\Program Files\cloudflared\cloudflared.exe
    if exist "C:\cloudflared\cloudflared.exe"                     set CF_EXE=C:\cloudflared\cloudflared.exe
    if exist "%USERPROFILE%\.cloudflared\cloudflared.exe"         set CF_EXE=%USERPROFILE%\.cloudflared\cloudflared.exe
    if exist "%~dp0cloudflared.exe"                               set CF_EXE=%~dp0cloudflared.exe

    if not "%CF_EXE%"=="" (
        start "Cloudflare Tunnel" cmd /k "title Cloudflare Tunnel - api.haisen.my.id && color 0B && echo. && echo  [CLOUDFLARE TUNNEL] Menghubungkan ke api.haisen.my.id... && echo. && \"%CF_EXE%\" tunnel run"
        echo         [OK] Cloudflare Tunnel berjalan di terminal terpisah.
        timeout /t 2 /nobreak >nul
    ) else (
        echo         [WARN] cloudflared tidak ditemukan. Tunnel tidak dijalankan.
    )
)

REM ─────────────────────────────────────────────────────────────────
REM  STEP 3: AKTIFKAN VENV DAN JALANKAN SERVER FLASK
REM ─────────────────────────────────────────────────────────────────
:START_VENV
echo.
echo   [3/4] Mengaktifkan Virtual Environment...
call venv\Scripts\activate
echo         [OK] VENV Aktif.

echo.
echo  ------------------------------------------------------------------------------------------
echo   [!] ENDPOINTS SISTEM:
echo       - KIOSK BOOTH     : http://localhost:5000   ^|  http://127.0.0.1:5000
echo       - ADMIN PANEL     : http://localhost:5000/admin
echo       - CREDENTIALS     : admin / haisen2024
echo       - DOMAIN PUBLIK   : https://api.haisen.my.id
echo  ------------------------------------------------------------------------------------------
echo   [!] Tekan CTRL+C di layar ini untuk mematikan server
echo  ------------------------------------------------------------------------------------------
echo.

REM ─────────────────────────────────────────────────────────────────
REM  STEP 4: PILIH ROUTE & BUKA CHROME (APP MODE + FULLFRAME)
REM ─────────────────────────────────────────────────────────────────
echo.
echo  ==========================================================================================
echo   [4/4] PILIH MODE TAMPILAN LAYAR PHOTOBOOTH
echo  ==========================================================================================
echo   [1] Tampilkan versi Localhost (http://localhost:5000)
echo   [2] Tampilkan pakai Domain Publik (https://api.haisen.my.id)
echo  ==========================================================================================
set /p ROUTE_PILIHAN="   Masukkan pilihan angka (1 atau 2) lalu tekan Enter: "

set "TARGET_URL=http://localhost:5000"
if "%ROUTE_PILIHAN%"=="2" set "TARGET_URL=https://api.haisen.my.id"

echo.
echo   [*] Menyiapkan Browser untuk %TARGET_URL% (terbuka otomatis dalam 4 detik)...

REM Cari instalasi Chrome
set "CHROME_EXE="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe"      set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe"      set "CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"

if "%CHROME_EXE%"=="" (
    echo         [WARN] Google Chrome tidak ditemukan. Buka %TARGET_URL% secara manual.
    goto START_PYTHON
)

REM Membuat script temporer untuk delay Chrome agar menghindari error kutip (quote escaping) pada CMD
echo @echo off > temp_chrome.bat
echo timeout /t 4 /nobreak ^>nul >> temp_chrome.bat
echo start "" "%CHROME_EXE%" --app="%TARGET_URL%" --start-fullscreen >> temp_chrome.bat
echo del temp_chrome.bat >> temp_chrome.bat

REM Menjalankan script temporer di background
start /B temp_chrome.bat
echo         [OK] Chrome Mode Aplikasi (Fullframe) berhasil di-trigger.

:START_PYTHON
echo.
echo   [*] Menjalankan Flask Application Engine...
python run.py

echo.
echo  ==========================================================================================
echo   [!] SERVER BERHENTI DENGAN AMAN. Tekan sembarang tombol untuk keluar.
echo  ==========================================================================================
pause