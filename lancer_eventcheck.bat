@echo off
title EventCheck - Menu Principal
color 0A

:menu
cls
echo.
echo ========================================
echo    EVENTCHECK - Gestion des Entrees
echo ========================================
echo.
echo    [1] Lancer l'application
echo    [2] Installer les bibliotheques
echo    [3] Verifier l'installation
echo    [4] Ouvrir le navigateur
echo    [5] Quitter
echo.
echo ========================================
echo.

set /p choix="Votre choix : "

if "%choix%"=="1" goto lancer
if "%choix%"=="2" goto installer
if "%choix%"=="3" goto verifier
if "%choix%"=="4" goto navigateur
if "%choix%"=="5" exit
goto menu

:lancer
cls
echo.
echo ========================================
echo    DEMARRAGE DE EVENTCHECK
echo ========================================
echo.
cd /d "%~dp0"

:: Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe !
    pause
    goto menu
)

:: Vérifier Flask
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installation des bibliotheques...
    pip install flask flask-socketio flask-cors pandas openpyxl pyttsx3 pydantic python-dotenv
)

echo.
echo L'application demarre...
echo URL : http://localhost:5000
echo.
echo NE FERMEZ PAS CETTE FENÊTRE !
echo.

:: Ouvrir navigateur après 3 secondes
start /b cmd /c "timeout /t 3 >nul && start http://localhost:5000"

python app.py
pause
goto menu

:installer
cls
echo.
echo ========================================
echo    INSTALLATION DES BIBLIOTHEQUES
echo ========================================
echo.
pip install flask flask-socketio flask-cors pandas openpyxl pyttsx3 pydantic python-dotenv
echo.
echo Installation terminee !
pause
goto menu

:verifier
cls
echo.
echo ========================================
echo    VERIFICATION DE L'INSTALLATION
echo ========================================
echo.
python --version
echo.
python -c "import flask; print('Flask : OK')" 2>nul || echo "Flask : NON INSTALLE"
python -c "import flask_socketio; print('SocketIO : OK')" 2>nul || echo "SocketIO : NON INSTALLE"
python -c "import pandas; print('Pandas : OK')" 2>nul || echo "Pandas : NON INSTALLE"
python -c "import openpyxl; print('OpenPyXL : OK')" 2>nul || echo "OpenPyXL : NON INSTALLE"
python -c "import pyttsx3; print('pyttsx3 : OK')" 2>nul || echo "pyttsx3 : NON INSTALLE"
python -c "import pydantic; print('Pydantic : OK')" 2>nul || echo "Pydantic : NON INSTALLE"
echo.
pause
goto menu

:navigateur
start http://localhost:5000
goto menu