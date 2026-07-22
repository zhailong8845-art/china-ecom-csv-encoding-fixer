@echo off
setlocal
if "%~1"=="" (
  echo Drag one CSV file onto run-windows.bat.
  pause
  exit /b 2
)
set "INPUT=%~1"
set "OUTPUT=%~dpn1-fixed.csv"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0csv_encoding_fixer.py" "%INPUT%" "%OUTPUT%" --json
) else (
  python "%~dp0csv_encoding_fixer.py" "%INPUT%" "%OUTPUT%" --json
)
set "RESULT=%errorlevel%"
if not "%RESULT%"=="0" echo Fix failed. The original file was not changed.
pause
exit /b %RESULT%
