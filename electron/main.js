const { app, BrowserWindow, Menu, Tray, ipcMain, dialog, shell, session } = require('electron');
const path = require('path');
const url = require('url');
const { autoUpdater } = require('electron-updater');
const fs = require('fs');
const { spawn, exec } = require('child_process');
const http = require('http');

let mainWindow;
let tray = null;
let backendProcess = null;
let isQuitting = false;

const APP_NAME = '超星座位预约';
const APP_VERSION = app.getVersion();
const BACKEND_PORT = 5000;

function startBackend() {
  return new Promise((resolve, reject) => {
    const pythonPath = process.env.PYTHON_PATH || 'python';
    const backendDir = path.join(__dirname, '..', 'backend');
    
    backendProcess = spawn(pythonPath, ['app.py'], {
      cwd: backendDir,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONPATH: path.join(__dirname, '..') }
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`Backend stdout: ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`Backend stderr: ${data}`);
    });

    backendProcess.on('error', (err) => {
      console.error('Failed to start backend:', err);
      reject(err);
    });

    backendProcess.on('exit', (code) => {
      console.log(`Backend process exited with code ${code}`);
      if (!isQuitting) {
        dialog.showErrorBox('后端服务异常', '后端服务意外退出，应用将重新启动');
        app.relaunch();
        app.exit();
      }
    });

    setTimeout(() => {
      resolve();
    }, 2000);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: `${APP_NAME} v${APP_VERSION}`,
    icon: path.join(__dirname, 'icons', 'app.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    show: false
  });

  const startUrl = process.env.ELECTRON_START_URL || 
    url.format({
      pathname: path.join(__dirname, '..', 'frontend', 'dist', 'index.html'),
      protocol: 'file:',
      slashes: true
    });

  mainWindow.loadURL(startUrl);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on('close', (event) => {
    if (!isQuitting && app.dock) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  setupProxy();
}

function setupProxy() {
  session.defaultSession.webRequest.onBeforeRequest((details, callback) => {
    if (details.url.startsWith('file://') && details.url.includes('/api/')) {
      const apiPath = details.url.replace(/^file:\/\/[^/]+\/api/, '/api');
      const proxyUrl = `http://localhost:${BACKEND_PORT}${apiPath}`;
      
      callback({ cancel: false, redirectURL: proxyUrl });
    } else {
      callback({ cancel: false });
    }
  });
}

function createMenu() {
  const template = [
    {
      label: '文件',
      submenu: [
        {
          label: '退出',
          accelerator: 'Ctrl+Q',
          click: () => {
            isQuitting = true;
            app.quit();
          }
        }
      ]
    },
    {
      label: '编辑',
      submenu: [
        { label: '撤销', accelerator: 'Ctrl+Z', role: 'undo' },
        { label: '重做', accelerator: 'Ctrl+Y', role: 'redo' },
        { type: 'separator' },
        { label: '剪切', accelerator: 'Ctrl+X', role: 'cut' },
        { label: '复制', accelerator: 'Ctrl+C', role: 'copy' },
        { label: '粘贴', accelerator: 'Ctrl+V', role: 'paste' },
        { label: '全选', accelerator: 'Ctrl+A', role: 'selectAll' }
      ]
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '检查更新',
          click: () => {
            autoUpdater.checkForUpdates();
          }
        },
        {
          label: `关于 ${APP_NAME}`,
          click: () => {
            dialog.showMessageBox({
              title: `关于 ${APP_NAME}`,
              message: `${APP_NAME}\n版本: ${APP_VERSION}\n\n超星学习通座位预约与签到管理工具`,
              icon: path.join(__dirname, 'icons', 'app.ico')
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function createTray() {
  tray = new Tray(path.join(__dirname, 'icons', 'app.ico'));
  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示主窗口',
      click: () => {
        mainWindow.show();
        mainWindow.focus();
      }
    },
    {
      label: '检查更新',
      click: () => {
        autoUpdater.checkForUpdates();
      }
    },
    {
      type: 'separator'
    },
    {
      label: '退出',
      click: () => {
        isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setToolTip(APP_NAME);
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    mainWindow.show();
    mainWindow.focus();
  });
}

function setupAutoUpdater() {
  autoUpdater.setFeedURL({
    provider: 'github',
    repo: 'ChaoXingReserveSeat',
    owner: 'your-github-username',
    private: false
  });

  autoUpdater.on('checking-for-update', () => {
    console.log('检查更新中...');
  });

  autoUpdater.on('update-available', (info) => {
    console.log('发现新版本:', info.version);
    dialog.showMessageBox({
      type: 'info',
      title: '发现新版本',
      message: `发现新版本 ${info.version}，是否立即更新？`,
      buttons: ['是', '否']
    }).then((result) => {
      if (result.response === 0) {
        autoUpdater.downloadUpdate();
      }
    });
  });

  autoUpdater.on('update-not-available', () => {
    dialog.showMessageBox({
      type: 'info',
      title: '检查更新',
      message: '当前已是最新版本',
      buttons: ['确定']
    });
  });

  autoUpdater.on('download-progress', (progress) => {
    console.log(`下载进度: ${progress.percent}%`);
  });

  autoUpdater.on('update-downloaded', () => {
    dialog.showMessageBox({
      type: 'info',
      title: '更新完成',
      message: '更新已下载完成，应用将重启安装更新',
      buttons: ['确定']
    }).then(() => {
      autoUpdater.quitAndInstall();
    });
  });

  autoUpdater.on('error', (err) => {
    console.error('更新错误:', err);
    dialog.showErrorBox('更新失败', `更新过程中发生错误: ${err.message}`);
  });
}

async function setupBackend() {
  try {
    await startBackend();
    console.log('Backend service started');
  } catch (err) {
    console.error('Failed to start backend:', err);
    dialog.showErrorBox('启动失败', `无法启动后端服务:\n${err.message}\n\n请确保已安装Python及相关依赖`);
    app.exit(1);
  }
}

app.whenReady().then(async () => {
  createWindow();
  createMenu();
  createTray();
  setupAutoUpdater();
  await setupBackend();

  autoUpdater.checkForUpdates();

  app.on('activate', () => {
    if (mainWindow === null) {
      createWindow();
    }
  });
});

app.on('before-quit', () => {
  isQuitting = true;
  if (backendProcess) {
    backendProcess.kill('SIGTERM');
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

ipcMain.handle('get-app-version', () => APP_VERSION);
ipcMain.handle('get-backend-url', () => `http://localhost:${BACKEND_PORT}`);
ipcMain.handle('open-external', (event, url) => {
  shell.openExternal(url);
});