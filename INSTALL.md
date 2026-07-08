# 超星学习通座位预约管理系统 - Ubuntu 安装部署文档

## 系统要求

- Ubuntu 20.04 LTS 或更高版本
- Python 3.8 或更高版本
- 至少 2GB 内存
- 至少 1GB 磁盘空间

## 目录结构

```
ChaoXingReserveSeat/
├── cli.py              # 命令行接口
├── scheduler.py        # 定时任务调度器
├── logger.py           # 日志管理系统
├── retry.py            # 异常恢复与重试机制
├── utils/              # 核心工具模块
│   ├── reserve.py      # 预约功能
│   ├── signin.py       # 签到功能
│   ├── reservation_manager.py  # 预约记录管理
│   └── encrypt.py      # 加密模块
├── backend/            # 后端API服务
│   ├── app.py          # Flask应用入口
│   ├── bputils/        # 工具类
│   └── routes/         # API路由
├── frontend/           # 前端Web应用
│   └── src/            # Vue组件
├── config.json         # 配置文件
├── requirements.txt    # Python依赖
└── INSTALL.md          # 安装文档
```

## 安装步骤

### 1. 安装系统依赖

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl
```

### 2. 克隆项目

```bash
git clone <repository-url>
cd ChaoXingReserveSeat
```

### 3. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 5. 配置文件设置

```bash
cp config.template.json config.json
```

编辑 `config.json` 文件，添加您的超星学习通账号信息：

```json
{
    "signin": {
        "enabled": true,
        "location": {
            "latitude": 30.0,
            "longitude": 120.0,
            "address": "图书馆"
        },
        "interval": 300
    },
    "reserve": [
        {
            "username": "你的学号或手机号",
            "password": "你的密码",
            "time": ["10:30", "14:15"],
            "roomid": "房间ID",
            "seatid": ["座位号"],
            "daysofweek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
    ]
}
```

### 6. 安装前端依赖（可选）

```bash
cd frontend
npm install
npm run build
cd ..
```

## 启动服务

### 启动后端服务

```bash
cd backend
python app.py
```

服务将在 http://localhost:5000 启动。

### 启动定时任务调度器

```bash
python scheduler.py --mode run
```

### 使用CLI命令

```bash
# 查看帮助
python cli.py --help

# 预约座位
python cli.py reserve --index 0

# 查询预约记录
python cli.py query

# 执行签到
python cli.py signin --index 0

# 执行签退
python cli.py signout --index 0

# 查看日志
python cli.py logs --tail 100

# 管理配置
python cli.py config list
```

## 配置说明

### 配置文件字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| signin.enabled | bool | 是否启用自动签到 |
| signin.location.latitude | float | GPS纬度 |
| signin.location.longitude | float | GPS经度 |
| signin.location.address | string | 位置描述 |
| signin.interval | int | 签到检查间隔(秒) |
| reserve[].username | string | 用户名/学号 |
| reserve[].password | string | 密码 |
| reserve[].time | array | 时间段 [开始时间, 结束时间] |
| reserve[].roomid | string | 房间ID |
| reserve[].seatid | array | 座位号列表 |
| reserve[].daysofweek | array | 预约日期 (Monday-Sunday) |

### 常用高校坐标

| 学校 | 纬度 | 经度 |
|------|------|------|
| 武汉大学 | 30.5427 | 114.3628 |
| 华中科技大学 | 30.5154 | 114.4214 |
| 浙江大学 | 30.2634 | 120.1236 |
| 南京大学 | 32.1161 | 118.9588 |
| 北京大学 | 39.9869 | 116.3058 |
| 清华大学 | 40.0084 | 116.3164 |

## 后台运行

### 使用 systemd 服务

创建服务文件 `/etc/systemd/system/chaoxing-seat.service`：

```ini
[Unit]
Description=超星学习通座位预约管理系统
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ChaoXingReserveSeat
ExecStart=/home/ubuntu/ChaoXingReserveSeat/venv/bin/python backend/app.py
Restart=always
RestartSec=10
Environment=PATH=/home/ubuntu/ChaoXingReserveSeat/venv/bin

[Install]
WantedBy=multi-user.target
```

创建调度器服务文件 `/etc/systemd/system/chaoxing-scheduler.service`：

```ini
[Unit]
Description=超星学习通定时任务调度器
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ChaoXingReserveSeat
ExecStart=/home/ubuntu/ChaoXingReserveSeat/venv/bin/python scheduler.py --mode run
Restart=always
RestartSec=10
Environment=PATH=/home/ubuntu/ChaoXingReserveSeat/venv/bin

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable chaoxing-seat
sudo systemctl enable chaoxing-scheduler
sudo systemctl start chaoxing-seat
sudo systemctl start chaoxing-scheduler
```

查看状态：

```bash
sudo systemctl status chaoxing-seat
sudo systemctl status chaoxing-scheduler
```

## Nginx 反向代理配置

```bash
sudo apt install nginx
```

创建配置文件 `/etc/nginx/sites-available/chaoxing-seat`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

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
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/chaoxing-seat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 日志管理

日志文件位于项目根目录下的 `chaoxing_seat.log`。

```bash
# 查看日志
tail -f chaoxing_seat.log

# 查看最近100条日志
python logger.py --action view --limit 100

# 导出日志
python logger.py --action export --export-file logs.json --format json

# 查看统计
python logger.py --action stats --days 7
```

## 故障排查

### 常见问题

1. **登录失败**
   - 检查用户名和密码是否正确
   - 确认网络连接正常

2. **预约失败**
   - 检查房间ID和座位号是否正确
   - 确认预约日期在配置的daysofweek范围内

3. **签到失败**
   - 检查GPS位置是否正确配置
   - 确认预约记录存在

4. **服务无法启动**
   - 检查端口5000是否被占用
   - 确认所有依赖已正确安装

### 错误日志

所有错误信息会记录到 `chaoxing_seat.log` 文件中，可以通过以下命令查看：

```bash
grep -E "(ERROR|CRITICAL)" chaoxing_seat.log
```

## 更新升级

```bash
cd ChaoXingReserveSeat
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart chaoxing-seat
sudo systemctl restart chaoxing-scheduler
```

## 安全建议

1. 配置文件 `config.json` 包含敏感信息，确保文件权限设置为 600
2. 使用HTTPS加密传输（推荐使用Let's Encrypt）
3. 定期更新密码
4. 不要在公共网络环境下使用
5. 启用防火墙限制访问

## 技术支持

如遇问题，请查看以下资源：
- 项目 README.md 文件
- 日志文件 chaoxing_seat.log
- 项目 issue 页面