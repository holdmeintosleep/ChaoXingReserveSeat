"""
预约ID管理器

负责预约ID的存储、读取和过期清理。
支持多用户、多日期、多时间段的预约ID管理。

存储格式:
{
    "username": {
        "2024-01-01": {
            "10:30-14:15": "184613190",
            "14:30-18:15": "184613191"
        }
    }
}
"""

import json
import os
import logging
from datetime import datetime, timedelta


class ReservationManager:
    def __init__(self, data_dir: str = None):
        """
        Args:
            data_dir: 数据存储目录，默认为项目根目录
        """
        if data_dir is None:
            data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_file = os.path.join(data_dir, "reservations.json")
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """确保数据文件存在，不存在则创建空文件"""
        if not os.path.exists(self.data_file):
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load_data(self):
        """加载预约数据"""
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_data(self, data):
        """保存预约数据"""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_reservation(self, username: str, date: str, time_segment: str, reserve_id: str):
        """
        保存预约ID
        
        Args:
            username: 用户名
            date: 预约日期 (格式: YYYY-MM-DD)
            time_segment: 时间段 (格式: HH:MM-HH:MM)
            reserve_id: 预约ID
        """
        data = self._load_data()
        
        if username not in data:
            data[username] = {}
        if date not in data[username]:
            data[username][date] = {}
        
        data[username][date][time_segment] = reserve_id
        self._save_data(data)
        
        logging.info(f"预约ID已保存: {username} | {date} | {time_segment} | {reserve_id}")

    def get_reservation(self, username: str, date: str = None, time_segment: str = None):
        """
        获取预约ID
        
        Args:
            username: 用户名
            date: 预约日期，默认为今天
            time_segment: 时间段，可选
        
        Returns:
            str: 预约ID，如果找不到返回空字符串
        """
        data = self._load_data()
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if username not in data:
            return ""
        if date not in data[username]:
            return ""
        
        # 如果指定了时间段，返回对应ID
        if time_segment:
            return data[username][date].get(time_segment, "")
        
        # 如果没有指定时间段，返回任意一个预约ID
        ids = list(data[username][date].values())
        return ids[0] if ids else ""

    def get_all_reservations(self, username: str = None):
        """
        获取所有预约信息
        
        Args:
            username: 用户名，可选，不指定则返回所有用户
        
        Returns:
            dict: 预约信息
        """
        data = self._load_data()
        
        if username:
            return data.get(username, {})
        return data

    def delete_reservation(self, username: str, date: str, time_segment: str):
        """
        删除指定的预约ID
        
        Args:
            username: 用户名
            date: 预约日期
            time_segment: 时间段
        """
        data = self._load_data()
        
        if username in data and date in data[username]:
            if time_segment in data[username][date]:
                del data[username][date][time_segment]
                # 如果该日期下没有预约了，删除日期条目
                if not data[username][date]:
                    del data[username][date]
                # 如果该用户下没有预约了，删除用户条目
                if not data[username]:
                    del data[username]
                self._save_data(data)
                logging.info(f"预约ID已删除: {username} | {date} | {time_segment}")

    def clean_expired(self, days_to_keep: int = 7):
        """
        清理过期的预约记录
        
        Args:
            days_to_keep: 保留天数，超过此天数的记录将被删除
        """
        data = self._load_data()
        today = datetime.now().date()
        expired_date = today - timedelta(days=days_to_keep)
        
        cleaned = False
        for username in list(data.keys()):
            for date in list(data[username].keys()):
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                    if date_obj < expired_date:
                        del data[username][date]
                        cleaned = True
                        logging.info(f"已清理过期预约: {username} | {date}")
                except ValueError:
                    # 日期格式错误，也删除
                    del data[username][date]
                    cleaned = True
            
            # 如果用户没有预约了，删除用户条目
            if not data[username]:
                del data[username]
        
        if cleaned:
            self._save_data(data)

    def clear_all(self):
        """清空所有预约记录"""
        self._save_data({})
        logging.info("所有预约记录已清空")