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
echo   [1/4] Memeriksa status XAMPP (MySQL + Apache)...

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
"%XAMPP_DIR%\mysql\bin\mysqld.exe" --standalone --console >nul 2>&1 &

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
    goto :START_VENV
)

echo         [*] Database '%DB_NAME%' belum ada. Membuat database baru...

"%MYSQL_BIN%" %MYSQL_ARGS% -e ^
"CREATE DATABASE IF NOT EXISTS %DB_NAME% CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; ^
USE %DB_NAME%; ^
CREATE TABLE IF NOT EXISTS admin_users ( ^
    id INT AUTO_INCREMENT PRIMARY KEY, ^
    username VARCHAR(80) NOT NULL UNIQUE, ^
    password_hash VARCHAR(256) NOT NULL, ^
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP ^
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; ^
CREATE TABLE IF NOT EXISTS app_settings ( ^
    id INT AUTO_INCREMENT PRIMARY KEY, ^
    key VARCHAR(100) NOT NULL UNIQUE, ^
    value TEXT, ^
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP ^
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; ^
CREATE TABLE IF NOT EXISTS photo_sessions ( ^
    id INT AUTO_INCREMENT PRIMARY KEY, ^
    unique_code VARCHAR(16) NOT NULL UNIQUE, ^
    template_name VARCHAR(120), ^
    collage_path VARCHAR(512), ^
    raw_photos_json TEXT, ^
    gif_path VARCHAR(512), ^
    completed TINYINT(1) DEFAULT 0, ^
    completed_at DATETIME, ^
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP ^
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;" 2>NUL

if "%ERRORLEVEL%"=="0" (
    echo         [OK] Database '%DB_NAME%' dan tabel berhasil dibuat!
) else (
    echo         [WARN] Gagal membuat database. Cek koneksi MySQL.
)

REM ─────────────────────────────────────────────────────────────────
REM  STEP 2.5: JALANKAN CLOUDFLARE TUNNEL (Terminal Terpisah)
REM ─────────────────────────────────────────────────────────────────
echo.
echo   [2.5/4] Menjalankan Cloudflare Tunnel...

where cloudflared >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    start "Cloudflare Tunnel" cmd /k "title Cloudflare Tunnel - photobooth.mysens.icu && color 0B && echo. && echo  [CLOUDFLARE TUNNEL] Menghubungkan ke photobooth.mysens.icu... && echo. && cloudflared tunnel run"
    echo         [OK] Cloudflare Tunnel berjalan di terminal terpisah.
    timeout /t 2 /nobreak >nul
) else (
    set CF_EXE=
    if exist "C:\Program Files\cloudflared\cloudflared.exe"       set CF_EXE=C:\Program Files\cloudflared\cloudflared.exe
    if exist "C:\cloudflared\cloudflared.exe"                     set CF_EXE=C:\cloudflared\cloudflared.exe
    if exist "%USERPROFILE%\.cloudflared\cloudflared.exe"         set CF_EXE=%USERPROFILE%\.cloudflared\cloudflared.exe
    if exist "%~dp0cloudflared.exe"                               set CF_EXE=%~dp0cloudflared.exe

    if not "%CF_EXE%"=="" (
        start "Cloudflare Tunnel" cmd /k "title Cloudflare Tunnel - photobooth.mysens.icu && color 0B && echo. && echo  [CLOUDFLARE TUNNEL] Menghubungkan ke photobooth.mysens.icu... && echo. && \"%CF_EXE%\" tunnel run"
        echo         [OK] Cloudflare Tunnel berjalan di terminal terpisah.
        timeout /t 2 /nobreak >nul
    ) else (
        echo         [WARN] cloudflared tidak ditemukan. Tunnel tidak dijalankan.
        echo                Install: https://developers.cloudflare.com/cloudflared/install
    )
)

REM ─────────────────────────────────────────────────────────────────
REM  STEP 3: AKTIFKAN VENV DAN JALANKAN SERVER FLASK
REM ─────────────────────────────────────────────────────────────────
:START_VENV
echo.
echo   [3/4] Mengaktifkan Virtual Environment dan menjalankan server...
echo.
echo  ------------------------------------------------------------------------------------------
echo   [!] ENDPOINTS SISTEM:
echo       - KIOSK BOOTH     : http://localhost:5000   ^|  http://127.0.0.1:5000
echo       - ADMIN PANEL     : http://localhost:5000/admin
echo       - CREDENTIALS     : admin / haisen2024
echo       - DOMAIN PUBLIK   : https://photobooth.mysens.icu
echo  ------------------------------------------------------------------------------------------
echo   [!] Tekan CTRL+C untuk mematikan server
echo  ------------------------------------------------------------------------------------------
echo.

call venv\Scripts\activate

REM ─────────────────────────────────────────────────────────────────
REM  STEP 4: BUKA CHROME KE DOMAIN + FULLSCREEN F11 (TANPA TAB)
REM ─────────────────────────────────────────────────────────────────
echo   [4/4] Membuka Chrome ke http://localhost:5000 ...

REM Tunggu server sedikit agar flask siap
timeout /t 3 /nobreak >nul

REM Cari instalasi Chrome
set "CHROME_EXE="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe"      set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe"      set "CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"

if "%CHROME_EXE%"=="" goto CHROME_NOT_FOUND

REM Jika Chrome Ditemukan:
REM Menggunakan parameter --app (menghilangkan tab & address bar) 
REM ditambah --start-fullscreen (otomatis menekan F11)
start "" "%CHROME_EXE%" --app="http://localhost:5000" --start-fullscreen
echo         [OK] Chrome dibuka dalam mode Layar Penuh (F11) tanpa Tab.
goto CHROME_DONE

:CHROME_NOT_FOUND
echo         [WARN] Google Chrome tidak ditemukan. Buka browser manual.
start "" "http://localhost:5000"

:CHROME_DONE
echo.
python run.py

echo.
echo  ==========================================================================================
echo   [!] SERVER BERHENTI DENGAN AMAN. Tekan sembarang tombol untuk keluar.
echo  ==========================================================================================
pause