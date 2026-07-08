# 预约与签到功能扩展方案

## 一、现有系统分析

### 已具备的能力
| 模块 | 能力 | 关键文件 |
|------|------|---------|
| 配置管理 | 可视化增删改查预约配置 | `ConfigForm.vue`, `ConfigList.vue`, `config_routes.py` |
| 预约执行 | `reserve` 类可登录、获取token、提交预约 | `utils/reserve.py` |
| 签到执行 | `SeatSignIn` 类可通过 reserveId 签到 | `utils/signin.py` |
| 预约ID管理 | `ReservationManager` 保存/读取预约ID | `utils/reservation_manager.py` |

### 缺失的能力
- **前端没有预约执行入口**：配置表单只管理config.json，不触发实际预约
- **前端没有签到入口**：签到逻辑存在于后端，但无前端界面
- **预约记录不可视**：`reservations.json` 中的预约记录无前端展示

## 二、技术方案

### 2.1 后端新增 API

**预约模块** (`backend/routes/reservation_routes.py`)：
| 方法 | 路由 | 功能 |
|------|------|------|
| POST | `/api/reservation/execute` | 执行预约（调用 `reserve` 类） |
| GET | `/api/reservation/history` | 获取预约历史记录 |
| DELETE | `/api/reservation/history` | 清除预约记录 |
| GET | `/api/reservation/status` | 获取预约执行状态 |

**签到模块** (`backend/routes/signin_routes.py`)：
| 方法 | 路由 | 功能 |
|------|------|------|
| POST | `/api/signin/execute` | 执行签到（通过 reserve_id） |
| GET | `/api/signin/status` | 获取签到状态 |
| POST | `/api/signin/cancel` | 取消签到 |

### 2.2 前端新增组件

**ReservationPanel.vue** - 预约管理面板：
- 展示所有配置列表，每项配有"立即预约"按钮
- 预约执行状态实时反馈（进行中/成功/失败）
- 预约历史记录表格展示

**SignInPanel.vue** - 签到管理面板：
- 展示预约记录列表（从 `reservations.json` 读取）
- 每条记录配有"签到"按钮
- 签到结果实时反馈

### 2.3 App.vue 改造

将现有单页面改为 Tab 页签导航：
- **配置管理** Tab：现有的 ConfigList + RuleDisplay
- **预约管理** Tab：新增 ReservationPanel
- **签到管理** Tab：新增 SignInPanel

## 三、实施步骤

1. 创建 `backend/routes/reservation_routes.py` - 预约执行API
2. 创建 `backend/routes/signin_routes.py` - 签到执行API
3. 修改 `backend/app.py` - 注册新路由
4. 创建 `frontend/src/components/ReservationPanel.vue`
5. 创建 `frontend/src/components/SignInPanel.vue`
6. 修改 `frontend/src/App.vue` - 添加Tab导航
7. 修改 `frontend/src/api/config.js` - 添加新API调用
8. 构建前端并验证

## 四、风险与注意事项

- 预约执行是异步操作，需要处理超时
- 签到需要有效的登录session，需复用 `reserve.py` 的登录逻辑
- `reserve.py` 中的 `submit` 方法包含滑块验证，需在配置中启用 `ENABLE_SLIDER`
- 前端需展示预约/签到的实时状态反馈