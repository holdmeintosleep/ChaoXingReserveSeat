@echo off
setlocal

set PIP_TARGET=D:\python_packages

if not exist "%PIP_TARGET%" mkdir "%PIP_TARGET%"

set PYTHONPATH=%PYTHONPATH%;%PIP_TARGET%

python -m pip install --target=%PIP_TARGET% requests flask flask-cors cryptography numpy opencv-python

echo 依赖安装完成！

pause