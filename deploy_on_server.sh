#!/bin/bash

set -e

REPO_URL="https://github.com/holdmeintosleep/ChaoXingReserveSeat.git"
PROJECT_DIR="/opt/ChaoXingReserveSeat"

echo "=========================================="
echo "超星学习通座位预约管理系统 - 服务器部署脚本"
echo "=========================================="

echo ""
echo "[阶段1] 更新系统并安装依赖"
echo "------------------------------------------"
sudo apt update -y
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx

echo ""
echo "[阶段2] 克隆GitHub仓库"
echo "------------------------------------------"
sudo rm -rf $PROJECT_DIR
sudo git clone $REPO_URL $PROJECT_DIR
sudo chown -R $USER:$USER $PROJECT_DIR

echo ""
echo "[阶段3] 创建虚拟环境并安装Python依赖"
echo "------------------------------------------"
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "[阶段4] 创建配置文件"
echo "------------------------------------------"
cp config.template.json config.json
echo "配置文件已创建，请编辑 config.json 添加账号信息"

echo ""
echo "[阶段5] 配置Nginx反向代理"
echo "------------------------------------------"
sudo cat > /etc/nginx/sites-available/chaoxing-seat << 'EOF'
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/chaoxing-seat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo ""
echo "[阶段6] 创建systemd服务"
echo "------------------------------------------"
sudo cat > /etc/systemd/system/chaoxing-seat.service << 'EOF'
[Unit]
Description=超星学习通座位预约管理系统
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ChaoXingReserveSeat
ExecStart=/opt/ChaoXingReserveSeat/venv/bin/python backend/app.py
Restart=always
RestartSec=10
Environment=PATH=/opt/ChaoXingReserveSeat/venv/bin

[Install]
WantedBy=multi-user.target
EOF

sudo cat > /etc/systemd/system/chaoxing-scheduler.service << 'EOF'
[Unit]
Description=超星学习通定时任务调度器
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ChaoXingReserveSeat
ExecStart=/opt/ChaoXingReserveSeat/venv/bin/python scheduler.py --mode run
Restart=always
RestartSec=10
Environment=PATH=/opt/ChaoXingReserveSeat/venv/bin

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable chaoxing-seat
sudo systemctl enable chaoxing-scheduler

echo ""
echo "[阶段7] 启动服务"
echo "------------------------------------------"
sudo systemctl start chaoxing-seat
sudo systemctl start chaoxing-scheduler

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "服务访问地址: http://$(curl -s ifconfig.me)"
echo ""
echo "请手动编辑配置文件:"
echo "  $PROJECT_DIR/config.json"
echo ""
echo "添加超星学习通账号信息后重启服务:"
echo "  sudo systemctl restart chaoxing-seat"
echo "  sudo systemctl restart chaoxing-scheduler"