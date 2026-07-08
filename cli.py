#!/usr/bin/env python3
"""
超星学习通座位预约管理 CLI 工具
提供预约、签到、签退、日志、配置及定时任务管理功能
"""
import argparse
import sys
import os
import json
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.reserve import reserve, get_date
from utils.signin import SeatSignIn
from utils.reservation_manager import ReservationManager
from utils.common import beijing_now, beijing_date_str, beijing_dayofweek
from backend.bputils.config_manager import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("chaoxing_seat.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


def cmd_reserve(args):
    """预约座位"""
    config_manager = ConfigManager()
    configs = config_manager.get_all_reserve_configs()

    if args.index is None:
        print("可用的预约配置:")
        for i, cfg in enumerate(configs):
            print(f"  [{i}] {cfg.get('username', '')} - {cfg.get('time', [])} - {cfg.get('seatid', [])}")
        if not configs:
            print("  (暂无配置，请使用 'config add' 添加)")
        return

    if args.index < 0 or args.index >= len(configs):
        print(f"错误: 配置索引 {args.index} 不存在，可用范围: 0-{len(configs)-1}")
        return

    cfg = configs[args.index]
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
        print(f"警告: 今天({current_day})不在配置的预约日内")
        if not args.force:
            print("使用 --force 强制预约")
            return

    print(f"开始预约: {username} | {times} | {seatids}")

    try:
        s = reserve(
            sleep_time=args.sleep_time,
            max_attempt=args.max_attempt,
            enable_slider=args.enable_slider,
            reserve_next_day=args.next_day,
        )
        s.get_login_status()
        login_ok, login_msg = s.login(username, password)
        if not login_ok:
            print(f"登录失败: {login_msg}")
            return

        s.requests.headers.update({"Host": "office.chaoxing.com"})
        suc = s.submit(times, roomid, seatids, False, username)

        if suc:
            print("预约成功!")
            today = get_date(0)
            time_segment = f"{times[0]}-{times[1]}"
            rm = ReservationManager()
            auto_id = rm.get_reservation(username, today, time_segment)
            if auto_id:
                print(f"预约ID: {auto_id}")
        else:
            print("预约失败")
    except Exception as e:
        print(f"执行异常: {e}")
        logging.error(f"预约执行异常: {e}")


def cmd_query(args):
    """查询预约记录"""
    rm = ReservationManager()

    if args.username:
        data = rm.get_all_reservations(args.username)
    else:
        data = rm.get_all_reservations()

    if not data:
        print("暂无预约记录")
        return

    for username, dates in data.items():
        print(f"\n用户: {username}")
        for date, times in dates.items():
            print(f"  日期: {date}")
            for time_segment, reserve_id in times.items():
                print(f"    时段: {time_segment} | 预约ID: {reserve_id}")


def cmd_signin(args):
    """执行签到"""
    config_manager = ConfigManager()
    configs = config_manager.get_all_reserve_configs()
    signin_config = config_manager.get_signin_config()

    location = signin_config.get("location", {})

    if args.index is not None:
        if args.index < 0 or args.index >= len(configs):
            print(f"错误: 配置索引 {args.index} 不存在")
            return
        users_to_signin = [configs[args.index]]
    else:
        users_to_signin = configs

    signin = SeatSignIn()
    signin.set_location(
        latitude=location.get("latitude", 30.0),
        longitude=location.get("longitude", 120.0),
        address=location.get("address", "图书馆"),
    )

    current_day = beijing_dayofweek()
    today = beijing_date_str()

    for cfg in users_to_signin:
        username = cfg.get("username", "")
        password = cfg.get("password", "")
        roomid = str(cfg.get("roomid", ""))
        seatids = cfg.get("seatid", [])
        daysofweek = cfg.get("daysofweek", [])
        times = cfg.get("time", [])

        if isinstance(seatids, str):
            seatids = [seatids]

        if current_day not in daysofweek:
            print(f"{username}: 今天不在签到日范围内，跳过")
            continue

        time_segment = f"{times[0]}-{times[1]}"

        rm = ReservationManager()
        reserve_id = rm.get_reservation(username, today, time_segment)

        print(f"\n开始签到: {username}")

        signin._create_new_session()
        signin.get_login_status()
        login_ok, login_msg = signin.login(username, password)

        if not login_ok:
            print(f"  登录失败: {login_msg}")
            continue

        signin.requests.headers.update({"Host": "office.chaoxing.com"})

        if reserve_id:
            print(f"  使用预约ID: {reserve_id}")
            result = signin.signin_with_reserve_id(reserve_id, roomid, seatids[0])
        else:
            print("  未找到预约ID，尝试从接口获取")
            result = signin.execute_signin(roomid, seatids[0])

        status = "成功" if result.get("success") else "失败"
        print(f"  签到{status}: {result.get('message', '')}")


def cmd_signout(args):
    """执行签退"""
    config_manager = ConfigManager()
    configs = config_manager.get_all_reserve_configs()

    if args.index is not None:
        if args.index < 0 or args.index >= len(configs):
            print(f"错误: 配置索引 {args.index} 不存在")
            return
        users_to_signout = [configs[args.index]]
    else:
        users_to_signout = configs

    current_day = beijing_dayofweek()
    today = beijing_date_str()

    for cfg in users_to_signout:
        username = cfg.get("username", "")
        password = cfg.get("password", "")
        times = cfg.get("time", [])
        daysofweek = cfg.get("daysofweek", [])

        if current_day not in daysofweek:
            print(f"{username}: 今天不在预约日范围内，跳过")
            continue

        time_segment = f"{times[0]}-{times[1]}"

        rm = ReservationManager()
        reserve_id = rm.get_reservation(username, today, time_segment)

        if not reserve_id:
            print(f"{username}: 未找到预约ID")
            continue

        print(f"\n开始签退: {username} | 预约ID: {reserve_id}")

        signin = SeatSignIn()
        signin._create_new_session()
        signin.get_login_status()
        login_ok, login_msg = signin.login(username, password)

        if not login_ok:
            print(f"  登录失败: {login_msg}")
            continue

        signin.requests.headers.update({"Host": "office.chaoxing.com"})
        result = signin.cancel_signin(reserve_id)

        status = "成功" if result.get("success") else "失败"
        print(f"  签退{status}: {result.get('message', '')}")


def cmd_logs(args):
    """查看和导出日志"""
    log_file = "chaoxing_seat.log"

    if not os.path.exists(log_file):
        print("日志文件不存在")
        return

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"读取日志失败: {e}")
        return

    if args.tail is not None:
        lines = lines[-args.tail:]
    elif args.since:
        try:
            since_time = datetime.strptime(args.since, "%Y-%m-%d %H:%M:%S")
            filtered = []
            for line in lines:
                try:
                    log_time_str = line.split(" - ")[0]
                    log_time = datetime.strptime(log_time_str, "%Y-%m-%d %H:%M:%S,%f")
                    if log_time >= since_time:
                        filtered.append(line)
                except Exception:
                    pass
            lines = filtered
        except Exception:
            print("时间格式错误，请使用: YYYY-MM-DD HH:MM:SS")
            return

    for line in lines:
        print(line, end="")

    if args.export:
        export_file = args.export
        try:
            with open(export_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"\n日志已导出到: {export_file}")
        except Exception as e:
            print(f"导出失败: {e}")


def cmd_config(args):
    """管理配置"""
    config_manager = ConfigManager()

    if args.action == "list":
        configs = config_manager.get_all_reserve_configs()
        print("预约配置列表:")
        if not configs:
            print("  (暂无配置)")
            return
        for i, cfg in enumerate(configs):
            print(f"\n[{i}]")
            print(f"  用户名: {cfg.get('username', '')}")
            print(f"  时间: {cfg.get('time', [])}")
            print(f"  房间ID: {cfg.get('roomid', '')}")
            print(f"  座位号: {cfg.get('seatid', [])}")
            print(f"  预约日: {cfg.get('daysofweek', [])}")

    elif args.action == "view":
        if args.index is None:
            print("请指定配置索引: --index")
            return
        cfg = config_manager.get_reserve_config(args.index)
        if cfg is None:
            print(f"配置 {args.index} 不存在")
            return
        print(json.dumps(cfg, indent=2, ensure_ascii=False))

    elif args.action == "add":
        if args.json is None:
            print("请提供配置JSON: --json")
            return
        try:
            data = json.loads(args.json)
            validation = config_manager.validate_config(data)
            if not validation["valid"]:
                print("配置验证失败:")
                for err in validation["errors"]:
                    print(f"  - {err}")
                return
            index = config_manager.add_reserve_config(data)
            print(f"配置添加成功，索引: {index}")
        except json.JSONDecodeError:
            print("JSON格式错误")

    elif args.action == "update":
        if args.index is None or args.json is None:
            print("请提供配置索引和JSON: --index --json")
            return
        try:
            data = json.loads(args.json)
            validation = config_manager.validate_config(data)
            if not validation["valid"]:
                print("配置验证失败:")
                for err in validation["errors"]:
                    print(f"  - {err}")
                return
            success = config_manager.update_reserve_config(args.index, data)
            if success:
                print("配置更新成功")
            else:
                print("配置更新失败，索引不存在")
        except json.JSONDecodeError:
            print("JSON格式错误")

    elif args.action == "delete":
        if args.index is None:
            print("请指定配置索引: --index")
            return
        success = config_manager.delete_reserve_config(args.index)
        if success:
            print("配置删除成功")
        else:
            print("配置删除失败，索引不存在")

    elif args.action == "signin":
        signin_cfg = config_manager.get_signin_config()
        print(json.dumps(signin_cfg, indent=2, ensure_ascii=False))


def cmd_scheduler(args):
    """管理定时任务调度"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from scheduler import TaskScheduler, TaskType, TaskStatus

    scheduler = TaskScheduler(auto_load=True)

    if args.action == "list":
        tasks = scheduler.get_tasks()
        if not tasks:
            print("暂无任务")
            return

        status_filter = args.status
        print(f"{'任务ID':<40} {'类型':<10} {'状态':<10} {'目标时间':<20} {'重试':<6}")
        print("-" * 90)
        for t in tasks:
            if status_filter and t.status.value != status_filter:
                continue
            target_str = t.target_time.strftime("%Y-%m-%d %H:%M:%S") if isinstance(t.target_time, datetime) else str(t.target_time)
            print(f"{t.task_id:<40} {t.task_type.value:<10} {t.status.value:<10} {target_str:<20} {t.retry_count}/{t.max_retries}")

    elif args.action == "create":
        if not args.task_type or args.config_index is None:
            print("请指定 --task-type 和 --config-index")
            return

        if args.task_type == "reserve":
            task = scheduler.schedule_reservation(args.config_index)
        elif args.task_type == "signin":
            if not args.target_time:
                print("签到任务需要指定 --target-time (格式: YYYY-MM-DD HH:MM:SS)")
                return
            target_time = datetime.strptime(args.target_time, "%Y-%m-%d %H:%M:%S")
            task = scheduler.schedule_signin(args.config_index, target_time, args.advance)
        elif args.task_type == "signout":
            if not args.target_time:
                print("签退任务需要指定 --target-time (格式: YYYY-MM-DD HH:MM:SS)")
                return
            target_time = datetime.strptime(args.target_time, "%Y-%m-%d %H:%M:%S")
            task = scheduler.schedule_signout(args.config_index, target_time, args.delay)
        else:
            print(f"未知任务类型: {args.task_type}")
            return

        print(f"任务已创建: {task.task_id}")

    elif args.action == "cancel":
        if not args.task_id:
            print("请指定 --task-id")
            return
        success = scheduler.cancel_task(args.task_id)
        if success:
            print("任务已取消")
        else:
            print("任务取消失败（任务不存在或已执行）")

    elif args.action == "auto":
        from backend.bputils.config_manager import ConfigManager
        config_manager = ConfigManager()
        configs = config_manager.get_all_reserve_configs()
        today = beijing_now().date()
        created_count = 0

        for i, cfg in enumerate(configs):
            daysofweek = cfg.get("daysofweek", [])
            current_day = beijing_dayofweek()
            if current_day not in daysofweek:
                continue

            times = cfg.get("time", [])
            try:
                scheduler.schedule_reservation(i, today)
                created_count += 1

                if len(times) >= 2:
                    start_time = datetime.strptime(times[0], "%H:%M").time()
                    end_time = datetime.strptime(times[1], "%H:%M").time()
                    signin_dt = datetime.combine(today, start_time)
                    signout_dt = datetime.combine(today, end_time)
                    scheduler.schedule_signin(i, signin_dt)
                    scheduler.schedule_signout(i, signout_dt)
                    created_count += 2
            except Exception as e:
                print(f"配置 [{i}] 创建任务失败: {e}")

        print(f"已自动创建 {created_count} 个今日任务")

    elif args.action == "run":
        print("启动定时任务调度器... (按 Ctrl+C 停止)")
        try:
            scheduler.run()
        except KeyboardInterrupt:
            print("\n调度器已停止")

    elif args.action == "notifications":
        notif_file = "notifications.json"
        if os.path.exists(notif_file):
            try:
                with open(notif_file, "r", encoding="utf-8") as f:
                    notifications = json.load(f)
                if not notifications:
                    print("暂无通知")
                    return
                for n in notifications[-50:]:
                    print(f"[{n['timestamp']}] {n['action']} - {n['status']}: {n['message']}")
            except Exception as e:
                print(f"读取通知失败: {e}")
        else:
            print("暂无通知记录")


def main():
    parser = argparse.ArgumentParser(
        prog="chaoxing-seat",
        description="超星学习通座位预约管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  预约座位:            chaoxing-seat reserve --index 0
  查询预约记录:        chaoxing-seat query
  签到:                chaoxing-seat signin --index 0
  签退:                chaoxing-seat signout --index 0
  查看日志:            chaoxing-seat logs --tail 100
  管理配置:            chaoxing-seat config list
  创建定时任务:        chaoxing-seat scheduler create --task-type signin --config-index 0 --target-time "2026-07-09 10:30:00"
  自动生成今日任务:    chaoxing-seat scheduler auto
  查看任务列表:        chaoxing-seat scheduler list
  启动调度器:          chaoxing-seat scheduler run
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # reserve 子命令
    reserve_parser = subparsers.add_parser("reserve", help="预约座位")
    reserve_parser.add_argument("--index", type=int, help="配置索引")
    reserve_parser.add_argument("--force", action="store_true", help="强制预约（忽略日期限制）")
    reserve_parser.add_argument("--sleep-time", type=float, default=0.2, help="请求间隔(秒)")
    reserve_parser.add_argument("--max-attempt", type=int, default=20, help="最大尝试次数")
    reserve_parser.add_argument("--enable-slider", action="store_true", help="启用滑块验证")
    reserve_parser.add_argument("--next-day", action="store_true", help="预约明天")

    # query 子命令
    query_parser = subparsers.add_parser("query", help="查询预约记录")
    query_parser.add_argument("--username", help="指定用户名")

    # signin 子命令
    signin_parser = subparsers.add_parser("signin", help="执行签到")
    signin_parser.add_argument("--index", type=int, help="配置索引")

    # signout 子命令
    signout_parser = subparsers.add_parser("signout", help="执行签退")
    signout_parser.add_argument("--index", type=int, help="配置索引")

    # logs 子命令
    logs_parser = subparsers.add_parser("logs", help="查看日志")
    logs_parser.add_argument("--tail", type=int, help="显示最后N行")
    logs_parser.add_argument("--since", help="显示指定时间之后的日志 (格式: YYYY-MM-DD HH:MM:SS)")
    logs_parser.add_argument("--export", help="导出日志到文件")

    # config 子命令
    config_parser = subparsers.add_parser("config", help="管理配置")
    config_parser.add_argument("action", choices=["list", "view", "add", "update", "delete", "signin"])
    config_parser.add_argument("--index", type=int, help="配置索引")
    config_parser.add_argument("--json", help="配置JSON")

    # scheduler 子命令
    sched_parser = subparsers.add_parser("scheduler", help="管理定时任务调度")
    sched_parser.add_argument("action", choices=["list", "create", "cancel", "auto", "run", "notifications"],
                              help="操作类型")
    sched_parser.add_argument("--task-type", choices=["reserve", "signin", "signout"], help="任务类型")
    sched_parser.add_argument("--config-index", type=int, help="配置索引")
    sched_parser.add_argument("--target-time", help="目标时间 (格式: YYYY-MM-DD HH:MM:SS)")
    sched_parser.add_argument("--task-id", help="任务ID")
    sched_parser.add_argument("--status", choices=["pending", "running", "success", "failed", "skipped"], help="按状态筛选")
    sched_parser.add_argument("--advance", type=int, default=5, help="提前签到分钟数")
    sched_parser.add_argument("--delay", type=int, default=0, help="延迟签退分钟数")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    command_map = {
        "reserve": cmd_reserve,
        "query": cmd_query,
        "signin": cmd_signin,
        "signout": cmd_signout,
        "logs": cmd_logs,
        "config": cmd_config,
        "scheduler": cmd_scheduler,
    }

    try:
        command_map[args.command](args)
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"错误: {e}")
        logging.error(f"命令执行错误: {e}")


if __name__ == "__main__":
    main()