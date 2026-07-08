# 超星学习通座位预约管理系统

一个功能完善的座位预约管理工具，提供 CLI 命令行界面和响应式 Web 应用，支持自动预约、定时签到/签退、日志管理等核心功能。

## 功能特性

### 核心功能
- **座位预约**：查询可用座位，提交预约请求，支持设置日期、时间段及座位偏好
- **预约管理**：查看/修改/取消个人预约记录
- **自动签到**：预约开始时间自动执行签到，支持配置提前签到时间阈值
- **自动签退**：预约结束时间自动执行签退，支持配置延迟签退时间阈值
- **定时任务调度**：可靠的定时任务调度机制，设备休眠/网络中断恢复后自动重试
- **日志系统**：完善的日志记录，支持查询、导出（JSON/CSV/TXT）和统计
- **错误恢复**：预约失败/签到超时等异常情况的重试机制和通知功能

### 应用形式
- **CLI 命令行工具**：功能完善的终端命令，适合脚本自动化和高级用户
- **Web 应用**：响应式界面，支持主流浏览器，提供直观的用户体验

## 系统要求

- Ubuntu 20.04 LTS 或更高版本
- Python 3.8+
- 至少 2GB 内存
- 至少 1GB 磁盘空间

## 快速开始

### 1. 安装依赖

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### 2. 克隆项目

```bash
git clone <repository-url>
cd ChaoXingReserveSeat
```

### 3. 创建虚拟环境并安装

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. 配置

```bash
cp config.template.json config.json
# 编辑 config.json，填入你的账号信息
```

### 5. 启动服务

```bash
# 启动后端 API 服务
cd backend && python app.py

# 新终端，启动定时任务调度器
python scheduler.py --mode run
```

访问 http://localhost:5000 使用 Web 界面。

## CLI 命令参考

### 预约座位

```bash
# 查看可用配置
python cli.py reserve

# 使用配置索引 0 预约
python cli.py reserve --index 0

# 强制预约（忽略日期限制）
python cli.py reserve --index 0 --force

# 预约明天
python cli.py reserve --index 0 --next-day
```

### 查询预约记录

```bash
python cli.py query
python cli.py query --username 你的学号
```

### 签到/签退

```bash
python cli.py signin --index 0
python cli.py signout --index 0
```

### 定时任务管理

```bash
# 自动生成今日任务
python cli.py scheduler auto

# 查看任务列表
python cli.py scheduler list

# 按状态筛选
python cli.py scheduler list --status pending

# 手动创建任务
python cli.py scheduler create --task-type signin --config-index 0 --target-time "2026-07-09 10:30:00"

# 取消任务
python cli.py scheduler cancel --task-id <任务ID>

# 启动调度器
python cli.py scheduler run

# 查看通知
python cli.py scheduler notifications
```

### 日志管理

```bash
# 查看最近 100 条日志
python cli.py logs --tail 100

# 按时间筛选
python cli.py logs --since "2026-07-01 00:00:00"

# 导出日志
python cli.py logs --export logs_backup.txt
```

### 配置管理

```bash
# 列出所有配置
python cli.py config list

# 查看指定配置
python cli.py config view --index 0

# 添加配置
python cli.py config add --json '{"username":"xxx","password":"xxx","time":["10:30","14:15"],"roomid":"123","seatid":["001"],"daysofweek":["Monday","Tuesday"]}'

# 更新配置
python cli.py config update --index 0 --json '{...}'

# 删除配置
python cli.py config delete --index 0

# 查看签到配置
python cli.py config signin
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/config` | 获取配置列表 |
| GET | `/api/config/<index>` | 获取单个配置 |
| POST | `/api/config` | 添加配置 |
| PUT | `/api/config/<index>` | 更新配置 |
| DELETE | `/api/config/<index>` | 删除配置 |
| GET | `/api/reservations` | 查询预约记录 |
| POST | `/api/reservations/reserve` | 提交预约 |
| POST | `/api/signin` | 执行签到 |
| POST | `/api/signout` | 执行签退 |
| GET | `/api/scheduler/tasks` | 获取任务列表 |
| POST | `/api/scheduler/tasks` | 创建定时任务 |
| DELETE | `/api/scheduler/tasks/<id>` | 取消任务 |
| POST | `/api/scheduler/start` | 启动调度器 |
| POST | `/api/scheduler/stop` | 停止调度器 |
| GET | `/api/scheduler/status` | 调度器状态 |
| POST | `/api/scheduler/auto_schedule` | 自动生成今日任务 |
| GET | `/api/logs` | 查询日志 |
| POST | `/api/logs/export` | 导出日志 |
| GET | `/api/logs/stats` | 日志统计 |
| POST | `/api/logs/clear` | 清除过期日志 |

## 项目结构

```
ChaoXingReserveSeat/
├── cli.py                  # CLI 命令行工具
├── scheduler.py            # 定时任务调度器
├── logger.py               # 日志管理系统
├── retry.py                # 重试与异常恢复机制
├── utils/                  # 核心工具模块
│   ├── common.py           # 公共工具函数
│   ├── reserve.py          # 预约功能
│   ├── signin.py           # 签到功能
│   ├── reservation_manager.py  # 预约记录管理
│   └── encrypt.py          # 加密模块
├── backend/                # 后端 API 服务
│   ├── app.py              # Flask 应用入口
│   ├── bputils/            # 业务工具类
│   │   ├── config_manager.py   # 配置管理器
│   │   └── path_utils.py       # 路径工具
│   └── routes/             # API 路由
│       ├── config_routes.py     # 配置路由
│       ├── reservation_routes.py # 预约路由
│       ├── signin_routes.py     # 签到路由
│       ├── scheduler_routes.py  # 调度器路由
│       └── log_routes.py        # 日志路由
├── frontend/               # 前端 Web 应用
│   ├── src/
│   │   ├── main.js         # Vue 入口
│   │   ├── App.vue         # 根组件
│   │   ├── api/            # API 调用
│   │   └── components/     # Vue 组件
│   ├── dist/               # 构建产物
│   └── package.json
├── config.template.json    # 配置文件模板
├── config.json             # 配置文件（需自行创建）
├── requirements.txt        # Python 依赖
├── INSTALL.md              # 详细安装部署文档
└── README.md               # 项目说明
```

## 配置文件说明

```json
{
    "signin": {
        "enabled": true,
        "location": {
            "latitude": 30.0,    // GPS 纬度
            "longitude": 120.0,  // GPS 经度
            "address": "图书馆"   // 位置描述
        },
        "interval": 300         // 签到检查间隔(秒)
    },
    "reserve": [
        {
            "username": "学号/手机号",
            "password": "密码",
            "time": ["10:30", "14:15"],  // [开始时间, 结束时间]
            "roomid": "房间ID",
            "seatid": ["座位号"],
            "daysofweek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
    ]
}
```

## 后台运行

使用 systemd 将服务设为开机自启。详见 [INSTALL.md](INSTALL.md)。

## 安全建议

1. 配置文件 `config.json` 包含敏感信息，确保文件权限为 `600`
2. 使用 HTTPS 加密传输
3. 定期更新密码
4. 启用防火墙限制访问

## 许可证

MIT License