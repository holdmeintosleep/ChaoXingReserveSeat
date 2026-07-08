#!/usr/bin/env python3
import os
import sys
import json
import logging
import logging.handlers
import csv
from datetime import datetime, timedelta
from enum import Enum

LOG_FILE = "chaoxing_seat.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  
MAX_BACKUP_COUNT = 5


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogCategory(Enum):
    RESERVE = "reserve"
    SIGNIN = "signin"
    SIGNOUT = "signout"
    SCHEDULER = "scheduler"
    SYSTEM = "system"
    API = "api"


class SeatLogger:
    def __init__(self, log_file=LOG_FILE, level=logging.INFO):
        self.log_file = log_file
        self._setup_logger(level)
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def _setup_logger(self, level):
        self.logger = logging.getLogger("chaoxing_seat")
        self.logger.setLevel(level)
        self.logger.propagate = False

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(category)s - %(message)s"
        )

        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=MAX_BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _log(self, level, category, message, **kwargs):
        extra = {"category": category.value}
        extra.update(kwargs)
        self.logger.log(level.value, message, extra=extra)

    def debug(self, category, message, **kwargs):
        self._log(LogLevel.DEBUG, category, message, **kwargs)

    def info(self, category, message, **kwargs):
        self._log(LogLevel.INFO, category, message, **kwargs)

    def warning(self, category, message, **kwargs):
        self._log(LogLevel.WARNING, category, message, **kwargs)

    def error(self, category, message, **kwargs):
        self._log(LogLevel.ERROR, category, message, **kwargs)

    def critical(self, category, message, **kwargs):
        self._log(LogLevel.CRITICAL, category, message, **kwargs)

    def get_log_files(self):
        files = [self.log_file]
        for i in range(1, MAX_BACKUP_COUNT + 1):
            backup_file = f"{self.log_file}.{i}"
            if os.path.exists(backup_file):
                files.append(backup_file)
        return files

    def read_logs(self, since=None, until=None, level=None, category=None, limit=None):
        logs = []
        log_files = self.get_log_files()

        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            parts = line.split(" - ", 3)
                            if len(parts) >= 4:
                                log_time_str = parts[0]
                                log_level = parts[1]
                                log_category = parts[2]
                                log_message = parts[3]

                                try:
                                    log_time = datetime.strptime(log_time_str, "%Y-%m-%d %H:%M:%S,%f")
                                except:
                                    try:
                                        log_time = datetime.strptime(log_time_str, "%Y-%m-%d %H:%M:%S")
                                    except:
                                        continue

                                if since and log_time < since:
                                    continue
                                if until and log_time > until:
                                    continue
                                if level and log_level != level:
                                    continue
                                if category and log_category != category:
                                    continue

                                logs.append({
                                    "time": log_time_str,
                                    "level": log_level,
                                    "category": log_category,
                                    "message": log_message
                                })
                        except Exception:
                            continue
            except Exception:
                continue

        logs.sort(key=lambda x: x["time"], reverse=True)

        if limit:
            logs = logs[:limit]

        return logs

    def export_logs(self, export_file, since=None, until=None, level=None, category=None, format="json"):
        logs = self.read_logs(since=since, until=until, level=level, category=category)

        if format == "json":
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump({"logs": logs, "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, f, indent=2, ensure_ascii=False)
        elif format == "csv":
            with open(export_file, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["时间", "级别", "分类", "消息"])
                for log in logs:
                    writer.writerow([log["time"], log["level"], log["category"], log["message"]])
        else:
            with open(export_file, "w", encoding="utf-8") as f:
                for log in logs:
                    f.write(f"{log['time']} - {log['level']} - {log['category']} - {log['message']}\n")

        return len(logs)

    def get_stats(self, days=7):
        since = datetime.now() - timedelta(days=days)
        logs = self.read_logs(since=since)

        stats = {
            "total": len(logs),
            "by_level": {},
            "by_category": {},
            "by_day": {}
        }

        for log in logs:
            level = log["level"]
            category = log["category"]
            log_time = log["time"]
            day = log_time.split()[0]

            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            stats["by_day"][day] = stats["by_day"].get(day, 0) + 1

        return stats

    def clear_old_logs(self, days_to_keep=30):
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleared_count = 0

        log_files = self.get_log_files()
        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                with open(log_file, "w", encoding="utf-8") as f:
                    for line in lines:
                        try:
                            log_time_str = line.split(" - ")[0]
                            log_time = datetime.strptime(log_time_str, "%Y-%m-%d %H:%M:%S,%f")
                            if log_time >= cutoff_date:
                                f.write(line)
                            else:
                                cleared_count += 1
                        except:
                            f.write(line)
            except Exception:
                continue

        return cleared_count


def main():
    import argparse
    parser = argparse.ArgumentParser(description="日志管理工具")
    parser.add_argument("--action", choices=["view", "export", "stats", "clear"], default="view", help="操作")
    parser.add_argument("--since", help="开始时间 (格式: YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--until", help="结束时间 (格式: YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="日志级别")
    parser.add_argument("--category", choices=[c.value for c in LogCategory], help="日志分类")
    parser.add_argument("--limit", type=int, help="显示条数")
    parser.add_argument("--export-file", help="导出文件名")
    parser.add_argument("--format", choices=["json", "csv", "txt"], default="json", help="导出格式")
    parser.add_argument("--days", type=int, default=7, help="统计天数")

    args = parser.parse_args()

    logger = SeatLogger()

    since = None
    if args.since:
        try:
            since = datetime.strptime(args.since, "%Y-%m-%d %H:%M:%S")
        except:
            print("时间格式错误")
            return

    until = None
    if args.until:
        try:
            until = datetime.strptime(args.until, "%Y-%m-%d %H:%M:%S")
        except:
            print("时间格式错误")
            return

    if args.action == "view":
        logs = logger.read_logs(since=since, until=until, level=args.level, category=args.category, limit=args.limit)
        for log in logs:
            print(f"{log['time']} - {log['level']} - {log['category']} - {log['message']}")

    elif args.action == "export":
        if not args.export_file:
            print("需要指定 --export-file")
            return
        count = logger.export_logs(args.export_file, since=since, until=until, level=args.level, category=args.category, format=args.format)
        print(f"已导出 {count} 条日志到 {args.export_file}")

    elif args.action == "stats":
        stats = logger.get_stats(days=args.days)
        print(json.dumps(stats, indent=2, ensure_ascii=False))

    elif args.action == "clear":
        count = logger.clear_old_logs(days_to_keep=args.days)
        print(f"已清除 {count} 条过期日志")


if __name__ == "__main__":
    main()