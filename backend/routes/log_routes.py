"""
日志管理API路由
提供日志查询、导出等功能
"""
from flask import Blueprint, request, jsonify, send_file
import os
import sys
import datetime
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import SeatLogger, LogCategory

log_bp = Blueprint('log', __name__)


@log_bp.route('/api/logs', methods=['GET'])
def get_logs():
    """查询日志"""
    since_str = request.args.get('since')
    until_str = request.args.get('until')
    level = request.args.get('level')
    category = request.args.get('category')
    limit = request.args.get('limit', type=int)

    logger = SeatLogger()

    since = None
    if since_str:
        try:
            since = datetime.datetime.strptime(since_str, "%Y-%m-%d %H:%M:%S")
        except:
            return jsonify({"success": False, "message": "时间格式错误"}), 400

    until = None
    if until_str:
        try:
            until = datetime.datetime.strptime(until_str, "%Y-%m-%d %H:%M:%S")
        except:
            return jsonify({"success": False, "message": "时间格式错误"}), 400

    logs = logger.read_logs(since=since, until=until, level=level, category=category, limit=limit)

    return jsonify({"success": True, "data": logs})


@log_bp.route('/api/logs/export', methods=['POST'])
def export_logs():
    """导出日志"""
    data = request.get_json() or {}
    since_str = data.get('since')
    until_str = data.get('until')
    level = data.get('level')
    category = data.get('category')
    format = data.get('format', 'json')

    logger = SeatLogger()

    since = None
    if since_str:
        try:
            since = datetime.datetime.strptime(since_str, "%Y-%m-%d %H:%M:%S")
        except:
            return jsonify({"success": False, "message": "时间格式错误"}), 400

    until = None
    if until_str:
        try:
            until = datetime.datetime.strptime(until_str, "%Y-%m-%d %H:%M:%S")
        except:
            return jsonify({"success": False, "message": "时间格式错误"}), 400

    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format}', delete=False, encoding='utf-8') as f:
        export_file = f.name

    try:
        count = logger.export_logs(export_file, since=since, until=until, level=level, category=category, format=format)

        if format == 'json':
            mimetype = 'application/json'
        elif format == 'csv':
            mimetype = 'text/csv'
        else:
            mimetype = 'text/plain'

        return send_file(
            export_file,
            mimetype=mimetype,
            as_attachment=True,
            download_name=f'logs.{format}'
        )
    finally:
        if os.path.exists(export_file):
            os.unlink(export_file)


@log_bp.route('/api/logs/stats', methods=['GET'])
def get_log_stats():
    """获取日志统计"""
    days = request.args.get('days', default=7, type=int)
    logger = SeatLogger()
    stats = logger.get_stats(days=days)
    return jsonify({"success": True, "data": stats})


@log_bp.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """清除过期日志"""
    data = request.get_json() or {}
    days_to_keep = data.get('days_to_keep', 30)
    logger = SeatLogger()
    count = logger.clear_old_logs(days_to_keep=days_to_keep)
    return jsonify({"success": True, "message": f"已清除 {count} 条过期日志"})