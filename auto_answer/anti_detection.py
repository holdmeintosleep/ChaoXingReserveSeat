import random
import time
import math
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


class AntiDetection:
    def __init__(self, driver: WebDriver, config: dict):
        self.driver = driver
        self.config = config
        self.min_delay = config.get("delay", {}).get("min_delay", 1)
        self.max_delay = config.get("delay", {}).get("max_delay", 6)
        self.mouse_move_enabled = config.get("anti_detection", {}).get("mouse_move", True)
        self.random_scroll_enabled = config.get("anti_detection", {}).get("random_scroll", True)
        self.fake_modify_rate = config.get("anti_detection", {}).get("fake_modify_rate", 0.2)

    def random_delay(self, min_delay=None, max_delay=None):
        """随机延迟，模拟人工思考时间"""
        min_d = min_delay if min_delay is not None else self.min_delay
        max_d = max_delay if max_delay is not None else self.max_delay
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)
        return delay

    def human_mouse_move(self, element: WebElement):
        """模拟人类鼠标移动轨迹，禁止坐标瞬移"""
        if not self.mouse_move_enabled:
            return

        try:
            # 获取元素位置
            element_rect = element.rect
            target_x = element_rect["x"] + element_rect["width"] / 2
            target_y = element_rect["y"] + element_rect["height"] / 2

            # 获取当前鼠标位置（默认从页面左上角开始）
            current_x = random.randint(0, 200)
            current_y = random.randint(0, 200)

            # 生成贝塞尔曲线轨迹点
            points = self._generate_bezier_curve(current_x, current_y, target_x, target_y)

            # 逐步移动鼠标
            actions = ActionChains(self.driver)
            for i, (x, y) in enumerate(points):
                if i == 0:
                    actions.move_to_element_with_offset(element, x - element_rect["x"], y - element_rect["y"])
                else:
                    actions.move_by_offset(x - points[i-1][0], y - points[i-1][1])
                # 添加微小延迟，模拟真实移动速度
                time.sleep(random.uniform(0.005, 0.015))

            actions.perform()
            self.random_delay(0.1, 0.3)
        except Exception as e:
            print(f"鼠标移动失败: {e}")

    def _generate_bezier_curve(self, start_x, start_y, end_x, end_y, num_points=15):
        """生成贝塞尔曲线轨迹点，模拟真实鼠标移动"""
        # 随机生成两个控制点
        control1_x = start_x + random.uniform(-100, 100)
        control1_y = start_y + random.uniform(-100, 100)
        control2_x = end_x + random.uniform(-100, 100)
        control2_y = end_y + random.uniform(-100, 100)

        points = []
        for t in range(num_points + 1):
            t_norm = t / num_points
            # 三次贝塞尔曲线公式
            x = (1 - t_norm)**3 * start_x + 3 * (1 - t_norm)**2 * t_norm * control1_x + \
                3 * (1 - t_norm) * t_norm**2 * control2_x + t_norm**3 * end_x
            y = (1 - t_norm)**3 * start_y + 3 * (1 - t_norm)**2 * t_norm * control1_y + \
                3 * (1 - t_norm) * t_norm**2 * control2_y + t_norm**3 * end_y
            points.append((x, y))

        return points

    def random_scroll(self):
        """随机滚动页面，模拟人工读题时的页面浏览"""
        if not self.random_scroll_enabled:
            return

        try:
            # 随机决定是否滚动
            if random.random() < 0.3:
                return

            # 获取当前滚动位置和页面高度
            current_scroll = self.driver.execute_script("return window.scrollY;")
            page_height = self.driver.execute_script("return document.body.scrollHeight;")
            window_height = self.driver.execute_script("return window.innerHeight;")

            # 计算可滚动范围
            max_scroll = page_height - window_height
            if max_scroll <= 0:
                return

            # 随机滚动到新位置
            scroll_amount = random.uniform(-200, 200)
            new_scroll = max(0, min(max_scroll, current_scroll + scroll_amount))

            # 平滑滚动
            self._smooth_scroll(int(new_scroll))
            self.random_delay(0.5, 1.5)
        except Exception as e:
            print(f"页面滚动失败: {e}")

    def _smooth_scroll(self, target_position):
        """平滑滚动到目标位置"""
        current_position = self.driver.execute_script("return window.scrollY;")
        distance = target_position - current_position
        steps = 20
        step_distance = distance / steps

        for _ in range(steps):
            current_position += step_distance
            self.driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.02, 0.05))

    def should_fake_modify(self):
        """决定是否模拟修改答案操作"""
        return random.random() < self.fake_modify_rate

    def human_click(self, element: WebElement):
        """模拟人类点击行为：先移动鼠标，再点击"""
        self.human_mouse_move(element)
        time.sleep(random.uniform(0.1, 0.3))
        element.click()
        self.random_delay(0.2, 0.5)

    def human_type(self, element: WebElement, text: str):
        """模拟人类输入行为：逐字输入，带有随机间隔"""
        self.human_mouse_move(element)
        time.sleep(random.uniform(0.1, 0.3))
        element.click()
        time.sleep(random.uniform(0.1, 0.2))

        for char in text:
            element.send_keys(char)
            # 模拟真实打字速度：中文稍慢，英文稍快
            if '\u4e00' <= char <= '\u9fff':
                time.sleep(random.uniform(0.1, 0.3))
            else:
                time.sleep(random.uniform(0.05, 0.15))

        self.random_delay(0.2, 0.5)