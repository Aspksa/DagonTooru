@echo off
rem Дракончик Тоору | Автор: Матиенко Антон Александрович | E-mail: Aspksa@yandex.ru
setlocal
cd /d "%~dp0"
set "TOORU_PY=runtime\python\python.exe"
if exist "%TOORU_PY%" goto launch
where py >nul 2>nul
if not errorlevel 1 (set "TOORU_PY=py -3" & goto launch)
where python >nul 2>nul
if not errorlevel 1 (set "TOORU_PY=python" & goto launch)
echo Python не найден. Запустите SETUP.bat для инструкции.
pause
exit /b 1

:launch
%TOORU_PY% -m core.server --probe >nul 2>nul
if not errorlevel 1 goto browser

start "Tooru Core" /min cmd /c "%TOORU_PY% -m core.server"
for /l %%i in (1,1,20) do (
    %TOORU_PY% -m core.server --probe >nul 2>nul
    if not errorlevel 1 goto browser
    timeout /t 1 /nobreak >nul
)

echo Не удалось запустить ядро Дракончика Тоору.
echo Возможно, порт 8765 занят другой программой или ядро завершилось с ошибкой.
echo Для диагностики запустите вручную: %TOORU_PY% -m core.server
pause
exit /b 1

:browser
start "" "http://127.0.0.1:8765/"
exit /b 0
