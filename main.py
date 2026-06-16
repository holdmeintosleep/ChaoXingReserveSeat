import json
import time
import argparse
import os
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
from utils import reserve, get_user_credentials, SeatSignIn

# 统一使用北京时间（UTC+8），不受服务器时区影响
get_current_time = lambda action: time.strftime("%H:%M:%S", time.localtime(time.time() + 8 * 3600))
get_current_dayofweek = lambda action: time.strftime("%A", time.localtime(time.time() + 8 * 3600))
SLEEPTIME = 0.2  # 每次抢座的间隔
ENDTIME = "22:01:00"  # 北京时间22:00启动抢座，22:01停止
ENABLE_SLIDER = True  # 是否有滑块验证
MAX_ATTEMPT = 20  # 最大尝试次数
RESERVE_NEXT_DAY = True  # 预约明天而不是今天的


def login_and_reserve(users, usernames, passwords, action, success_list=None):
    logging.info(
        f"Global settings: \nSLEEPTIME: {SLEEPTIME}\nENDTIME: {ENDTIME}\nENABLE_SLIDER: {ENABLE_SLIDER}\nRESERVE_NEXT_DAY: {RESERVE_NEXT_DAY}"
    )
    if action and len(usernames.split(",")) != len(users):
        raise Exception("user number should match the number of config")
    if success_list is None:
        success_list = [False] * len(users)
    current_dayofweek = get_current_dayofweek(action)
    for index, user in enumerate(users):
        username = user.get("username", "")
        password = user.get("password", "")
        times = user.get("time", [])
        roomid = user.get("roomid", "")
        seatid = user.get("seatid", [])
        daysofweek = user.get("daysofweek", [])
        if action:
            username, password = (
                usernames.split(",")[index],
                passwords.split(",")[index],
            )
        if current_dayofweek not in daysofweek:
            logging.info("Today not set to reserve")
            continue
        if not success_list[index]:
            logging.info(
                f"----------- {username} -- {times} -- {seatid} try -----------"
            )
            s = reserve(
                sleep_time=SLEEPTIME,
                max_attempt=MAX_ATTEMPT,
                enable_slider=ENABLE_SLIDER,
                reserve_next_day=RESERVE_NEXT_DAY,
            )
            s.get_login_status()
            s.login(username, password)
            s.requests.headers.update({"Host": "office.chaoxing.com"})
            suc = s.submit(times, roomid, seatid, action, username)
            success_list[index] = suc
    return success_list


def main(users, action=False):
    current_time = get_current_time(action)
    logging.info(f"start time {current_time}, action {'on' if action else 'off'}")
    attempt_times = 0
    usernames, passwords = None, None
    if action:
        usernames, passwords = get_user_credentials(action)
    success_list = None
    current_dayofweek = get_current_dayofweek(action)
    today_reservation_num = sum(
        1 for d in users if current_dayofweek in d.get("daysofweek")
    )
    while current_time < ENDTIME:
        attempt_times += 1
        # try:
        success_list = login_and_reserve(
            users, usernames, passwords, action, success_list
        )
        # except Exception as e:
        #     print(f"An error occurred: {e}")
        print(
            f"attempt time {attempt_times}, time now {current_time}, success list {success_list}"
        )
        current_time = get_current_time(action)
        if sum(success_list) == today_reservation_num:
            print(f"reserved successfully!")
            return


def debug(users, action=False):
    logging.info(
        f"Global settings: \nSLEEPTIME: {SLEEPTIME}\nENDTIME: {ENDTIME}\nENABLE_SLIDER: {ENABLE_SLIDER}\nRESERVE_NEXT_DAY: {RESERVE_NEXT_DAY}"
    )
    logging.info(f" Debug Mode start! , action {'on' if action else 'off'}")
    if action:
        usernames, passwords = get_user_credentials(action)
    current_dayofweek = get_current_dayofweek(action)
    for index, user in enumerate(users):
        username = user.get("username", "")
        password = user.get("password", "")
        times = user.get("time", [])
        roomid = user.get("roomid", "")
        seatid = user.get("seatid", [])
        daysofweek = user.get("daysofweek", [])
        if type(seatid) == str:
            seatid = [seatid]
        if action:
            username, password = (
                usernames.split(",")[index],
                passwords.split(",")[index],
            )
        if current_dayofweek not in daysofweek:
            logging.info("Today not set to reserve")
            continue
        logging.info(f"----------- {username} -- {times} -- {seatid} try -----------")
        s = reserve(
            sleep_time=SLEEPTIME,
            max_attempt=MAX_ATTEMPT,
            enable_slider=ENABLE_SLIDER,
            reserve_next_day=RESERVE_NEXT_DAY,
        )
        s.get_login_status()
        s.login(username, password)
        s.requests.headers.update({"Host": "office.chaoxing.com"})
        s.submit(times, roomid, seatid, action, username)


def get_roomid(args1, args2):
    username = input("请输入用户名：")
    password = input("请输入密码：")
    s = reserve(
        sleep_time=SLEEPTIME,
        max_attempt=MAX_ATTEMPT,
        enable_slider=ENABLE_SLIDER,
        reserve_next_day=RESERVE_NEXT_DAY,
    )
    s.get_login_status()
    s.login(username=username, password=password)
    s.requests.headers.update({"Host": "office.chaoxing.com"})
    encode = input("请输入deptldEnc：")
    s.roomid(encode)


def do_signin(users, action=False):
    """
    自动签到入口

    支持两种模式：
    1. 一次性签到 - 检查当前时段并签到（默认）
    2. 定时循环签到 - 持续运行，在每个时段开始时自动签到

    可通过config.json中的signin.enabled控制是否启用
    """
    with open(
        os.path.join(os.path.dirname(__file__), "config.json"), "r+"
    ) as config_file:
        config = json.load(config_file)
        signin_config = config.get("signin", {})

    if not signin_config.get("enabled", True):
        logging.info("签到模块已在config.json中禁用 (signin.enabled=false)")
        return

    # 读取GPS位置配置
    location = signin_config.get("location", {})
    check_interval = signin_config.get("check_interval", 60)

    # 创建签到实例
    signin = SeatSignIn()
    signin.set_location(
        latitude=location.get("latitude", 30.0),
        longitude=location.get("longitude", 120.0),
        address=location.get("address", "图书馆"),
    )

    if action:
        # GitHub Actions 模式：定时循环签到
        logging.info("启动定时循环签到模式 (GitHub Actions)")
        signin.run_scheduled_signin(users, check_interval=check_interval)
    else:
        # 本地模式：一次性签到（检查当前时段）
        logging.info("启动一次性签到模式（检查当前时段）")
        results = signin.segmented_signin(users)

        # 输出结果摘要
        success_count = sum(1 for r in results if r.get("success"))
        fail_count = len(results) - success_count
        logging.info(f"签到完成: 成功 {success_count}, 失败 {fail_count}")

        for r in results:
            status = "成功" if r.get("success") else "失败"
            logging.info(
                f"  {r.get('username')} | {r.get('time_segment', 'N/A')} | "
                f"{status} | {r.get('message', '')}"
            )


if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    parser = argparse.ArgumentParser(prog="Chao Xing seat auto reserve")
    parser.add_argument("-u", "--user", default=config_path, help="user config file")
    parser.add_argument(
        "-m",
        "--method",
        default="reserve",
        choices=["reserve", "debug", "room", "signin"],
        help="for debug",
    )
    parser.add_argument(
        "-a",
        "--action",
        action="store_true",
        help="use --action to enable in github action",
    )
    args = parser.parse_args()
    func_dict = {"reserve": main, "debug": debug, "room": get_roomid, "signin": do_signin}
    with open(args.user, "r+") as data:
        usersdata = json.load(data)["reserve"]
    func_dict[args.method](usersdata, args.action)
