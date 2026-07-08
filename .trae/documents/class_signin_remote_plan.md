# 超星课堂远程签到功能实现计划

## 摘要

在现有超星座位预约与签到系统基础上，新增**课堂签到（远程签到）**功能。该功能支持自动检测教师发布的课堂签到活动并完成签到，覆盖普通签到、位置签到、手势签到、二维码签到、拍照签到等多种类型。实现方式基于 `mobilelearn.chaoxing.com` 的课堂签到API体系，与现有 `office.chaoxing.com` 的座位签到API相互独立。

## 当前状态分析

### 现有项目架构
- **后端**: Python Flask，提供REST API
- **前端**: Vue.js + Element Plus，单页应用
- **核心模块**: `utils/signin.py`（座位签到）、`utils/reserve.py`（座位预约）
- **API路由**: `backend/routes/signin_routes.py`（座位签到路由）
- **配置**: `config.json` 管理用户、座位、签到位置等

### 现有签到功能局限
现有 `SeatSignIn` 类仅支持图书馆座位签到（基于 `office.chaoxing.com`），无法处理课堂签到（基于 `mobilelearn.chaoxing.com`）。两者API体系完全不同：
- 座位签到使用 `reserveId` + 座位信息
- 课堂签到使用 `activeId` + 课程信息 + 多种签到类型

### 用户提供的线索
- 课堂签到页面URL: `https://x.chaoxing.com/course/begin?connectCode=6137...`
- 签到活动API: `GET /widget/sign/getMoreUserAttendList?activeId=21101999...`
- 二维码每10秒自动刷新
- Cookie包含 `vc3`, `uf`, `p_auth_token`, `UID` 等关键字段

## 变更方案

### 1. 新增课堂签到核心模块

**文件**: `utils/class_signin.py`

**功能**:
- 登录超星获取Cookie（复用现有AES加密）
- 获取用户课程列表（`mooc1-api.chaoxing.com/mycourse/backclazzdata`）
- 获取课程活动列表，筛选进行中的签到活动（`activeType=2, status=1`）
- 支持多种签到类型：普通、位置、手势、二维码、拍照
- 二维码内容解析（提取 `activeId` 和 `enc/signCode`）
- 自动签到：定时轮询检测新签到活动并自动完成

**关键API**:
```
登录: POST https://passport2-api.chaoxing.com/v11/loginregister
课程: GET  https://mooc1-api.chaoxing.com/mycourse/backclazzdata
活动: GET  https://mobilelearn.chaoxing.com/ppt/activeAPI/taskactivelist
签到: GET  https://mobilelearn.chaoxing.com/pptSign/stuSignajax
```

**实现要点**:
- 使用 `requests.Session` 管理Cookie
- 复用现有 `utils/encrypt.py` 的AES加密登录
- 请求间隔至少2秒，避免触发频率限制
- 双接口备用（新版失败切换旧版）

### 2. 新增课堂签到API路由

**文件**: `backend/routes/class_signin_routes.py`

**路由设计**:
| 路由 | 方法 | 功能 |
|------|------|------|
| `/api/class/signin/login` | POST | 测试登录并返回Cookie状态 |
| `/api/class/signin/courses` | GET/POST | 获取用户课程列表 |
| `/api/class/signin/activities` | GET/POST | 获取指定课程的签到活动 |
| `/api/class/signin/execute` | POST | 执行课堂签到 |
| `/api/class/signin/qrcode/decode` | POST | 解析二维码内容 |
| `/api/class/signin/auto/start` | POST | 启动自动签到监控 |
| `/api/class/signin/auto/stop` | POST | 停止自动签到监控 |
| `/api/class/signin/auto/status` | GET | 查询自动签到状态 |

**请求/响应格式**: 统一使用JSON，与现有API风格一致。

### 3. 扩展配置文件

**文件**: `config.template.json`

**新增 `class_signin` 配置段**:
```json
{
  "signin": { ... },
  "reserve": [ ... ],
  "class_signin": {
    "enabled": true,
    "check_interval": 60,
    "location": {
      "latitude": 30.0,
      "longitude": 120.0,
      "address": "教学楼"
    },
    "accounts": [
      {
        "username": "手机号",
        "password": "密码",
        "auto_sign": true,
        "courses": []
      }
    ]
  }
}
```

### 4. 注册新路由

**文件**: `backend/app.py`

**变更**: 导入并注册 `class_signin_bp`:
```python
from routes.class_signin_routes import class_signin_bp
app.register_blueprint(class_signin_bp)
```

### 5. 项目副本建立

**操作**: 将当前项目完整复制到指定位置（用户指定或默认副本目录），在副本上进行所有开发操作，确保原项目不受影响。

## 假设与决策

1. **Cookie有效期**: 假设 `vc3` 等Cookie有效期约30天，实现自动登录刷新机制
2. **签到类型优先级**: 默认支持所有签到类型，用户可在配置中指定优先策略
3. **二维码解析**: 二维码内容可能包含URL或纯文本，需支持两种格式解析
4. **自动签到策略**: 每 `check_interval` 秒轮询一次活动列表，发现新签到立即执行
5. **位置签到**: 如需位置签到，复用现有 `signin.location` 配置或单独配置 `class_signin.location`
6. **多账号支持**: 每个账号独立Session，避免Cookie冲突
7. **错误处理**: 签到失败时记录日志并返回详细错误信息，不自动重试（避免频繁请求）

## 验证步骤

1. **单元测试**: 测试 `ClassSignIn` 类的登录、获取课程、获取活动、签到方法
2. **API测试**: 使用Postman或curl测试所有新API路由
3. **二维码解析测试**: 使用真实二维码内容测试解析功能
4. **自动签到测试**: 启动自动签到，验证能否检测到新活动并完成签到
5. **集成测试**: 端到端测试完整流程（登录 -> 获取课程 -> 检测活动 -> 签到）
