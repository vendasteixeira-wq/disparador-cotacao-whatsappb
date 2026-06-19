@echo off
title Disparador de Cotacao - Estrela d'Agua
color 0A
cd /d "%~dp0"
echo.
echo  ================================================
echo   Disparador de Cotacao - Pousada Estrela d'Agua
echo  ================================================
py -3.11 --version >nul 2>&1
if errorlevel 1 (echo [ERRO] Python 3.11 nao encontrado! & pause & exit /b)
echo  [1/3] Python OK
py -3.11 -m pip install flask pywhatkit google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client --quiet --disable-pip-version-check
echo  [2/3] Dependencias OK
echo  [3/3] Iniciando servidor...
echo.
echo   Acesse: http://localhost:5050
echo   Feche esta janela para encerrar
echo.
start "" cmd /c "timeout /t 3 >nul && start http://localhost:5050"
py -3.11 app.py
pause
