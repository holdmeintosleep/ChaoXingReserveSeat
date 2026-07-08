#!/usr/bin/env python3
"""
定时任务调度器模块
提供任务调度、自动执行、恢复机制和通知功能
"""
import os
import sys
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.reserve import reserve, get_date
from utils.signin import SeatSignIn
from utils.reservation_manager import ReservationManager
from utils.common import beijing_now, beijing_date_str, beijing_dayofweek, check_network
from backend.bputils.config_manager import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("chaoxing_seat.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskType(Enum):
    RESERVE = "reserve"
    SIGNIN = "signin"
    SIGNOUT = "signout"


class ScheduledTask:
    def __init__(self, task_id, task_type, config_index, target_time,
                 advance_threshold=0, delay_threshold=0, max_retries=3):
        self.task_id = task_id
        self.task_type = task_type
        self.config_index = config_index
        self.target_time = target_time
        self.advance_threshold = advance_threshold
        self.delay_threshold = delay_threshold
        self.max_retries = max_retries
        self.status = TaskStatus.PENDING
        self.retry_count = 0
        self.last_attempt_time = None
        self.result = None
        self.error_message = None

    def __dict__(self):
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "config_index": self.config_index,
            "target_time": self.target_time.strftime("%Y-%m-%d %H:%M:%S"),
            "advance_threshold": self.advance_threshold,
            "delay_threshold": self.delay_threshold,
            "max_retries": self.max_retries,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "last_attempt_time": self.last_attempt_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_attempt_time else None,
            "result": self.result,
            "error_message": self.error_message
        }


class TaskScheduler:
    def __init__(self, auto_load=True):
        self.config_manager = ConfigManager()
        self.reservation_manager = ReservationManager()
        self.tasks = []
        self.running = False
        self._lock = threading.Lock()
        self._check_interval = 30
        self._recovery_check_interval = 60
        self._last_recovery_check = None
        self._notification_file = "notifications.json"
        if auto_load:
            self._load_tasks()

    def _load_tasks(self):
        task_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")
        if os.path.exists(task_file):
            try:
                with open(task_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for task_data in data.get("tasks", []):
                        task = ScheduledTask(
                            task_id=task_data["task_id"],
                            task_type=TaskType(task_data["task_type"]),
                            config_index=task_data["config_index"],
                            target_time=datetime.strptime(task_data["target_time"], "%Y-%m-%d %H:%M:%S"),
                            advance_threshold=task_data.get("advance_threshold", 0),
                            delay_threshold=task_data.get("delay_threshold", 0),
                            max_retries=task_data.get("max_retries", 3)
                        )
                        task.status = TaskStatus(task_data["status"])
                        task.retry_count = task_data.get("retry_count", 0)
                        task.last_attempt_time = datetime.strptime(task_data["last_attempt_time"], "%Y-%m-%d %H:%M:%S") if task_data.get("last_attempt_time") else None
                        task.result = task_data.get("result")
                        task.error_message = task_data.get("error_message")
                        self.tasks.append(task)
                    logging.info(f"已加载 {len(self.tasks)} 个任务")
            except Exception as e:
                logging.error(f"加载任务失败: {e}")

    def _save_tasks(self):
        task_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")
        try:
            data = {"tasks": [t.__dict__() for t in self.tasks]}
            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"保存任务失败: {e}")

    def _notify(self, task_id, action, status, message):
        notification = {
            "task_id": task_id,
            "action": action,
            "status": status,
            "message": message,
            "timestamp": beijing_now().strftime("%Y-%m-%d %H:%M:%S")
        }
        logging.info(f"通知: {message}")
        try:
            existing = []
            if os.path.exists(self._notification_file):
                with open(self._notification_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            existing.append(notification)
            with open(self._notification_file, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"保存通知失败: {e}")

    def _create_task_id(self, task_type, config_index):
        now = beijing_now()
        return f"{task_type.value}_{config_index}_{now.strftime('%Y%m%d_%H%M%S')}"

    def schedule_reservation(self, config_index, reserve_date=None, advance_threshold=0):
        if reserve_date is None:
            reserve_date = beijing_now().date()

        task = ScheduledTask(
            task_id=self._create_task_id(TaskType.RESERVE, config_index),
            task_type=TaskType.RESERVE,
            config_index=config_index,
            target_time=datetime.combine(reserve_date, datetime.min.time()) + timedelta(hours=22),
            advance_threshold=advance_threshold,
            max_retries=3
        )
        with self._lock:
            self.tasks.append(task)
            self._save_tasks()
        logging.info(f"已预约任务: {task.task_id}")
        return task

    def schedule_signin(self, config_index, signin_time, advance_threshold=5):
        task = ScheduledTask(
            task_id=self._create_task_id(TaskType.SIGNIN, config_index),
            task_type=TaskType.SIGNIN,
            config_index=config_index,
            target_time=signin_time,
            advance_threshold=advance_threshold,
            max_retries=3
        )
        with self._lock:
            self.tasks.append(task)
            self._save_tasks()
        logging.info(f"已预约签到任务: {task.task_id}")
        return task

    def schedule_signout(self, config_index, signout_time, delay_threshold=0):
        task = ScheduledTask(
            task_id=self._create_task_id(TaskType.SIGNOUT, config_index),
            task_type=TaskType.SIGNOUT,
            config_index=config_index,
            target_time=signout_time,
            delay_threshold=delay_threshold,
            max_retries=3
        )
        with self._lock:
            self.tasks.append(task)
            self._save_tasks()
        logging.info(f"已预约签退任务: {task.task_id}")
        return task

    def _execute_reserve(self, task):
        configs = self.config_manager.get_all_reserve_configs()
        if task.config_index < 0 or task.config_index >= len(configs):
            return False, "配置不存在"

        cfg = configs[task.config_index]
        username = cfg.get("username", "")
        password = cfg.get("password", "")
        times = cfg.get("time", [])
        roomid = str(cfg.get("roomid", ""))
        seatids = cfg.get("seatid", [])
        daysofweek = cfg.get("daysofweek", [])

        if isinstance(seatids, str):
            seatids = [seatids]

        current_day = beijing_dayofweek()
        if current_day not in daysofweek:
            return False, f"今天({current_day})不在预约日范围内"

        try:
            s = reserve(
                sleep_time=0.2,
                max_attempt=20,
                enable_slider=True,
                reserve_next_day=False,
            )
            s.get_login_status()
            login_ok, login_msg = s.login(username, password)
            if not login_ok:
                return False, f"登录失败: {login_msg}"

            s.requests.headers.update({"Host": "office.chaoxing.com"})
            suc = s.submit(times, roomid, seatids, False, username)

            if suc:
                today = get_date(0)
                time_segment = f"{times[0]}-{times[1]}"
                auto_id = self.reservation_manager.get_reservation(username, today, time_segment)
                msg = f"预约成功" + (f"，预约ID: {auto_id}" if auto_id else "")
                return True, msg
            else:
                return False, "预约失败"
        except Exception as e:
            return False, f"执行异常: {e}"

    def _execute_signin(self, task):
        configs = self.config_manager.get_all_reserve_configs()
        signin_config = self.config_manager.get_signin_config()

        if task.config_index < 0 or task.config_index >= len(configs):
            return False, "配置不存在"

        cfg = configs[task.config_index]
        username = cfg.get("username", "")
        password = cfg.get("password", "")
        roomid = str(cfg.get("roomid", ""))
        seatids = cfg.get("seatid", [])
        times = cfg.get("time", [])

        if isinstance(seatids, str):
            seatids = [seatids]

        location = signin_config.get("location", {})

        today = beijing_date_str()
        time_segment = f"{times[0]}-{times[1]}"
        reserve_id = self.reservation_manager.get_reservation(username, today, time_segment)

        if not reserve_id:
            return False, "未找到预约ID"

        try:
            signin = SeatSignIn()
            signin.set_location(
                latitude=location.get("latitude", 30.0),
                longitude=location.get("longitude", 120.0),
                address=location.get("address", "图书馆"),
            )
            signin._create_new_session()
            signin.get_login_status()
            login_ok, login_msg = signin.login(username, password)

            if not login_ok:
                return False, f"登录失败: {login_msg}"

            signin.requests.headers.update({"Host": "office.chaoxing.com"})
            result = signin.signin_with_reserve_id(reserve_id, roomid, seatids[0])

            if result.get("success"):
                return True, "签到成功"
            else:
                return False, f"签到失败: {result.get('message', '')}"
        except Exception as e:
            return False, f"执行异常: {e}"

    def _execute_signout(self, task):
        configs = self.config_manager.get_all_reserve_configs()

        if task.config_index < 0 or task.config_index >= len(configs):
            return False, "配置不存在"

        cfg = configs[task.config_index]
        username = cfg.get("username", "")
        password = cfg.get("password", "")
        times = cfg.get("time", [])

        today = beijing_date_str()
        time_segment = f"{times[0]}-{times[1]}"
        reserve_id = self.reservation_manager.get_reservation(username, today, time_segment)

        if not reserve_id:
            return False, "未找到预约ID"

        try:
            signin = SeatSignIn()
            signin._create_new_session()
            signin.get_login_status()
            login_ok, login_msg = signin.login(username, password)

            if not login_ok:
                return False, f"登录失败: {login_msg}"

            signin.requests.headers.update({"Host": "office.chaoxing.com"})
            result = signin.cancel_signin(reserve_id)

            if result.get("success"):
                return True, "签退成功"
            else:
                return False, f"签退失败: {result.get('message', '')}"
        except Exception as e:
            return False, f"执行异常: {e}"

    def _execute_with_retry(self, task, execute_func, retry_delay=60):
        """Execute a task with retry logic and network check"""
        attempt = task.retry_count + 1
        while attempt <= task.max_retries:
            task.last_attempt_time = beijing_now()
            task.retry_count = attempt - 1

            if not check_network():
                logging.warning(f"网络不可用，等待重试 ({attempt}/{task.max_retries})")
                time.sleep(retry_delay)
                attempt += 1
                continue

            try:
                success, message = execute_func(task)
                if success:
                    task.status = TaskStatus.SUCCESS
                    task.result = message
                    self._notify(task.task_id, task.task_type.value, "success", message)
                    logging.info(f"任务 {task.task_id} 执行成功: {message}")
                    return
                else:
                    task.error_message = message
                    logging.warning(f"任务 {task.task_id} 执行失败 ({attempt}/{task.max_retries}): {message}")
            except Exception as e:
                task.error_message = str(e)
                logging.error(f"任务 {task.task_id} 异常: {e}")

            attempt += 1
            if attempt <= task.max_retries:
                sleep_time = retry_delay * (2 ** (attempt - 2))
                logging.info(f"等待 {sleep_time} 秒后重试...")
                time.sleep(sleep_time)

        task.status = TaskStatus.FAILED
        task.retry_count = task.max_retries
        self._notify(task.task_id, task.task_type.value, "failed",
                     task.error_message or "达到最大重试次数")
        logging.error(f"任务 {task.task_id} 已达最大重试次数，标记为失败")

    def _execute_task(self, task):
        task.status = TaskStatus.RUNNING

        if task.task_type == TaskType.RESERVE:
            self._execute_with_retry(task, self._execute_reserve)
        elif task.task_type == TaskType.SIGNIN:
            self._execute_with_retry(task, self._execute_signin)
        elif task.task_type == TaskType.SIGNOUT:
            self._execute_with_retry(task, self._execute_signout)
        else:
            task.status = TaskStatus.FAILED
            task.error_message = "未知任务类型"

        self._save_tasks()

    def _check_and_execute(self):
        now = beijing_now()

        with self._lock:
            tasks_snapshot = [t for t in self.tasks if t.status == TaskStatus.PENDING]

        for task in tasks_snapshot:
            if task.task_type == TaskType.SIGNIN:
                earliest_time = task.target_time - timedelta(minutes=task.advance_threshold)
                if now >= earliest_time:
                    self._execute_task(task)
            elif task.task_type == TaskType.SIGNOUT:
                latest_time = task.target_time + timedelta(minutes=task.delay_threshold)
                if now >= task.target_time and now <= latest_time:
                    self._execute_task(task)
            else:
                if now >= task.target_time:
                    self._execute_task(task)

    def _check_recovery(self):
        now = beijing_now()

        if self._last_recovery_check is not None:
            elapsed = (now - self._last_recovery_check).total_seconds()
            if elapsed < self._recovery_check_interval:
                return

        self._last_recovery_check = now

        with self._lock:
            pending_tasks = [t for t in self.tasks if t.status == TaskStatus.PENDING]

        for task in pending_tasks:
            if task.task_type == TaskType.SIGNIN:
                latest_time = task.target_time + timedelta(minutes=30)
                if now > latest_time:
                    logging.info(f"检测到遗漏的签到任务 {task.task_id}，尝试恢复执行")
                    self._execute_task(task)
            elif task.task_type == TaskType.SIGNOUT:
                latest_time = task.target_time + timedelta(minutes=60)
                if now > latest_time:
                    logging.info(f"检测到遗漏的签退任务 {task.task_id}，尝试恢复执行")
                    self._execute_task(task)
            else:
                if now > task.target_time:
                    logging.info(f"检测到遗漏的任务 {task.task_id}，尝试恢复执行")
                    self._execute_task(task)

    def _cleanup_completed(self, days_to_keep=7):
        cutoff_date = beijing_now() - timedelta(days=days_to_keep)
        with self._lock:
            self.tasks = [
                t for t in self.tasks
                if (t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)) or
                   (t.last_attempt_time is not None and t.last_attempt_time > cutoff_date)
            ]
        if self.tasks:
            self._save_tasks()

    def run(self):
        self.running = True
        logging.info("定时任务调度器已启动")

        while self.running:
            try:
                self._check_and_execute()
                self._check_recovery()
                self._cleanup_completed()
                time.sleep(self._check_interval)
            except KeyboardInterrupt:
                logging.info("收到中断信号，正在停止...")
                self.running = False
            except Exception as e:
                logging.error(f"调度器异常: {e}")
                time.sleep(60)

        logging.info("定时任务调度器已停止")

    def stop(self):
        self.running = False

    def get_tasks(self, status=None):
        with self._lock:
            if status:
                return [t for t in self.tasks if t.status == TaskStatus(status)]
            return list(self.tasks)

    def cancel_task(self, task_id):
        with self._lock:
            for task in self.tasks:
                if task.task_id == task_id and task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.SKIPPED
                    self._save_tasks()
                    return True
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="定时任务调度器")
    parser.add_argument("--mode", choices=["run", "schedule", "list", "cancel"], default="run", help="运行模式")
    parser.add_argument("--task-type", choices=["reserve", "signin", "signout"], help="任务类型")
    parser.add_argument("--config-index", type=int, help="配置索引")
    parser.add_argument("--target-time", help="目标时间 (格式: YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--task-id", help="任务ID")
    args = parser.parse_args()

    scheduler = TaskScheduler()

    if args.mode == "run":
        scheduler.run()
    elif args.mode == "schedule":
        if args.task_type is None or args.config_index is None:
            print("需要指定 --task-type 和 --config-index")
            return

        if args.task_type == "reserve":
            task = scheduler.schedule_reservation(args.config_index)
        elif args.task_type == "signin":
            if args.target_time is None:
                print("签到任务需要指定 --target-time")
                return
            target_time = datetime.strptime(args.target_time, "%Y-%m-%d %H:%M:%S")
            task = scheduler.schedule_signin(args.config_index, target_time)
        elif args.task_type == "signout":
            if args.target_time is None:
                print("签退任务需要指定 --target-time")
                return
            target_time = datetime.strptime(args.target_time, "%Y-%m-%d %H:%M:%S")
            task = scheduler.schedule_signout(args.config_index, target_time)

        print(f"任务已创建: {task.task_id}")
    elif args.mode == "list":
        scheduler._load_tasks()
        tasks = scheduler.get_tasks()
        if not tasks:
            print("暂无任务")
        for t in tasks:
            print(f"{t.task_id} | {t.task_type.value} | {t.status.value} | {t.target_time}")
    elif args.mode == "cancel":
        if args.task_id is None:
            print("需要指定 --task-id")
            return
        success = scheduler.cancel_task(args.task_id)
        if success:
            print("任务已取消")
        else:
            print("任务取消失败（任务不存在或已执行）")


if __name__ == "__main__":
    main()