#!/usr/bin/env python3
"""
公共工具函数模块
提供北京时区时间处理、网络检查等通用功能
"""
import urllib.request
from datetime import datetime, timezone, timedelta

# 北京时区 UTC+8
BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now():
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)


def beijing_date_str(fmt="%Y-%m-%d"):
    """获取当前北京日期字符串"""
    return beijing_now().strftime(fmt)


def beijing_dayofweek():
    """获取当前北京星期几（英文全名）"""
    return beijing_now().strftime("%A")


def check_network(test_url="http://www.baidu.com", timeout=5):
    """检查网络连接是否可用"""
    try:
        urllib.request.urlopen(test_url, timeout=timeout)
        return True
    except Exception:
        return False


def load_json_file(filepath, default=None):
    """安全加载JSON文件"""
    import json
    import os
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json_file(filepath, data):
    """安全保存JSON文件"""
    import json
    import os
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)