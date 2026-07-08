#!/usr/bin/env python3
import time
import json
import logging
import functools
from datetime import datetime, timedelta
from enum import Enum


class RetryStrategy(Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


class RetryException(Exception):
    def __init__(self, message, retry_count=0, max_retries=0):
        super().__init__(message)
        self.retry_count = retry_count
        self.max_retries = max_retries


def retry(
    max_retries=3,
    delay=1,
    strategy=RetryStrategy.FIXED,
    backoff_factor=2,
    exceptions=(Exception,),
    on_retry=None,
    timeout=None
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retry_count = 0
            last_exception = None
            start_time = time.time()

            while retry_count < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    retry_count += 1

                    if on_retry:
                        on_retry(retry_count, max_retries, e)

                    logging.warning(
                        f"重试 {retry_count}/{max_retries} - {func.__name__} 失败: {e}"
                    )

                    if timeout and (time.time() - start_time) >= timeout:
                        logging.error(f"超时，停止重试")
                        break

                    if strategy == RetryStrategy.FIXED:
                        sleep_time = delay
                    elif strategy == RetryStrategy.EXPONENTIAL:
                        sleep_time = delay * (backoff_factor ** (retry_count - 1))
                    elif strategy == RetryStrategy.LINEAR:
                        sleep_time = delay * retry_count
                    else:
                        sleep_time = delay

                    time.sleep(sleep_time)

            raise RetryException(
                f"{func.__name__} 重试 {max_retries} 次后仍然失败: {last_exception}",
                retry_count=retry_count,
                max_retries=max_retries
            )

        return wrapper

    return decorator


class RetryManager:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.retry_records = {}

    def record_retry(self, task_id, action, retry_count, success, error_message=None):
        if task_id not in self.retry_records:
            self.retry_records[task_id] = []

        self.retry_records[task_id].append({
            "action": action,
            "retry_count": retry_count,
            "success": success,
            "error_message": error_message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        if success:
            self.logger.info(f"任务 {task_id} 操作 {action} 成功")
        else:
            self.logger.warning(f"任务 {task_id} 操作 {action} 失败 ({retry_count}次): {error_message}")

    def get_retry_history(self, task_id):
        return self.retry_records.get(task_id, [])

    def should_retry(self, task_id, max_retries=3, min_interval=60):
        records = self.retry_records.get(task_id, [])
        if len(records) >= max_retries:
            return False

        if records:
            last_retry = datetime.strptime(records[-1]["timestamp"], "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - last_retry).total_seconds() < min_interval:
                return False

        return True

    def clear_old_records(self, days_to_keep=7):
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed = 0

        for task_id in list(self.retry_records.keys()):
            records = self.retry_records[task_id]
            new_records = []
            for record in records:
                try:
                    record_time = datetime.strptime(record["timestamp"], "%Y-%m-%d %H:%M:%S")
                    if record_time >= cutoff_date:
                        new_records.append(record)
                    else:
                        removed += 1
                except:
                    new_records.append(record)

            if new_records:
                self.retry_records[task_id] = new_records
            else:
                del self.retry_records[task_id]

        return removed


def notify_user(task_id, action, status, message, notify_method="log"):
    notification = {
        "task_id": task_id,
        "action": action,
        "status": status,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if notify_method == "log":
        logging.info(f"通知: {notification}")
    elif notify_method == "file":
        with open("notifications.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(notification) + "\n")

    return notification


class NetworkRecovery:
    def __init__(self, check_interval=5, max_wait=300):
        self.check_interval = check_interval
        self.max_wait = max_wait

    def wait_for_network(self, test_func=None):
        import urllib.request

        start_time = time.time()

        while time.time() - start_time < self.max_wait:
            try:
                if test_func:
                    test_func()
                else:
                    urllib.request.urlopen("http://www.baidu.com", timeout=5)
                return True
            except Exception:
                logging.warning("网络不可用，等待重试...")
                time.sleep(self.check_interval)

        return False


class TaskRecovery:
    def __init__(self, retry_manager=None):
        self.retry_manager = retry_manager or RetryManager()

    def recover_task(self, task_id, task_func, max_retries=3):
        if not self.retry_manager.should_retry(task_id, max_retries):
            return False, "达到最大重试次数或重试间隔不足"

        retry_count = len(self.retry_manager.get_retry_history(task_id))

        try:
            result = task_func()
            self.retry_manager.record_retry(task_id, "recovery", retry_count + 1, True)
            notify_user(task_id, "recovery", "success", f"任务恢复成功")
            return True, result
        except Exception as e:
            self.retry_manager.record_retry(task_id, "recovery", retry_count + 1, False, str(e))
            notify_user(task_id, "recovery", "failed", f"任务恢复失败: {e}")
            return False, str(e)


@retry(max_retries=3, delay=2, strategy=RetryStrategy.EXPONENTIAL)
def test_retry_function():
    import random
    if random.random() < 0.7:
        raise Exception("模拟失败")
    return "成功"


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        try:
            result = test_retry_function()
            print(f"测试结果: {result}")
        except RetryException as e:
            print(f"测试失败: {e}")

    rm = RetryManager()
    rm.record_retry("test_task", "reserve", 1, False, "网络超时")
    rm.record_retry("test_task", "reserve", 2, True)

    print("重试历史:", rm.get_retry_history("test_task"))
    print("是否应该重试:", rm.should_retry("test_task"))