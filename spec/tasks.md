# 超星座位自动签到 - 实现计划

## [x] Task 1: 创建预约ID管理工具类
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 创建 ReservationManager 类，负责预约ID的存储、读取和过期清理
  - 使用JSON文件存储预约信息，包含用户、日期、时间段、预约ID等字段
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-1.1: 保存预约ID后能正确读取
  - `programmatic` TR-1.2: 过期的预约ID自动清理
- **Notes**: 存储格式: {username: {date: {time_segment: reserve_id}}}

## [x] Task 2: 修改预约模块，预约成功后保存预约ID
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 修改 reserve.py 中的 get_submit 方法
  - 当预约成功时，解析响应获取预约ID并保存
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-2.1: 预约成功后reservations.json包含正确的预约ID
  - `programmatic` TR-2.2: 预约失败时不保存任何数据

## [x] Task 3: 修改签到模块，自动读取预约ID
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 修改 signin.py 中的 segmented_signin 方法
  - 优先使用配置中的reserveId，其次从reservations.json读取
- **Acceptance Criteria Addressed**: AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-3.1: 配置中有reserveId时优先使用
  - `programmatic` TR-3.2: 配置中无reserveId时自动读取保存的预约ID

## [x] Task 4: 更新配置文件，移除手动填写的reserveId
- **Priority**: P1
- **Depends On**: Task 3
- **Description**: 
  - 更新config.json，移除手动配置的reserveId
  - 添加自动获取预约ID的说明
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `human-judgement` TR-4.1: 配置文件清晰易懂

## [x] Task 5: 测试完整流程
- **Priority**: P1
- **Depends On**: Task 1-4
- **Description**: 
  - 测试预约→保存预约ID→签到的完整流程
  - 验证手动填写和自动获取两种模式都能正常工作
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-5.1: 完整流程测试通过
  - `human-judgement` TR-5.2: 用户体验良好