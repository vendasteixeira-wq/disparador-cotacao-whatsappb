@echo off
title Setup Google API
color 0B
cd /d "%~dp0"
echo.
echo  Configurando Google API...
echo  Siga as instrucoes na tela.
echo.
py -3.11 setup_google.py
pause
