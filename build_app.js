const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const projectRoot = path.dirname(__filename);
const buildDir = path.join(projectRoot, 'build', 'ChaoxingReserveSeat');

function copyDir(src, dest) {
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }
  
  const files = fs.readdirSync(src);
  for (const file of files) {
    const srcPath = path.join(src, file);
    const destPath = path.join(dest, file);
    
    if (fs.statSync(srcPath).isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function createBuild() {
  console.log('Creating build directory...');
  if (fs.existsSync(buildDir)) {
    fs.rmSync(buildDir, { recursive: true });
  }
  fs.mkdirSync(buildDir, { recursive: true });

  console.log('Copying Electron resources...');
  const electronPath = path.join(projectRoot, 'electron', 'node_modules', 'electron');
  const electronDist = path.join(electronPath, 'dist');
  
  if (fs.existsSync(electronDist)) {
    copyDir(electronDist, buildDir);
  } else {
    console.error('Electron not found!');
    process.exit(1);
  }

  console.log('Creating app.asar...');
  const appDir = path.join(buildDir, 'resources', 'app');
  fs.mkdirSync(appDir, { recursive: true });

  console.log('Copying application files...');
  copyDir(path.join(projectRoot, 'electron'), appDir);
  copyDir(path.join(projectRoot, 'frontend', 'dist'), path.join(appDir, 'frontend', 'dist'));
  copyDir(path.join(projectRoot, 'backend'), path.join(appDir, 'backend'));
  copyDir(path.join(projectRoot, 'utils'), path.join(appDir, 'utils'));
  fs.copyFileSync(path.join(projectRoot, 'config.template.json'), path.join(appDir, 'config.template.json'));
  fs.copyFileSync(path.join(projectRoot, 'main.py'), path.join(appDir, 'main.py'));

  console.log('Creating startup script...');
  const startupScript = `@echo off
cd /d "%~dp0"
start "" "ChaoxingReserveSeat.exe"
exit`;
  fs.writeFileSync(path.join(buildDir, '启动应用.bat'), startupScript);

  console.log('Build completed successfully!');
  console.log(`Build directory: ${buildDir}`);
}

createBuild();