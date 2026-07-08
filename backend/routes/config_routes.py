from flask import Blueprint, request, jsonify, send_file
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bputils.config_manager import ConfigManager

config_bp = Blueprint('config', __name__)
config_manager = ConfigManager()


@config_bp.route('/api/config', methods=['GET'])
def get_config():
    config = config_manager.load_config()
    return jsonify(config)


@config_bp.route('/api/config/reserve', methods=['GET'])
def get_reserve_configs():
    configs = config_manager.get_all_reserve_configs()
    return jsonify({"data": configs})


@config_bp.route('/api/config/reserve', methods=['POST'])
def add_reserve_config():
    data = request.get_json()
    validation = config_manager.validate_config(data)
    if not validation["valid"]:
        return jsonify({"success": False, "message": "配置验证失败", "errors": validation["errors"]}), 400
    
    index = config_manager.add_reserve_config(data)
    return jsonify({"success": True, "message": "添加成功", "index": index})


@config_bp.route('/api/config/reserve/<int:index>', methods=['GET'])
def get_reserve_config(index):
    config = config_manager.get_reserve_config(index)
    if config is None:
        return jsonify({"success": False, "message": "配置不存在"}), 404
    return jsonify({"data": config})


@config_bp.route('/api/config/reserve/<int:index>', methods=['PUT'])
def update_reserve_config(index):
    data = request.get_json()
    validation = config_manager.validate_config(data)
    if not validation["valid"]:
        return jsonify({"success": False, "message": "配置验证失败", "errors": validation["errors"]}), 400
    
    success = config_manager.update_reserve_config(index, data)
    if success:
        return jsonify({"success": True, "message": "更新成功"})
    return jsonify({"success": False, "message": "配置不存在"}), 404


@config_bp.route('/api/config/reserve/<int:index>', methods=['DELETE'])
def delete_reserve_config(index):
    success = config_manager.delete_reserve_config(index)
    if success:
        return jsonify({"success": True, "message": "删除成功"})
    return jsonify({"success": False, "message": "配置不存在"}), 404


@config_bp.route('/api/config/export', methods=['GET'])
def export_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    if not os.path.exists(config_path):
        return jsonify({"success": False, "message": "配置文件不存在"}), 404
    return send_file(config_path, as_attachment=True, download_name="config.json")


@config_bp.route('/api/config/validate', methods=['POST'])
def validate_config():
    data = request.get_json()
    result = config_manager.validate_config(data)
    return jsonify(result)


@config_bp.route('/api/config/signin', methods=['GET'])
def get_signin_config():
    config = config_manager.get_signin_config()
    return jsonify({"data": config})


@config_bp.route('/api/config/signin', methods=['PUT'])
def update_signin_config():
    data = request.get_json()
    config_manager.update_signin_config(data)
    return jsonify({"success": True, "message": "更新成功"})


@config_bp.route('/api/rules', methods=['GET'])
def get_rules():
    rules = {
        "reservation": {
            "title": "预约规则",
            "items": [
                {"name": "预约开始时间", "value": "提前15天的22:00"},
                {"name": "单次预约时长", "value": "4小时"},
                {"name": "座位预留时长", "value": "20分钟"},
                {"name": "每日预约次数", "value": "2次"},
                {"name": "每周预约次数", "value": "不限"},
                {"name": "暂离次数", "value": "不限"},
                {"name": "暂离时长", "value": "120分钟"}
            ]
        },
        "violation": {
            "title": "违规规则",
            "items": [
                {"name": "未按时签到", "value": "记为违约"},
                {"name": "暂离超时未返回", "value": "记为违约"},
                {"name": "每周违约达5次", "value": "暂停预约功能"}
            ]
        },
        "process": {
            "title": "使用流程",
            "steps": [
                {"step": 1, "name": "预约座位", "description": "在预约时段前选择座位进行预约"},
                {"step": 2, "name": "扫码签到", "description": "在预约开始时间后20分钟内扫码签到"},
                {"step": 3, "name": "使用完毕退座", "description": "使用完毕后点击退座"}
            ]
        }
    }
    return jsonify(rules)