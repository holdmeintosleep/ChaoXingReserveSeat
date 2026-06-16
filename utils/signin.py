"""
超星学习通座位自动签到模块

功能：
  1. 支持分段式签到 - 自动检测当前时间段并签到
  2. GPS位置模拟 - 绕过位置检查机制
  3. 二维码固定值识别 - 从预约信息中提取reserveId
  4. 签到状态查询 - 查询当前预约及签到状态
  5. 签到取消 - 支持取消已完成的签到
  6. 自动获取预约ID - 从reservations.json读取，无需手动配置

技术路径：
  - 利用签到二维码的固定值(reserveId)特性，直接从预约信息页面提取
  - 构建与超星服务器的通信机制，完成签到数据自动提交
  - 支持模拟GPS定位信息以通过位置检查
  - 优先使用配置中的reserveId，其次从reservations.json自动读取
"""

import json
import re
import time
import logging
import datetime
import requests
from urllib3.exceptions import InsecureRequestWarning

# 延迟导入，避免循环依赖
try:
    from .reservation_manager import ReservationManager
except ImportError:
    ReservationManager = None

# 北京时间的时区偏移
UTC_OFFSET = 8


def _beijing_now():
    """获取北京时间"""
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=UTC_OFFSET)))


def _beijing_time_str(fmt="%H:%M:%S"):
    """获取北京时间字符串"""
    return _beijing_now().strftime(fmt)


def _beijing_date_str(fmt="%Y-%m-%d"):
    """获取北京日期字符串"""
    return _beijing_now().strftime(fmt)


def _beijing_dayofweek():
    """获取北京时间的星期"""
    return _beijing_now().strftime("%A")


def _time_to_minutes(time_str):
    """将 HH:MM 格式的时间转换为分钟数"""
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def _current_minutes():
    """获取当前北京时间对应的分钟数"""
    now = _beijing_now()
    return now.hour * 60 + now.minute


class SeatSignIn:
    """
    超星座位自动签到类
    
    使用示例:
        signin = SeatSignIn()
        signin.get_login_status()
        signin.login(username, password)
        signin.requests.headers.update({"Host": "office.chaoxing.com"})
        
        # 单个签到
        success = signin.execute_signin(roomid="6913", seatid="011")
        
        # 分段式自动签到（根据配置自动判断当前时段）
        results = signin.segmented_signin(config_users)
    """

    def __init__(self, session=None):
        """
        Args:
            session: 可复用的 requests.Session 对象（如从 reserve 实例传入）
        """
        self.requests = session or requests.session()

        # API 端点
        self.login_page = (
            "https://passport2.chaoxing.com/mlogin?loginType=1&newversion=true&fid="
        )
        self.login_url = "https://passport2.chaoxing.com/fanyalogin"
        self.reserve_info_url = (
            "https://office.chaoxing.com/data/apps/seat/reserve/info"
        )
        self.sign_url = "https://office.chaoxing.com/data/apps/seat/sign"
        self.used_times_url = (
            "https://office.chaoxing.com/data/apps/seat/getusedtimes"
        )
        self.seat_page_url = (
            "https://office.chaoxing.com/front/third/apps/seat/code?id={}&seatNum={}"
        )

        # 默认GPS位置（用于模拟定位）
        self.default_location = {
            "latitude": 30.0,
            "longitude": 120.0,
            "address": "图书馆",
        }

        self.headers = {
            "Referer": "https://office.chaoxing.com/",
            "Host": "office.chaoxing.com",
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) "
                "AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 "
                "Mobile/14E304 Safari/602.1"
            ),
            "X-Requested-With": "XMLHttpRequest",
        }

        self.login_headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) "
                "AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 "
                "Mobile/14E304 Safari/602.1 "
                "wechatdevtools/1.05.2109131 MicroMessenger/8.0.5 "
                "Language/zh_CN webview/16364215743155638"
            ),
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "passport2.chaoxing.com",
        }

        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    def _create_new_session(self):
        """创建新的session，用于多用户登录时避免session冲突"""
        self.requests = requests.session()
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # ─── 登录相关 ─────────────────────────────────────────────

    def get_login_status(self):
        """初始化登录页面，获取初始cookie"""
        self.requests.headers = self.login_headers
        try:
            self.requests.get(url=self.login_page, verify=False, timeout=15)
        except requests.RequestException as e:
            logging.error(f"获取登录页面失败: {e}")

    def login(self, username: str, password: str, max_retries: int = 3):
        """
        执行登录操作
        
        Args:
            username: 明文用户名（内部会AES加密）
            password: 明文密码（内部会AES加密）
            max_retries: 最大重试次数，默认3次
        
        Returns:
            (success: bool, message: str)
        """
        from .encrypt import AES_Encrypt

        encrypted_username = AES_Encrypt(username)
        encrypted_password = AES_Encrypt(password)

        params = {
            "fid": -1,
            "uname": encrypted_username,
            "password": encrypted_password,
            "refer": (
                "http%3A%2F%2Foffice.chaoxing.com%2Ffront%2Fthird"
                "%2Fapps%2Fseat%2Fcode%3Fid%3D4219%26seatNum%3D380"
            ),
            "t": True,
        }

        for attempt in range(max_retries):
            try:
                response = self.requests.post(
                    url=self.login_url, params=params, verify=False, timeout=15
                )
                
                if not response.text:
                    logging.warning(f"登录响应为空，重试 {attempt+1}/{max_retries}")
                    time.sleep(1)
                    continue
                
                try:
                    result = response.json()
                except json.JSONDecodeError:
                    text = response.text[:500] if response.text else "空响应"
                    logging.warning(
                        f"登录响应不是有效JSON ({attempt+1}/{max_retries}): {text[:100]}..."
                    )
                    time.sleep(1)
                    continue
                
                if result.get("status"):
                    logging.info(f"用户 {username} 登录成功")
                    return True, ""
                else:
                    msg = result.get("msg2", result.get("msg", "未知错误"))
                    logging.warning(f"用户 {username} 登录失败: {msg}")
                    return False, msg
                    
            except requests.RequestException as e:
                logging.warning(f"登录请求异常 ({attempt+1}/{max_retries}): {e}")
                time.sleep(1)
        
        logging.error(f"用户 {username} 登录失败，已重试 {max_retries} 次")
        return False, f"登录请求失败，已重试 {max_retries} 次"

    # ─── GPS位置模拟 ──────────────────────────────────────────

    def set_location(self, latitude: float, longitude: float, address: str = ""):
        """
        设置模拟GPS位置
        
        Args:
            latitude: 纬度（如 30.2595 对应武汉大学）
            longitude: 经度（如 114.3671 对应武汉大学）
            address: 位置描述文本
        
        常用高校参考坐标:
            武汉大学:     30.5427, 114.3628
            华中科技大学: 30.5154, 114.4214
            浙江大学:     30.2634, 120.1236
            南京大学:     32.1161, 118.9588
            北京大学:     39.9869, 116.3058
            清华大学:     40.0084, 116.3164
        """
        self.default_location = {
            "latitude": latitude,
            "longitude": longitude,
            "address": address or f"({latitude:.4f}, {longitude:.4f})",
        }
        logging.info(
            f"GPS位置已设置: lat={latitude}, lng={longitude}, addr={self.default_location['address']}"
        )

    def get_location(self):
        """获取当前模拟的GPS位置"""
        return self.default_location.copy()

    # ─── 预约信息查询 ─────────────────────────────────────────

    def get_reserve_info(self, roomid: str, seatid: str):
        """
        获取预约信息，提取二维码中的固定值(reserveId)
        
        这是签到的核心步骤：
        签到二维码中的固定值就是reserveId，从预约信息页面提取后
        可直接传递给签到接口完成签到，无需实际扫描二维码。
        
        Args:
            roomid: 房间ID（如 "6913"）
            seatid: 座位号（如 "011"）
        
        Returns:
            dict: {
                "reserve_id": str,     # 预约ID（签到所需的关键参数）
                "room_name": str,      # 房间名称
                "seat_num": str,       # 座位号
                "status": str,         # 预约状态
                "start_time": str,     # 开始时间
                "end_time": str,       # 结束时间
                "raw": dict            # 原始响应数据
            }
            失败返回 None
        """
        url = f"{self.reserve_info_url}?id={roomid}&seatNum={seatid}"
        try:
            resp = self.requests.get(
                url, headers=self.headers, verify=False, timeout=10
            )
            text = resp.text

            # 解析JSON响应
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                # 尝试正则提取reserveId
                match = re.findall(r'"id":(\d+)', text)
                if match:
                    return {
                        "reserve_id": match[0],
                        "room_name": "",
                        "seat_num": seatid,
                        "status": "unknown",
                        "start_time": "",
                        "end_time": "",
                        "raw": {},
                    }
                logging.error(f"无法解析预约信息响应: {text[:200]}")
                return None

            # 提取关键信息
            if data.get("success") is not False and "data" in data:
                info = data["data"]
                # reserveId可能在不同的字段中
                reserve_id = str(
                    info.get("id", "")
                    or info.get("reserveId", "")
                    or info.get("reserve_id", "")
                )
                return {
                    "reserve_id": reserve_id,
                    "room_name": info.get("roomName", ""),
                    "seat_num": str(info.get("seatNum", seatid)),
                    "status": info.get("status", ""),
                    "start_time": info.get("startTime", ""),
                    "end_time": info.get("endTime", ""),
                    "raw": info,
                }
            else:
                # 尝试从纯文本中提取
                match = re.findall(r'"id":(\d+)', text)
                if match:
                    return {
                        "reserve_id": match[0],
                        "room_name": "",
                        "seat_num": seatid,
                        "status": "unknown",
                        "start_time": "",
                        "end_time": "",
                        "raw": {},
                    }

            logging.warning(f"预约信息为空或格式异常: {text[:200]}")
            
            # 如果从座位信息接口获取失败，尝试从用户预约列表获取
            logging.info("尝试从用户预约列表获取预约信息...")
            list_result = self._get_reserve_info_from_list(roomid, seatid)
            if list_result:
                return list_result
            
            # 添加调试信息：输出用户当前的所有预约
            try:
                reservations = self.get_current_reservations()
                if reservations:
                    logging.info(f"用户当前预约列表 ({len(reservations)}):")
                    for i, res in enumerate(reservations):
                        logging.info(f"  [{i+1}] roomId={res.get('roomId', 'N/A')}, seatNum={res.get('seatNum', 'N/A')}, id={res.get('id', 'N/A')}, status={res.get('status', 'N/A')}")
                else:
                    logging.info("用户当前没有任何预约")
            except Exception as e:
                logging.error(f"获取预约列表失败: {e}")
            
            return None

        except requests.RequestException as e:
            logging.error(f"请求预约信息失败: {e}")
            # 如果请求失败，尝试从用户预约列表获取
            logging.info("尝试从用户预约列表获取预约信息...")
            list_result = self._get_reserve_info_from_list(roomid, seatid)
            if list_result:
                return list_result
            
            # 添加调试信息
            try:
                reservations = self.get_current_reservations()
                logging.info(f"用户当前预约列表: {reservations}")
            except Exception as e:
                logging.error(f"获取预约列表失败: {e}")
            
            return None
    
    def _get_reserve_info_from_list(self, roomid: str, seatid: str):
        """
        从用户预约列表中获取指定座位的预约信息
        
        Args:
            roomid: 房间ID
            seatid: 座位号
        
        Returns:
            dict: 预约信息，失败返回 None
        """
        try:
            reservations = self.get_current_reservations()
            if not reservations:
                logging.warning("用户当前没有有效的预约")
                return None
            
            # 匹配房间和座位
            for res in reservations:
                res_room_id = str(res.get("roomId", ""))
                res_seat_num = str(res.get("seatNum", ""))
                
                # 尝试多种匹配方式
                if (res_room_id == roomid or str(res.get("roomid", "")) == roomid) and \
                   (res_seat_num == seatid or str(res.get("seatid", "")) == seatid):
                    reserve_id = str(
                        res.get("id", "")
                        or res.get("reserveId", "")
                        or res.get("reserve_id", "")
                    )
                    if reserve_id:
                        logging.info(f"从预约列表找到预约: reserveId={reserve_id}, room={roomid}, seat={seatid}")
                        return {
                            "reserve_id": reserve_id,
                            "room_name": res.get("roomName", ""),
                            "seat_num": res_seat_num,
                            "status": res.get("status", ""),
                            "start_time": res.get("startTime", ""),
                            "end_time": res.get("endTime", ""),
                            "raw": res,
                        }
            
            logging.warning(f"在预约列表中未找到匹配的预约 (room={roomid}, seat={seatid})")
            return None
            
        except Exception as e:
            logging.error(f"从预约列表获取信息失败: {e}")
            return None

    def extract_reserve_id_from_qr_url(self, qr_url: str):
        """
        从签到二维码URL中提取reserveId
        
        二维码URL格式示例:
        https://office.chaoxing.com/front/third/apps/seat/index
            ?fidEnc=92329df6bdb2d3ec
            &num=011
            &reserveId=184471363
            &room=6913
        
        Args:
            qr_url: 签到二维码解码后的URL
        
        Returns:
            dict: {"reserve_id": str, "room_id": str, "seat_num": str, "fid_enc": str}
        """
        params = {}
        if "?" in qr_url:
            query = qr_url.split("?")[1]
            for pair in query.split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    params[key] = value

        return {
            "reserve_id": params.get("reserveId", ""),
            "room_id": params.get("room", ""),
            "seat_num": params.get("num", ""),
            "fid_enc": params.get("fidEnc", ""),
        }

    # ─── 签到核心逻辑 ─────────────────────────────────────────

    def execute_signin(
        self, roomid: str = "", seatid: str = "", reserve_id: str = ""
    ):
        """
        执行单次签到操作
        
        Args:
            roomid: 房间ID（可选）
            seatid: 座位号（可选）
            reserve_id: 预约ID（优先使用，如果提供则直接签到）
        
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "reserve_id": str,
                "roomid": str,
                "seatid": str,
                "location": dict
            }
        """
        # 1. 如果提供了reserve_id，直接使用
        if not reserve_id:
            # 尝试获取reserveId
            info = self.get_reserve_info(roomid, seatid)
            if not info or not info.get("reserve_id"):
                return {
                    "success": False,
                    "message": f"无法获取预约ID，可能当前无有效预约 (room={roomid}, seat={seatid})",
                    "reserve_id": "",
                    "roomid": roomid,
                    "seatid": seatid,
                    "location": self.default_location,
                }
            reserve_id = info["reserve_id"]

        logging.info(
            f"开始签到: room={roomid}, seat={seatid}, reserveId={reserve_id}"
        )

        # 2. 提交签到请求
        #    签到接口使用GET请求，将reserveId作为id参数传递
        url = f"{self.sign_url}?id={reserve_id}"

        # 添加GPS位置参数（如果服务器需要位置验证）
        loc = self.default_location
        url += (
            f"&latitude={loc['latitude']}"
            f"&longitude={loc['longitude']}"
            f"&address={loc['address']}"
        )

        try:
            resp = self.requests.get(
                url, headers=self.headers, verify=False, timeout=10
            )
            text = resp.text

            # 解析响应
            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                result = {"raw": text}

            if (
                result.get("success")
                or result.get("status") == "success"
                or '"success":true' in text
                or '"success": true' in text
            ):
                logging.info(
                    f"签到成功: room={roomid}, seat={seatid}, reserveId={reserve_id}"
                )
                return {
                    "success": True,
                    "message": "签到成功",
                    "reserve_id": reserve_id,
                    "roomid": roomid,
                    "seatid": seatid,
                    "location": self.default_location,
                }
            else:
                msg = result.get("msg", result.get("message", text[:200]))
                logging.warning(f"签到失败: {msg}")
                return {
                    "success": False,
                    "message": str(msg),
                    "reserve_id": reserve_id,
                    "roomid": roomid,
                    "seatid": seatid,
                    "location": self.default_location,
                }

        except requests.RequestException as e:
            logging.error(f"签到请求异常: {e}")
            return {
                "success": False,
                "message": f"网络请求异常: {e}",
                "reserve_id": reserve_id,
                "roomid": roomid,
                "seatid": seatid,
                "location": self.default_location,
            }
    
    def signin_with_reserve_id(self, reserve_id: str, roomid: str = "", seatid: str = ""):
        """
        使用预约ID直接签到
        
        Args:
            reserve_id: 预约ID（如从取消签到URL中获取的ID）
            roomid: 房间ID（可选，用于日志）
            seatid: 座位号（可选，用于日志）
        
        Returns:
            dict: 签到结果
        """
        logging.info(f"使用预约ID直接签到: reserveId={reserve_id}")
        return self.execute_signin(roomid=roomid, seatid=seatid, reserve_id=reserve_id)

    # ─── 分段式签到 ───────────────────────────────────────────

    def get_current_time_segment(self, time_configs: list):
        """
        判断当前时间落在哪个时间段内
        
        分段式签到场景：
        - 用户预约了多个时间段（如 10:30-14:15, 14:30-18:15, 18:30-22:30）
        - 每个时间段开始时需要单独签到
        - 此方法根据当前北京时间判断应执行哪个时段的签到
        
        Args:
            time_configs: 时间段配置列表，如 [["10:30","14:15"], ["14:30","18:15"]]
        
        Returns:
            (segment_index, start_time, end_time) 或 (None, None, None)
        """
        current_min = _current_minutes()

        for i, times in enumerate(time_configs):
            if len(times) < 2:
                continue
            start_min = _time_to_minutes(times[0])
            end_min = _time_to_minutes(times[1])
            if start_min <= current_min <= end_min:
                return i, times[0], times[1]

        return None, None, None

    def segmented_signin(self, config_users: list):
        """
        分段式自动签到
        
        遍历配置中的所有用户和时间段，对当前活跃的时间段执行签到。
        这是自动签到的主入口方法。
        
        重要: 每个用户使用独立的session，避免多用户登录时的session冲突
        
        配置说明:
            - 如果配置中提供了 reserveId，则直接使用该ID进行签到（手动填写模式）
            - 如果未提供 reserveId，则从 reservations.json 自动读取（自动获取模式）
            - 如果都没有，则尝试从座位信息接口获取
        
        Args:
            config_users: 用户配置列表，格式与config.json中的reserve数组一致
                每项包含: username, password, time, roomid, seatid, reserveId, daysofweek
        
        Returns:
            list: 签到结果列表
        """
        current_day = _beijing_dayofweek()
        results = []
        
        # 创建预约管理器实例
        rm = ReservationManager() if ReservationManager else None

        for user_config in config_users:
            username = user_config.get("username", "")
            password = user_config.get("password", "")
            times_list = user_config.get("time", [])
            roomid = str(user_config.get("roomid", ""))
            seatids = user_config.get("seatid", [])
            reserve_ids = user_config.get("reserveId", "")
            daysofweek = user_config.get("daysofweek", [])

            if isinstance(seatids, str):
                seatids = [seatids]
            
            # 处理reserveId配置（可以是字符串或列表）
            if isinstance(reserve_ids, str):
                reserve_ids = [reserve_ids] if reserve_ids else []

            # 检查今天是否需要签到
            if current_day not in daysofweek:
                logging.info(f"{username}: 今天({current_day})不在签到日范围内，跳过")
                continue

            # 判断当前时间段
            seg_time = times_list if isinstance(times_list[0], list) else [times_list]
            seg_idx, start_time, end_time = self.get_current_time_segment(seg_time)
            time_segment = f"{start_time}-{end_time}"

            if seg_idx is None:
                logging.info(
                    f"{username}: 当前时间 {_beijing_time_str()} 不在任何签到时段内"
                )
                continue

            logging.info(
                f"{username}: 当前时段 [{time_segment}]，开始签到"
            )

            # 为每个用户创建独立的session，避免session冲突
            self._create_new_session()
            
            # 登录
            self.get_login_status()
            login_ok, login_msg = self.login(username, password)
            if not login_ok:
                results.append(
                    {
                        "username": username,
                        "success": False,
                        "message": f"登录失败: {login_msg}",
                    }
                )
                continue

            self.requests.headers.update({"Host": "office.chaoxing.com"})

            # 优先级：配置的reserveId > 自动获取的reserveId > 接口获取
            if not reserve_ids and rm:
                # 从reservations.json自动读取预约ID
                today_date = _beijing_date_str()
                auto_reserve_id = rm.get_reservation(username, today_date, time_segment)
                if auto_reserve_id:
                    reserve_ids = [auto_reserve_id]
                    logging.info(f"{username}: 从预约记录自动获取到预约ID: {auto_reserve_id}")

            # 如果有reserveId（配置的或自动获取的），直接使用
            if reserve_ids:
                for ridx, reserve_id in enumerate(reserve_ids):
                    seatid = seatids[ridx] if ridx < len(seatids) else seatids[0]
                    result = self.execute_signin(roomid, str(seatid), reserve_id)
                    result["username"] = username
                    result["time_segment"] = time_segment
                    results.append(result)
            else:
                # 对每个座位签到（尝试从接口获取reserveId）
                for idx, seatid in enumerate(seatids):
                    result = self.execute_signin(roomid, str(seatid))
                    result["username"] = username
                    result["time_segment"] = time_segment
                    results.append(result)

        return results

    # ─── 签到取消 ─────────────────────────────────────────────

    def cancel_signin(self, reserve_id: str):
        """
        取消签到
        
        Args:
            reserve_id: 预约ID
        
        Returns:
            dict: {"success": bool, "message": str}
        """
        url = f"https://office.chaoxing.com/data/apps/seat/cancel?id={reserve_id}"
        try:
            resp = self.requests.get(
                url, headers=self.headers, verify=False, timeout=10
            )
            text = resp.text
            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                result = {"raw": text}

            if result.get("success") or '"success":true' in text:
                logging.info(f"取消签到成功: reserveId={reserve_id}")
                return {"success": True, "message": "取消签到成功"}
            else:
                msg = result.get("msg", text[:100])
                logging.warning(f"取消签到失败: {msg}")
                return {"success": False, "message": str(msg)}

        except requests.RequestException as e:
            logging.error(f"取消签到请求异常: {e}")
            return {"success": False, "message": str(e)}

    # ─── 预约状态查询 ─────────────────────────────────────────

    def get_current_reservations(self):
        """
        查询当前用户的所有有效预约
        
        Returns:
            list: 预约信息列表
        """
        url = "https://office.chaoxing.com/data/apps/seat/list"
        try:
            resp = self.requests.get(
                url, headers=self.headers, verify=False, timeout=10
            )
            data = resp.json()
            if data.get("success"):
                return data.get("data", {}).get("reserveList", [])
            return []
        except Exception as e:
            logging.error(f"查询预约列表失败: {e}")
            return []

    def check_signin_status(self, roomid: str, seatid: str):
        """
        检查指定座位的签到状态
        
        Args:
            roomid: 房间ID
            seatid: 座位号
        
        Returns:
            dict: 签到状态信息，含 is_signedin 字段
        """
        info = self.get_reserve_info(roomid, seatid)
        if not info:
            return {"is_signedin": False, "has_reservation": False}

        status = info.get("status", "")
        return {
            "is_signedin": status in ("signIn", "sign", "signed", "已签到"),
            "has_reservation": True,
            "reserve_id": info.get("reserve_id"),
            "status": status,
            "start_time": info.get("start_time"),
            "end_time": info.get("end_time"),
        }

    # ─── 定时自动签到（用于持续运行场景）──────────────────────

    def run_scheduled_signin(self, config_users: list, check_interval: int = 60):
        """
        定时循环签到模式
        
        持续运行，每隔 check_interval 秒检查一次是否需要签到。
        适用于长期部署（如GitHub Actions、云服务器等）。
        
        Args:
            config_users: 用户配置列表
            check_interval: 检查间隔（秒），默认60秒
        
        Returns:
            None（持续运行直到所有用户签到完成或超时）
        """
        max_run_seconds = 3600  # 最多运行1小时
        start_time = time.time()
        signed_users = set()

        while time.time() - start_time < max_run_seconds:
            current_day = _beijing_dayofweek()
            current_time_str = _beijing_time_str()

            for user_config in config_users:
                username = user_config.get("username", "")
                daysofweek = user_config.get("daysofweek", [])

                if current_day not in daysofweek:
                    continue

                times_list = user_config.get("time", [])
                if not isinstance(times_list[0], list):
                    times_list = [times_list]

                seg_idx, start_time_str, end_time_str = (
                    self.get_current_time_segment(times_list)
                )

                if seg_idx is None:
                    continue

                # 生成唯一标识：用户+时段
                user_seg_key = f"{username}_{start_time_str}_{end_time_str}"
                if user_seg_key in signed_users:
                    continue

                logging.info(
                    f"[{current_time_str}] 检测到签到时段: {username} "
                    f"[{start_time_str}-{end_time_str}]"
                )

                results = self.segmented_signin([user_config])
                for r in results:
                    if r.get("success"):
                        signed_users.add(user_seg_key)
                        logging.info(
                            f"用户 {username} 时段 [{start_time_str}-{end_time_str}] "
                            f"签到成功！"
                        )

                # 检查是否所有用户都已完成
                total_segments = 0
                for uc in config_users:
                    u_day = uc.get("daysofweek", [])
                    if current_day not in u_day:
                        continue
                    tl = uc.get("time", [])
                    if not isinstance(tl[0], list):
                        tl = [tl]
                    total_segments += len(tl)

                if len(signed_users) >= total_segments:
                    logging.info("所有用户所有时段签到完成！")
                    return

            time.sleep(check_interval)

        logging.info("签到定时任务结束（超时或全部完成）")