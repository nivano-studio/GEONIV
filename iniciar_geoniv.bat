@echo off
title GEONIV - Meliponario Geolocation System
echo ========================================================
echo        GEONIV - Mapeamento e Controle de Meliponario
echo ========================================================
echo.
echo Verificando e instalando dependencias necessarias...
python -m pip install -r requirements.txt --quiet

echo.
echo Iniciando o servidor local GEONIV...
echo Abrindo a interface no seu navegador em http://localhost:8000
echo.

start http://localhost:8000
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload

pause
