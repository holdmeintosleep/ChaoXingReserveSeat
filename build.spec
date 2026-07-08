import os
import sys
import shutil

project_root = os.path.abspath('.')
dist_dir = os.path.join(project_root, 'dist', 'ChaoxingReserveSeat')

block_cipher = None

a = Analysis(
    ['desktop_app.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'backend'), 'backend'),
        (os.path.join(project_root, 'utils'), 'utils'),
        (os.path.join(project_root, 'config.template.json'), '.'),
        (os.path.join(project_root, 'main.py'), '.'),
        (os.path.join(project_root, 'install_deps.bat'), '.')
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'requests',
        'cryptography',
        'numpy',
        'cv2',
        'backend.app',
        'backend.bputils.config_manager',
        'backend.bputils.path_utils',
        'backend.routes.config_routes',
        'backend.routes.reservation_routes',
        'backend.routes.signin_routes',
        'utils.reserve',
        'utils.reservation_manager',
        'utils.signin',
        'utils.encrypt'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'notebook',
        'ipython'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ChaoxingReserveSeat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ChaoxingReserveSeat'
)

def post_build():
    frontend_src = os.path.join(project_root, 'frontend', 'dist')
    frontend_dest = os.path.join(dist_dir, '_internal', 'frontend', 'dist')
    if os.path.exists(frontend_src) and os.path.exists(dist_dir):
        if os.path.exists(frontend_dest):
            shutil.rmtree(frontend_dest)
        shutil.copytree(frontend_src, frontend_dest)
        print(f'Copied frontend to {frontend_dest}')

post_build()