import json
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)


class ConfigManager:
    def __init__(self, config_path: str = None):
        if config_path is None:
            try:
                from flask import current_app
                config_path = current_app.config.get('CONFIG_PATH')
            except Exception:
                pass
            
            if config_path is None:
                utils_dir = os.path.dirname(os.path.abspath(__file__))
                backend_dir = os.path.dirname(utils_dir)
                project_root = os.path.dirname(backend_dir)
                config_path = os.path.join(project_root, "config.json")
        
        self.config_path = config_path
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        if not os.path.exists(self.config_path):
            template_path = None
            
            try:
                from flask import current_app
                resource_path = current_app.config.get('RESOURCE_PATH')
                if resource_path:
                    template_path = os.path.join(resource_path, "config.template.json")
            except Exception:
                pass
            
            if template_path is None:
                template_path = self.config_path.replace("config.json", "config.template.json")
            
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    content = f.read()
                with open(self.config_path, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                default_config = {
                    "signin": {
                        "enabled": True,
                        "location": {
                            "latitude": 30.0,
                            "longitude": 120.0,
                            "address": "图书馆"
                        },
                        "interval": 300
                    },
                    "reserve": []
                }
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)

    def load_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"signin": {}, "reserve": []}

    def save_config(self, config):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def get_all_reserve_configs(self):
        config = self.load_config()
        return config.get("reserve", [])

    def get_reserve_config(self, index):
        configs = self.get_all_reserve_configs()
        if 0 <= index < len(configs):
            return configs[index]
        return None

    def add_reserve_config(self, config):
        full_config = self.load_config()
        full_config["reserve"].append(config)
        self.save_config(full_config)
        return len(full_config["reserve"]) - 1

    def update_reserve_config(self, index, config):
        full_config = self.load_config()
        if 0 <= index < len(full_config["reserve"]):
            full_config["reserve"][index] = config
            self.save_config(full_config)
            return True
        return False

    def delete_reserve_config(self, index):
        full_config = self.load_config()
        if 0 <= index < len(full_config["reserve"]):
            del full_config["reserve"][index]
            self.save_config(full_config)
            return True
        return False

    def validate_config(self, config):
        errors = []
        
        if not config.get("username"):
            errors.append("用户名不能为空")
        if not config.get("password"):
            errors.append("密码不能为空")
        if not config.get("time") or len(config["time"]) != 2:
            errors.append("请设置开始时间和结束时间")
        else:
            start_time = config["time"][0]
            end_time = config["time"][1]
            if not self._is_valid_time(start_time):
                errors.append(f"开始时间格式错误: {start_time}")
            if not self._is_valid_time(end_time):
                errors.append(f"结束时间格式错误: {end_time}")
            if self._is_valid_time(start_time) and self._is_valid_time(end_time):
                if not self._is_time_before(start_time, end_time):
                    errors.append("结束时间必须晚于开始时间")
                duration = self._calculate_duration(start_time, end_time)
                if duration > 4:
                    errors.append(f"预约时长不能超过4小时（当前: {duration}小时）")
        
        if not config.get("roomid"):
            errors.append("房间ID不能为空")
        if not config.get("seatid"):
            errors.append("座位号不能为空")
        if not config.get("daysofweek") or len(config["daysofweek"]) == 0:
            errors.append("请至少选择一个预约日期")
        
        return {"valid": len(errors) == 0, "errors": errors}

    def _is_valid_time(self, time_str):
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False

    def _is_time_before(self, time1, time2):
        t1 = datetime.strptime(time1, "%H:%M")
        t2 = datetime.strptime(time2, "%H:%M")
        return t1 < t2

    def _calculate_duration(self, start, end):
        t1 = datetime.strptime(start, "%H:%M")
        t2 = datetime.strptime(end, "%H:%M")
        diff = t2 - t1
        return round(diff.total_seconds() / 3600, 1)

    def get_signin_config(self):
        config = self.load_config()
        return config.get("signin", {})

    def update_signin_config(self, signin_config):
        full_config = self.load_config()
        full_config["signin"] = signin_config
        self.save_config(full_config)