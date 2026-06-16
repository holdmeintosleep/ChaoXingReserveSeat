# 超星座位自动签到 - 自动获取预约ID功能

## Overview
- **Summary**: 实现自动获取预约ID功能，在自动预约成功后保存预约ID，签到时自动读取使用，无需手动填写
- **Purpose**: 解决用户需要手动填写reserveId的问题，实现预约和签到的无缝衔接
- **Target Users**: 使用超星座位预约系统的学生和教职工

## Goals
- [x] 在自动预约成功后自动保存预约ID
- [x] 签到时自动读取保存的预约ID进行签到
- [x] 支持多用户、多时间段的预约ID管理
- [x] 提供手动填写和自动获取两种模式

## Non-Goals (Out of Scope)
- 不修改超星服务器端逻辑
- 不支持第三方预约平台

## Background & Context
- 当前签到模块需要手动配置reserveId才能正常工作
- 预约模块成功预约后，服务器会返回预约ID
- 需要在预约和签到之间建立数据传递机制

## Functional Requirements
- **FR-1**: 预约成功后自动保存预约ID到本地文件
- **FR-2**: 签到时优先读取本地保存的预约ID
- **FR-3**: 支持按用户、日期、时间段区分不同的预约ID
- **FR-4**: 提供手动填写预约ID的备用方案

## Non-Functional Requirements
- **NFR-1**: 预约ID存储文件使用JSON格式，便于阅读和编辑
- **NFR-2**: 自动过期机制，过期的预约ID自动清理

## Constraints
- **Technical**: Python 3.8+, requests库
- **Dependencies**: 依赖现有的reserve和signin模块

## Assumptions
- 用户已经配置好自动预约功能
- 预约和签到使用相同的用户凭证

## Acceptance Criteria

### AC-1: 预约成功后自动保存预约ID
- **Given**: 用户执行自动预约并成功
- **When**: 预约请求返回success=true
- **Then**: 预约ID被保存到reservations.json文件
- **Verification**: `programmatic`

### AC-2: 签到时自动使用保存的预约ID
- **Given**: 用户已成功预约并保存了预约ID
- **When**: 用户执行签到命令
- **Then**: 系统自动读取预约ID并完成签到
- **Verification**: `programmatic`

### AC-3: 手动填写预约ID作为备用方案
- **Given**: 用户在config.json中手动配置了reserveId
- **When**: 用户执行签到命令
- **Then**: 系统优先使用手动配置的reserveId
- **Verification**: `programmatic`