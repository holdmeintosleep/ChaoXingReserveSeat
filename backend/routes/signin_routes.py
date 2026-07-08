"""
签到执行API路由
提供通过reserve_id签到、取消签到、状态查询等功能
"""
from flask import Blueprint, request, jsonify
import os
import sys
import json
import logging
import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.signin import SeatSignIn
from utils.reservation_manager import ReservationManager

signin_bp = Blueprint('signin', __name__)
reservation_manager = ReservationManager()

# 签到执行状态存储
_signin_status = {}


def _beijing_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))


def _beijing_dayofweek():
    return _beijing_now().strftime("%A")


@signin_bp.route('/api/signin/execute', methods=['POST'])
def execute_signin():
    """
    通过预约记录ID执行签到
    请求体: {
        "username": "xxx",
        "password": "xxx",
        "reserve_id": "184613190",  // 可选，不提供则从预约记录自动获取
        "roomid": "6913",           // 可选
        "seatid": "011",            // 可选
        "date": "2024-01-01",       // 可选，默认为今天
        "time_segment": "10:30-14:15" // 可选，用于从预约记录匹配
    }
    """
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")
    reserve_id = data.get("reserve_id", "")
    roomid = str(data.get("roomid", ""))
    seatid = str(data.get("seatid", ""))

    if not username or not password:
        return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400

    # 如果没有提供reserve_id，尝试从预约记录获取
    if not reserve_id:
        date = data.get("date") or datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=8))
        ).strftime("%Y-%m-%d")
        time_segment = data.get("time_segment", "")
        reserve_id = reservation_manager.get_reservation(username, date, time_segment)
        if not reserve_id:
            return jsonify({
                "success": False,
                "message": "未找到预约ID，请提供reserve_id或确保预约记录存在"
            }), 400

    # 读取签到配置（GPS位置等）
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "config.json"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    signin_config = config.get("signin", {})
    location = signin_config.get("location", {})

    # 执行签到
    signin = SeatSignIn()
    signin.set_location(
        latitude=location.get("latitude", 30.0),
        longitude=location.get("longitude", 120.0),
        address=location.get("address", "图书馆"),
    )
    signin.get_login_status()
    login_ok, login_msg = signin.login(username, password)

    if not login_ok:
        return jsonify({
            "success": False,
            "message": f"登录失败: {login_msg}"
        }), 400

    signin.requests.headers.update({"Host": "office.chaoxing.com"})
    result = signin.signin_with_reserve_id(reserve_id, roomid, seatid)

    return jsonify({
        "success": result.get("success", False),
        "message": result.get("message", ""),
        "data": result
    })


@signin_bp.route('/api/signin/cancel', methods=['POST'])
def cancel_signin():
    """
    取消签到
    请求体: {
        "username": "xxx",
        "password": "xxx",
        "reserve_id": "184613190"
    }
    """
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")
    reserve_id = data.get("reserve_id", "")

    if not username or not password:
        return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400
    if not reserve_id:
        return jsonify({"success": False, "message": "reserve_id不能为空"}), 400

    signin = SeatSignIn()
    signin.get_login_status()
    login_ok, login_msg = signin.login(username, password)

    if not login_ok:
        return jsonify({
            "success": False,
            "message": f"登录失败: {login_msg}"
        }), 400

    signin.requests.headers.update({"Host": "office.chaoxing.com"})
    result = signin.cancel_signin(reserve_id)

    return jsonify({
        "success": result.get("success", False),
        "message": result.get("message", "")
    })


@signin_bp.route('/api/signin/status', methods=['GET'])
def signin_status():
    """
    查询签到状态
    需要提供: username, password, roomid, seatid
    """
    username = request.args.get("username", "")
    password = request.args.get("password", "")
    roomid = request.args.get("roomid", "")
    seatid = request.args.get("seatid", "")

    if not username or not password:
        return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400

    signin = SeatSignIn()
    signin.get_login_status()
    login_ok, login_msg = signin.login(username, password)

    if not login_ok:
        return jsonify({
            "success": False,
            "message": f"登录失败: {login_msg}"
        }), 400

    signin.requests.headers.update({"Host": "office.chaoxing.com"})

    if roomid and seatid:
        status = signin.check_signin_status(roomid, seatid)
    else:
        reservations = signin.get_current_reservations()
        status = {"reservations": reservations}

    return jsonify({"success": True, "data": status})


@signin_bp.route('/api/signin/batch', methods=['POST'])
def batch_signin():
    """
    批量签到：根据预约历史记录自动签到
    请求体: {
        "config_index": 0  // 使用哪个配置的账号密码登录
    }
    如果不指定config_index，则遍历所有预约记录尝试签到
    """
    data = request.get_json() or {}
    config_index = data.get("config_index")

    # 读取配置
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "config.json"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    reserve_configs = config.get("reserve", [])
    signin_config = config.get("signin", {})
    location = signin_config.get("location", {})

    # 获取所有预约记录
    all_reservations = reservation_manager.get_all_reservations()
    if not all_reservations:
        return jsonify({
            "success": False,
            "message": "没有预约记录，请先执行预约"
        }), 400

    results = []
    today = _beijing_now().strftime("%Y-%m-%d")

    for username, dates in all_reservations.items():
        # 查找匹配的配置
        cfg = None
        if config_index is not None and 0 <= config_index < len(reserve_configs):
            if reserve_configs[config_index].get("username") == username:
                cfg = reserve_configs[config_index]
        else:
            for c in reserve_configs:
                if c.get("username") == username:
                    cfg = c
                    break

        if not cfg:
            continue

        # 获取今天的预约记录
        if today not in dates:
            continue

        password = cfg.get("password", "")
        roomid = str(cfg.get("roomid", ""))

        for time_seg, reserve_id in dates[today].items():
            signin = SeatSignIn()
            signin.set_location(
                latitude=location.get("latitude", 30.0),
                longitude=location.get("longitude", 120.0),
                address=location.get("address", "图书馆"),
            )
            signin.get_login_status()
            login_ok, login_msg = signin.login(username, password)

            if not login_ok:
                results.append({
                    "username": username,
                    "time_segment": time_seg,
                    "success": False,
                    "message": f"登录失败: {login_msg}"
                })
                continue

            signin.requests.headers.update({"Host": "office.chaoxing.com"})
            result = signin.signin_with_reserve_id(reserve_id, roomid, "")
            result["username"] = username
            result["time_segment"] = time_seg
            results.append(result)

    return jsonify({
        "success": True,
        "message": f"签到完成，共处理 {len(results)} 条记录",
        "data": results
    })