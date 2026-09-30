@echo off
rem Дракончик Тоору | Автор: Матиенко Антон Александрович | E-mail: Aspksa@yandex.ru
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "PYTHON_VERSION=3.14.7"
set "ARCHIVE=temp\python-%PYTHON_VERSION%-embeddable.zip"
set "TARGET=runtime\python"
set "STAGING=runtime\python.new"
set "PREVIOUS=runtime\python.previous"

if exist "%TARGET%\python.exe" (
    "%TARGET%\python.exe" -c "import sys; assert sys.version_info >= (3,10); import core.server" >nul 2>nul
    if not errorlevel 1 goto ready
    echo Обнаружен повреждённый или несовместимый portable Python. Будет выполнено восстановление.
)

where curl.exe >nul 2>nul
if errorlevel 1 (
    echo Не найден curl.exe. Нужен штатный curl Windows для HTTPS-загрузки.
    pause
    exit /b 1
)
where certutil.exe >nul 2>nul
if errorlevel 1 (
    echo Не найден certutil.exe. Невозможно проверить SHA-256.
    pause
    exit /b 1
)
where tar.exe >nul 2>nul
if errorlevel 1 (
    echo Не найден tar.exe. Невозможно распаковать ZIP штатными средствами.
    pause
    exit /b 1
)

set "TOORU_ARCH=%PROCESSOR_ARCHITECTURE%"
if defined PROCESSOR_ARCHITEW6432 set "TOORU_ARCH=%PROCESSOR_ARCHITEW6432%"

if /I "%TOORU_ARCH%"=="AMD64" (
    set "PYTHON_URL=https://www.python.org/ftp/python/3.14.7/python-3.14.7-embeddable-amd64.zip"
    set "PYTHON_SHA256=76c3c0384ab3f822486f32450f3a4d20f5d65ad0ec32ee34290971aa0eb817e6"
    goto download
)
if /I "%TOORU_ARCH%"=="ARM64" (
    set "PYTHON_URL=https://www.python.org/ftp/python/3.14.7/python-3.14.7-embeddable-arm64.zip"
    set "PYTHON_SHA256=b777fa08b68a177e350f8730c3e97a2b216d81e3eb5d183b039c65d43a6a2b3e"
    goto download
)
if /I "%TOORU_ARCH%"=="x86" (
    set "PYTHON_URL=https://www.python.org/ftp/python/3.14.7/python-3.14.7-embeddable-win32.zip"
    set "PYTHON_SHA256=c784a4596d706d647d430286e2db1d1e3dcc1acb8bc6993fabf147fc00606e18"
    goto download
)

echo Неподдерживаемая архитектура Windows: %TOORU_ARCH%
pause
exit /b 1

:download
if not exist "temp" mkdir "temp"
if not exist "runtime" mkdir "runtime"
if exist "%ARCHIVE%" del /q "%ARCHIVE%"

echo Загрузка официального Python %PYTHON_VERSION% для %TOORU_ARCH%...
curl.exe --fail --location --silent --show-error --retry 3 --retry-delay 2 --proto =https --tlsv1.2 --output "%ARCHIVE%" "%PYTHON_URL%"
if errorlevel 1 (
    echo Не удалось скачать Python с python.org.
    if exist "%ARCHIVE%" del /q "%ARCHIVE%"
    pause
    exit /b 1
)

echo Проверка SHA-256...
certutil.exe -hashfile "%ARCHIVE%" SHA256 | findstr /I /C:"%PYTHON_SHA256%" >nul
if errorlevel 1 (
    echo ОШИБКА: SHA-256 загруженного архива не совпадает с зафиксированным значением.
    del /q "%ARCHIVE%"
    pause
    exit /b 1
)

if exist "%STAGING%" rmdir /s /q "%STAGING%"
mkdir "%STAGING%"
if errorlevel 1 goto install_failed

tar.exe -xf "%ARCHIVE%" -C "%STAGING%"
if errorlevel 1 goto install_failed
if not exist "%STAGING%\python.exe" goto install_failed

set "PTH_FILE="
for %%F in ("%STAGING%\python*._pth") do (
    if exist "%%~fF" set "PTH_FILE=%%~fF"
)
if not defined PTH_FILE (
    echo Не найден файл python*._pth в официальном embeddable runtime.
    goto install_failed
)

>>"!PTH_FILE!" echo ..\..

(
    echo Дракончик Тоору
    echo Автор: Матиенко Антон Александрович
    echo E-mail: Aspksa@yandex.ru
    echo Python: %PYTHON_VERSION%
    echo Architecture: %TOORU_ARCH%
    echo Source: %PYTHON_URL%
    echo SHA-256: %PYTHON_SHA256%
) > "%STAGING%\TOORU_RUNTIME.txt"

"%STAGING%\python.exe" -c "import sys; assert sys.version_info[:2] == (3,14); import core.server; print(sys.version)"
if errorlevel 1 (
    echo Новый portable Python не прошёл проверку импорта ядра.
    goto install_failed
)

if exist "%PREVIOUS%" rmdir /s /q "%PREVIOUS%"
if exist "%TARGET%" (
    move "%TARGET%" "%PREVIOUS%" >nul
    if errorlevel 1 (
        echo Не удалось сохранить предыдущий runtime. Закройте работающий Tooru Core.
        goto install_failed
    )
)

move "%STAGING%" "%TARGET%" >nul
if errorlevel 1 (
    echo Не удалось активировать новый runtime.
    if exist "%PREVIOUS%" move "%PREVIOUS%" "%TARGET%" >nul
    goto install_failed
)

"%TARGET%\python.exe" -c "import sys; assert sys.version_info[:2] == (3,14); import core.server"
if errorlevel 1 (
    echo Активированный runtime не прошёл финальную проверку. Выполняется откат.
    rmdir /s /q "%TARGET%"
    if exist "%PREVIOUS%" move "%PREVIOUS%" "%TARGET%" >nul
    goto install_failed
)

if exist "%PREVIOUS%" rmdir /s /q "%PREVIOUS%"
if exist "%ARCHIVE%" del /q "%ARCHIVE%"

:ready
"%TARGET%\python.exe" --version
if errorlevel 1 exit /b 1
echo Portable Python готов. Запустите ДракончикТоору.bat.
pause
exit /b 0

:install_failed
if exist "%STAGING%" rmdir /s /q "%STAGING%"
if exist "%ARCHIVE%" del /q "%ARCHIVE%"
pause
exit /b 1
