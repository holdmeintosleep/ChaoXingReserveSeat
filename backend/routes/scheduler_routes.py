"""
定时任务调度API路由
提供任务调度、查询、取消等功能
"""
from flask import Blueprint, request, jsonify
import os
import sys
import json
import datetime
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scheduler import TaskScheduler, TaskType, TaskStatus

scheduler_bp = Blueprint('scheduler', __name__)

_scheduler = None


def _get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler(auto_load=True)
    return _scheduler


def _beijing_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))


@scheduler_bp.route('/api/scheduler/tasks', methods=['GET'])
def get_tasks():
    """获取所有任务列表"""
    scheduler = _get_scheduler()
    status_filter = request.args.get('status')
    
    if status_filter:
        tasks = scheduler.get_tasks(status=status_filter)
    else:
        tasks = scheduler.get_tasks()
    
    return jsonify({
        "success": True,
        "data": [t.__dict__() for t in tasks]
    })


@scheduler_bp.route('/api/scheduler/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取单个任务详情"""
    scheduler = _get_scheduler()
    tasks = scheduler.get_tasks()
    
    for task in tasks:
        if task.task_id == task_id:
            return jsonify({"success": True, "data": task.__dict__()})
    
    return jsonify({"success": False, "message": "任务不存在"}), 404


@scheduler_bp.route('/api/scheduler/tasks', methods=['POST'])
def create_task():
    """创建定时任务"""
    data = request.get_json() or {}
    task_type = data.get("task_type")
    config_index = data.get("config_index")
    target_time_str = data.get("target_time")
    advance_threshold = data.get("advance_threshold", 0)
    delay_threshold = data.get("delay_threshold", 0)

    if not task_type or config_index is None:
        return jsonify({"success": False, "message": "缺少必要参数"}), 400

    try:
        scheduler = _get_scheduler()

        if task_type == "reserve":
            task = scheduler.schedule_reservation(config_index)
        elif task_type == "signin":
            if not target_time_str:
                return jsonify({"success": False, "message": "签到任务需要target_time"}), 400
            target_time = datetime.datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
            task = scheduler.schedule_signin(config_index, target_time, advance_threshold)
        elif task_type == "signout":
            if not target_time_str:
                return jsonify({"success": False, "message": "签退任务需要target_time"}), 400
            target_time = datetime.datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
            task = scheduler.schedule_signout(config_index, target_time, delay_threshold)
        else:
            return jsonify({"success": False, "message": "未知任务类型"}), 400

        return jsonify({
            "success": True,
            "message": "任务创建成功",
            "data": task.__dict__()
        })

    except Exception as e:
        logging.error(f"创建任务失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@scheduler_bp.route('/api/scheduler/tasks/<task_id>', methods=['DELETE'])
def cancel_task(task_id):
    """取消任务"""
    scheduler = _get_scheduler()
    success = scheduler.cancel_task(task_id)
    
    if success:
        return jsonify({"success": True, "message": "任务已取消"})
    return jsonify({"success": False, "message": "任务取消失败（任务不存在或已执行）"}), 400


@scheduler_bp.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """启动调度器"""
    import threading
    
    def run_scheduler():
        scheduler = _get_scheduler()
        scheduler.run()
    
    if _scheduler and _scheduler.running:
        return jsonify({"success": False, "message": "调度器已在运行"}), 400

    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    
    return jsonify({"success": True, "message": "调度器已启动"})


@scheduler_bp.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """停止调度器"""
    scheduler = _get_scheduler()
    
    if not scheduler.running:
        return jsonify({"success": False, "message": "调度器未在运行"}), 400

    scheduler.stop()
    return jsonify({"success": True, "message": "调度器已停止"})


@scheduler_bp.route('/api/scheduler/status', methods=['GET'])
def scheduler_status():
    """获取调度器状态"""
    scheduler = _get_scheduler()
    
    return jsonify({
        "success": True,
        "data": {
            "running": scheduler.running,
            "task_count": len(scheduler.get_tasks())
        }
    })


@scheduler_bp.route('/api/scheduler/auto_schedule', methods=['POST'])
def auto_schedule():
    """根据配置自动生成今日任务"""
    data = request.get_json() or {}
    config_index = data.get("config_index")
    
    from backend.bputils.config_manager import ConfigManager
    
    config_manager = ConfigManager()
    configs = config_manager.get_all_reserve_configs()
    
    if config_index is not None:
        if config_index < 0 or config_index >= len(configs):
            return jsonify({"success": False, "message": "配置索引不存在"}), 400
        target_configs = [configs[config_index]]
    else:
        target_configs = configs

    scheduler = _get_scheduler()
    created_tasks = []
    today = _beijing_now().date()
    
    for cfg in target_configs:
        username = cfg.get("username", "")
        times = cfg.get("time", [])
        daysofweek = cfg.get("daysofweek", [])
        cfg_index = configs.index(cfg)
        
        current_day = _beijing_now().strftime("%A")
        if current_day not in daysofweek:
            continue

        try:
            reserve_task = scheduler.schedule_reservation(cfg_index, today)
            created_tasks.append({
                "type": "reserve",
                "task": reserve_task.__dict__()
            })

            if len(times) >= 2:
                start_time_str = times[0]
                end_time_str = times[1]
                
                start_datetime = datetime.datetime.strptime(start_time_str, "%H:%M").time()
                end_datetime = datetime.datetime.strptime(end_time_str, "%H:%M").time()
                
                signin_time = datetime.datetime.combine(today, start_datetime)
                signout_time = datetime.datetime.combine(today, end_datetime)
                
                signin_task = scheduler.schedule_signin(cfg_index, signin_time)
                signout_task = scheduler.schedule_signout(cfg_index, signout_time)
                
                created_tasks.append({
                    "type": "signin",
                    "task": signin_task.__dict__()
                })
                created_tasks.append({
                    "type": "signout",
                    "task": signout_task.__dict__()
                })

        except Exception as e:
            logging.error(f"为用户 {username} 创建任务失败: {e}")

    return jsonify({
        "success": True,
        "message": f"已创建 {len(created_tasks)} 个任务",
        "data": created_tasks
    })