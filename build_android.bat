@echo off
echo 🌸 CRIANDO APK DA PRINCESA ANA PAULA 📱

echo.
echo ⏳ Verificando Node.js...
node --version
if %errorlevel% neq 0 (
    echo ❌ Node.js não encontrado! 
    echo 📥 Baixe em: https://nodejs.org
    pause
    exit /b 1
)

echo.
echo ⏳ Instalando dependências...
call npm install

echo.
echo ⏳ Construindo aplicativo...
call python build_app.py

echo.
echo ⏳ Adicionando plataforma Android...
call npx cap add android

echo.
echo ⏳ Sincronizando arquivos...
call npx cap sync android

echo.
echo ⏳ Abrindo Android Studio...
call npx cap open android

echo.
echo 🎉 PRONTO! Android Studio foi aberto.
echo.
echo 📱 PRÓXIMOS PASSOS NO ANDROID STUDIO:
echo    1. Aguarde o projeto carregar
echo    2. Conecte seu celular Android (modo desenvolvedor)
echo    3. Clique no botão ▶️ (Run) para instalar no celular
echo    4. OU vá em Build → Generate Signed Bundle/APK
echo.
echo 👑 A Princesa Ana Paula terá seu app nativo! 💖
pause