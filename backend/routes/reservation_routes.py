"""
预约执行API路由
提供预约执行、历史记录查询等功能
"""
from flask import Blueprint, request, jsonify
import os
import sys
import json
import threading
import logging
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.reserve import reserve, get_date
from utils.reservation_manager import ReservationManager
from bputils.path_utils import get_config_path

reservation_bp = Blueprint('reservation', __name__)
reservation_manager = ReservationManager()

_execution_status = {}


def _beijing_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))


def _beijing_dayofweek():
    return _beijing_now().strftime("%A")


@reservation_bp.route('/api/reservation/execute', methods=['POST'])
def execute_reservation():
    """
    执行预约操作
    请求体: { "config_index": 0 }  或 { "config_index": "all" }
    """
    data = request.get_json() or {}
    config_index = data.get("config_index")

    config_path = get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    reserve_configs = config.get("reserve", [])

    if config_index == "all":
        targets = list(range(len(reserve_configs)))
    elif isinstance(config_index, int) and 0 <= config_index < len(reserve_configs):
        targets = [config_index]
    else:
        return jsonify({"success": False, "message": "无效的配置索引"}), 400

    current_day = _beijing_dayofweek()
    valid_targets = []
    for idx in targets:
        cfg = reserve_configs[idx]
        if current_day in cfg.get("daysofweek", []):
            valid_targets.append(idx)

    if not valid_targets:
        return jsonify({
            "success": False,
            "message": f"今天({current_day})不在任何配置的预约日内"
        }), 400

    task_id = f"reserve_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    _execution_status[task_id] = {
        "status": "running",
        "results": [],
        "total": len(valid_targets),
        "completed": 0
    }

    def _do_reserve():
        results = []
        for idx in valid_targets:
            cfg = reserve_configs[idx]
            username = cfg.get("username", "")
            password = cfg.get("password", "")
            times = cfg.get("time", [])
            roomid = str(cfg.get("roomid", ""))
            seatids = cfg.get("seatid", [])

            if isinstance(seatids, str):
                seatids = [seatids]

            result = {
                "username": username,
                "time": times,
                "roomid": roomid,
                "seatid": seatids,
                "success": False,
                "message": ""
            }

            try:
                s = reserve(
                    sleep_time=0.2,
                    max_attempt=5,
                    enable_slider=True,
                    reserve_next_day=False,
                )
                s.get_login_status()
                login_ok, login_msg = s.login(username, password)
                if not login_ok:
                    result["message"] = f"登录失败: {login_msg}"
                    results.append(result)
                    _execution_status[task_id]["completed"] += 1
                    continue

                s.requests.headers.update({"Host": "office.chaoxing.com"})
                suc = s.submit(times, roomid, seatids, False, username)
                result["success"] = suc
                result["message"] = "预约成功" if suc else "预约失败"

                if suc:
                    today = get_date(0)
                    time_segment = f"{times[0]}-{times[1]}"
                    for seat in seatids:
                        rm = ReservationManager()
                        auto_id = rm.get_reservation(username, today, time_segment)
                        if auto_id:
                            result["reserve_id"] = auto_id
                            break

            except Exception as e:
                result["message"] = f"执行异常: {str(e)}"
                logging.error(f"预约执行异常: {e}")

            results.append(result)
            _execution_status[task_id]["completed"] += 1

        _execution_status[task_id]["status"] = "done"
        _execution_status[task_id]["results"] = results

    thread = threading.Thread(target=_do_reserve, daemon=True)
    thread.start()

    return jsonify({
        "success": True,
        "message": "预约任务已启动",
        "task_id": task_id,
        "configs": len(valid_targets)
    })


@reservation_bp.route('/api/reservation/status/<task_id>', methods=['GET'])
def reservation_status(task_id):
    """获取预约执行状态"""
    status = _execution_status.get(task_id)
    if not status:
        return jsonify({"success": False, "message": "任务不存在"}), 404
    return jsonify({"success": True, "data": status})


@reservation_bp.route('/api/reservation/history', methods=['GET'])
def reservation_history():
    """获取预约历史记录"""
    username = request.args.get("username")
    data = reservation_manager.get_all_reservations(username)
    return jsonify({"success": True, "data": data})


@reservation_bp.route('/api/reservation/history', methods=['DELETE'])
def clear_reservation_history():
    """清除预约历史记录"""
    username = request.args.get("username")
    if username:
        data = reservation_manager._load_data()
        if username in data:
            del data[username]
            reservation_manager._save_data(data)
        return jsonify({"success": True, "message": f"已清除 {username} 的预约记录"})
    else:
        reservation_manager.clear_all()
        return jsonify({"success": True, "message": "已清除所有预约记录"})