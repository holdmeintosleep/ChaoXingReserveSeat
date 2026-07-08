@echo off
chcp 65001 >nul
echo ================================================
echo   超星学习通自动答题工具 - 打包脚本
echo   仅用于技术学习研究
echo ================================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到Python环境
    echo 请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

:: 检查pip是否安装
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到pip
    pause
    exit /b 1
)

echo 1. 安装依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 错误: 安装依赖失败
    pause
    exit /b 1
)
echo 依赖安装成功
echo.

echo 2. 打包为单文件exe...
echo 正在使用PyInstaller打包，请稍候...
echo.

:: 使用PyInstaller打包
pyinstaller ^
    --onefile ^
    --windowed ^
    --name=ChaoXingAutoAnswer ^
    --add-data="config.json;." ^
    --hidden-import=selenium ^
    --hidden-import=requests ^
    --hidden-import=beautifulsoup4 ^
    --hidden-import=lxml ^
    --hidden-import=chromedriver_autoinstaller ^
    --hidden-import=msedgedriver_autoinstaller ^
    --exclude-module=matplotlib ^
    --exclude-module=numpy ^
    --exclude-module=scipy ^
    --distpath=dist ^
    --workpath=build ^
    --specpath=build ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo 错误: 打包失败
    pause
    exit /b 1
)

echo.
echo 打包成功！
echo.
echo 输出文件位置: dist\ChaoXingAutoAnswer.exe
echo.

:: 复制配置文件到dist目录
copy config.json dist\ >nul
if %errorlevel% equ 0 (
    echo 配置文件已复制到 dist\config.json
)

echo.
echo ================================================
echo   打包完成！
echo ================================================
echo.
echo 使用方法:
echo 1. 将 dist 目录下的文件复制到U盘
echo 2. 在目标电脑上运行 ChaoXingAutoAnswer.exe
echo 3. 首次运行请先配置登录信息
echo.
echo 注意: 目标电脑需要安装Chrome或Edge浏览器
echo ================================================
pause