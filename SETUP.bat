@echo off
rem Дракончик Тоору | Автор: Матиенко Антон Александрович | E-mail: Aspksa@yandex.ru
setlocal
cd /d "%~dp0"
if exist "runtime\python\python.exe" goto ready
echo Для переносимого запуска поместите официальный Python 3.10+ в runtime\python\python.exe.
echo Можно также установить Python 3.10+ в Windows, затем запустить ДракончикТоору.bat.
echo Автоматическая загрузка Python пока не реализована: требуется проверяемый установочный пакет.
pause
exit /b 1
:ready
"runtime\python\python.exe" --version
if errorlevel 1 exit /b 1
echo Python готов. Запустите ДракончикТоору.bat.
pause
