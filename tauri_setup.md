# 手机应用打包方案 - Tauri

## 方案概述

使用 Tauri 将 Vue + Flask 应用打包为原生手机应用。

## 步骤

### 1. 安装依赖

```bash
# 安装 Node.js (已安装)
# 安装 Rust (用于编译 Tauri)
# 安装 Android SDK (用于 Android 打包)
```

### 2. 初始化 Tauri 项目

```bash
cd frontend
npm install @tauri-apps/cli --save-dev
npx tauri init -y
```

### 3. 配置 Tauri

修改 `tauri.conf.json`:

```json
{
  "build": {
    "beforeBuildCommand": "npm run build",
    "devPath": "http://localhost:5000",
    "distDir": "../dist"
  },
  "tauri": {
    "bundle": {
      "identifier": "com.example.chaoxing-reserve",
      "icon": ["icons/128x128.png", "icons/128x128@2x.png"]
    }
  }
}
```

### 4. 打包命令

```bash
# 开发模式
npx tauri dev

# 构建桌面应用
npx tauri build

# 构建 Android APK
npx tauri build --target aarch64-linux-android

# 构建 iOS (需要 macOS)
npx tauri build --target aarch64-apple-ios
```

## 注意事项

1. **后端集成**: 需要将 Flask 后端打包进应用，或使用远程 API
2. **Android SDK**: 需要安装 Android Studio 或 SDK 命令行工具
3. **iOS**: 需要 macOS 系统和 Xcode
4. **图标**: 需要准备不同尺寸的应用图标

## 替代方案

### 方案A: WebView 封装 (推荐)
使用 Capacitor 或 Cordova 将网页包装为原生应用

### 方案B: 纯前端 + 远程 API
将前端部署到服务器，后端 API 对外暴露，手机通过浏览器访问

### 方案C: 本地服务器模式
使用 Python 的 mobile 库打包 Flask 应用为 APK