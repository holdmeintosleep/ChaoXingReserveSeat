# 超星学习通自动答题工具 - U盘部署教程

## ⚠️ 合规风险提示

**本工具仅用于Web自动化技术学习与研究目的**，严禁用于考试作弊等违规场景。

---

## 目录结构

```
U盘根目录/
├── ChaoXingAutoAnswer.exe    # 主程序
└── config.json               # 配置文件
```

---

## 部署步骤

### 第一步：打包程序

1. 在开发电脑上打开命令提示符（CMD）
2. 进入项目目录：
   ```
   cd D:\code\Project\ChaoXingReserveSeat\auto_answer
   ```
3. 运行打包脚本：
   ```
   build.bat
   ```
4. 等待打包完成，输出文件位于 `dist` 目录

### 第二步：复制到U盘

1. 打开 `dist` 目录
2. 将以下文件复制到U盘根目录：
   - `ChaoXingAutoAnswer.exe`
   - `config.json`

### 第三步：配置工具

1. 将U盘插入目标电脑
2. 打开U盘，双击运行 `ChaoXingAutoAnswer.exe`
3. 首次运行需要配置登录信息：
   ```
   ChaoXingAutoAnswer.exe config login
   ```

---

## 配置项说明

### login（登录信息）
```json
{
    "username": "你的学号或手机号",
    "password": "你的密码",
    "login_url": "https://passport2.chaoxing.com/mlogin?loginType=1&newversion=true&fid="
}
```

### browser（浏览器设置）
```json
{
    "type": "chrome",
    "headless": false,
    "window_size": "1920,1080"
}
```

### delay（延迟设置）
```json
{
    "min_delay": 1,
    "max_delay": 6,
    "total_time_min": 180
}
```

### search_api（搜题API）
```json
{
    "enabled": true,
    "api_url": "你的API地址",
    "api_key": "你的API密钥",
    "timeout": 10
}
```

---

## 使用方法

### 运行自动答题

```
ChaoXingAutoAnswer.exe run
```

### 配置登录信息

```
ChaoXingAutoAnswer.exe config login
```

### 配置浏览器

```
ChaoXingAutoAnswer.exe config browser
```

### 配置延迟参数

```
ChaoXingAutoAnswer.exe config delay
```

### 配置搜题API

```
ChaoXingAutoAnswer.exe config api
```

### 查看当前配置

```
ChaoXingAutoAnswer.exe config show
```

---

## 注意事项

1. **目标电脑要求**：
   - Windows 10/11 系统
   - 安装了 Chrome 或 Edge 浏览器
   - 网络连接正常

2. **U盘使用**：
   - 建议使用 USB 3.0 或更高版本的U盘
   - 运行时不要拔出U盘
   - 配置文件会保存在U盘上

3. **安全提示**：
   - 不要在公共电脑上保存密码
   - 定期更新工具版本
   - 注意保护个人信息

---

## 常见问题

### Q1: 程序无法启动
**原因**：目标电脑缺少必要的运行库

**解决**：安装 [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Q2: 浏览器启动失败
**原因**：未安装Chrome或Edge浏览器

**解决**：安装Chrome或Edge浏览器

### Q3: 登录失败
**原因**：账号密码错误或网络问题

**解决**：检查账号密码是否正确，确保网络连接正常

### Q4: 题目识别失败
**原因**：页面结构变化

**解决**：更新工具版本，或手动调整配置

---

## 更新日志

### v1.0.0
- 初始版本
- 支持单选、多选、判断、填空题
- 支持Chrome和Edge浏览器
- 支持搜题API和本地题库