@echo off
echo 🚀 PREPARANDO DEPLOY AUTOMÁTICO - PRINCESA APP

echo.
echo 📋 Verificando arquivos necessários...

if not exist "requirements.txt" (
    echo ❌ requirements.txt não encontrado!
    pause
    exit /b 1
)

if not exist "Procfile" (
    echo ❌ Procfile não encontrado!
    pause
    exit /b 1
)

if not exist "app.py" (
    echo ❌ app.py não encontrado!
    pause
    exit /b 1
)

echo ✅ Todos os arquivos encontrados!

echo.
echo 📁 Criando estrutura para deploy...

echo.
echo 🔧 Verificando Git...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git não instalado! 
    echo 📥 Baixe em: https://git-scm.com/download/windows
    pause
    exit /b 1
)

echo.
echo 📦 Inicializando repositório Git...
if not exist ".git" (
    git init
    git add .
    git commit -m "🌸 Initial commit - Princesa App"
    echo ✅ Repositório Git criado!
) else (
    echo ⚠️ Git já inicializado
)

echo.
echo 🌐 PRÓXIMOS PASSOS MANUAIS:
echo.
echo 1. 📁 CRIAR REPOSITÓRIO NO GITHUB:
echo    - Acesse: https://github.com/new
echo    - Nome: princesa-app
echo    - Público: ✅
echo    - Criar repositório
echo.
echo 2. 📤 CONECTAR E SUBIR CÓDIGO:
echo    git remote add origin https://github.com/SEU-USUARIO/princesa-app.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 3. 🚀 DEPLOY NO RENDER:
echo    - Acesse: https://render.com
echo    - Criar conta gratuita
echo    - New ^> Web Service
echo    - Connect GitHub
echo    - Selecionar princesa-app
echo.
echo 4. ⚙️ CONFIGURAÇÕES DO RENDER:
echo    - Name: princesa-app-ana-paula
echo    - Environment: Python 3
echo    - Build Command: ./build.sh
echo    - Start Command: gunicorn app:app
echo.
echo 5. 🗄️ BANCO DE DADOS:
echo    - New ^> PostgreSQL (gratuito)
echo    - Copiar credenciais
echo    - Adicionar nas Environment Variables
echo.
echo 💡 GUIA COMPLETO: DEPLOY_GUIDE.md
echo.
echo 🎉 EM 15 MINUTOS SEU APP ESTARÁ ONLINE 24/7!
echo.
pause