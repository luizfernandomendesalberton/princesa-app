# 📱 CRIANDO APP ANDROID NATIVO - PRINCESA

## 🎯 **Transformando em APK Real com Capacitor**

### 🛠️ **Pré-requisitos:**
1. **Node.js** (v16+) - [nodejs.org](https://nodejs.org)
2. **Android Studio** - [developer.android.com](https://developer.android.com/studio)
3. **Java JDK 11** ou superior
4. **Gradle** (instalado com Android Studio)

### 📱 **Passo 1: Instalar Capacitor**

```bash
# No diretório do projeto princesa
cd "c:\Users\luizf\OneDrive\Documentos\Web-pastas-diversos\princesa"

# Instalar Capacitor CLI globalmente
npm install -g @capacitor/cli

# Criar package.json se não existir
npm init -y

# Instalar Capacitor no projeto
npm install @capacitor/core @capacitor/android @capacitor/ios
```

### 🔧 **Passo 2: Configurar Capacitor**

```bash
# Inicializar Capacitor
npx cap init "Princesa App" com.princesa.anapaula

# Adicionar plataforma Android
npx cap add android
```

### 📁 **Passo 3: Estrutura para Build**

Criar `www` folder com arquivos estáticos:

```bash
# Criar diretório de build
mkdir www

# Copiar arquivos do Flask para www
# (vamos criar um script para isso)
```

### 🎨 **Passo 4: Configurações do App**

Arquivo `capacitor.config.ts`:
```typescript
import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.princesa.anapaula',
  appName: 'Princesa Ana Paula',
  webDir: 'www',
  bundledWebRuntime: false,
  server: {
    androidScheme: 'https'
  },
  plugins: {
    StatusBar: {
      style: 'Dark',
      backgroundColor: '#ff1493'
    },
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: '#ff69b4',
      androidSplashResourceName: 'splash',
      showSpinner: false
    },
    LocalNotifications: {
      smallIcon: 'ic_stat_icon_config_sample',
      iconColor: '#ff1493'
    }
  }
};

export default config;
```

### 🖼️ **Passo 5: Ícones e Splash Screen**

Estrutura de recursos:
```
android/app/src/main/res/
├── mipmap-hdpi/
├── mipmap-mdpi/
├── mipmap-xhdpi/
├── mipmap-xxhdpi/
├── mipmap-xxxhdpi/
└── drawable/
```

### 🔄 **Passo 6: Build Script Automático**