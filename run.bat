@echo off
title Projeto Princesa Ana Paula
color d
echo.
echo ===============================================
echo            🌸 PROJETO PRINCESA 💖
echo         Sistema para Ana Paula Schlickmann
echo ===============================================
echo.
echo 🚀 Iniciando o servidor...
echo.
cd /d "%~dp0"

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado! Por favor, instale o Python 3.8+
    echo.
    pause
    exit /b 1
)

REM Verificar se as dependências estão instaladas
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo 📦 Instalando dependências...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Erro ao instalar dependências!
        pause
        exit /b 1
    )
)

echo ✅ Dependências verificadas!
echo.
echo 🌐 Iniciando servidor Flask...
echo 💖 Acesse: http://localhost:5000
echo 🔑 Login: ana_paula / princesa123
echo.
echo ⚡ Pressione Ctrl+C para parar o servidor
echo.

REM Iniciar o servidor
python back-end/sever.py

echo.
echo 👋 Servidor encerrado!
pause