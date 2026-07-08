const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url)
});