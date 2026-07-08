import os
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from anti_detection import AntiDetection
from question_parser import QuestionParser
from search_api import SearchAPI


class BrowserAutomation:
    def __init__(self, config: dict):
        self.config = config
        self.driver = None
        self.anti_detection = None
        self.question_parser = QuestionParser()
        self.search_api = SearchAPI(config)
        
        self.username = config.get("login", {}).get("username", "")
        self.password = config.get("login", {}).get("password", "")
        self.login_url = config.get("login", {}).get("login_url", "")
        self.browser_type = config.get("browser", {}).get("type", "chrome")
        self.headless = config.get("browser", {}).get("headless", False)
        self.auto_submit = config.get("auto_submit", True)
        
        self.start_time = 0
        self.total_time_min = config.get("delay", {}).get("total_time_min", 180)

    def init_browser(self):
        """初始化浏览器，配置防检测参数"""
        try:
            if self.browser_type.lower() == "chrome":
                # 使用webdriver-manager自动管理Chrome驱动
                service = ChromeService(ChromeDriverManager().install())
                
                options = ChromeOptions()
                self._configure_chrome_options(options)
                
                self.driver = webdriver.Chrome(service=service, options=options)
            
            elif self.browser_type.lower() == "edge":
                # 使用webdriver-manager自动管理Edge驱动
                service = EdgeService(EdgeChromiumDriverManager().install())
                
                options = EdgeOptions()
                self._configure_edge_options(options)
                
                self.driver = webdriver.Edge(service=service, options=options)
            
            else:
                raise ValueError(f"不支持的浏览器类型: {self.browser_type}")
            
            # 设置窗口大小
            window_size = self.config.get("browser", {}).get("window_size", "1920,1080")
            width, height = map(int, window_size.split(","))
            self.driver.set_window_size(width, height)
            
            # 初始化防检测模块
            self.anti_detection = AntiDetection(self.driver, self.config)
            
            print(f"浏览器启动成功: {self.browser_type}")
            return True
            
        except Exception as e:
            print(f"浏览器启动失败: {e}")
            return False

    def _configure_chrome_options(self, options: ChromeOptions):
        """配置Chrome浏览器选项，添加防检测参数"""
        # 基本配置
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        
        # 防检测配置
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # 设置语言
        options.add_argument("--lang=zh-CN")
        
        # 模拟正常浏览器的User-Agent
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 如果是无头模式
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")

    def _configure_edge_options(self, options: EdgeOptions):
        """配置Edge浏览器选项，添加防检测参数"""
        # 基本配置
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        
        # 防检测配置
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # 设置语言
        options.add_argument("--lang=zh-CN")
        
        # 模拟正常浏览器的User-Agent
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0")
        
        # 如果是无头模式
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")

    def bypass_automation_detection(self):
        """绕过浏览器自动化检测"""
        if not self.driver:
            return
        
        try:
            # 执行JavaScript移除自动化标识
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 添加额外的防检测措施
            self.driver.execute_script("""
                // 模拟真实的navigator属性
                navigator.__proto__.plugins = [1, 2, 3, 4, 5];
                navigator.__proto__.languages = ['zh-CN', 'zh', 'en'];
                
                // 模拟真实的WebGL渲染器
                const originalGetContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type) {
                    const context = originalGetContext.call(this, type);
                    if (type === 'webgl' || type === 'experimental-webgl') {
                        const getParameter = context.getParameter.bind(context);
                        context.getParameter = function(pname) {
                            if (pname === 37445) {
                                return 'WebKit WebGL';
                            }
                            if (pname === 37446) {
                                return 'WebKit';
                            }
                            return getParameter(pname);
                        };
                    }
                    return context;
                };
            """)
            
            print("自动化检测绕过完成")
            
        except Exception as e:
            print(f"绕过检测失败: {e}")

    def login(self):
        """登录超星学习通"""
        if not self.driver or not self.username or not self.password:
            print("登录信息不完整")
            return False
        
        try:
            print(f"正在登录: {self.username}")
            
            # 打开登录页面
            self.driver.get(self.login_url)
            self.anti_detection.random_delay(2, 4)
            
            # 等待页面加载
            self._wait_for_page_load()
            
            # 绕过检测
            self.bypass_automation_detection()
            
            # 查找用户名输入框
            username_input = self._find_element((By.ID, "phone"), 10)
            if not username_input:
                username_input = self._find_element((By.NAME, "username"), 10)
            if not username_input:
                username_input = self._find_element((By.CSS_SELECTOR, "input[placeholder*='手机号']"), 10)
            
            # 输入用户名
            if username_input:
                self.anti_detection.human_type(username_input, self.username)
            else:
                print("未找到用户名输入框")
                return False
            
            # 查找密码输入框
            password_input = self._find_element((By.ID, "pwd"), 10)
            if not password_input:
                password_input = self._find_element((By.NAME, "password"), 10)
            if not password_input:
                password_input = self._find_element((By.CSS_SELECTOR, "input[placeholder*='密码']"), 10)
            
            # 输入密码
            if password_input:
                self.anti_detection.human_type(password_input, self.password)
            else:
                print("未找到密码输入框")
                return False
            
            # 检测并处理验证码
            if not self._handle_captcha():
                return False
            
            # 查找登录按钮
            login_button = self._find_element((By.ID, "loginBtn"), 10)
            if not login_button:
                login_button = self._find_element((By.CSS_SELECTOR, "button[type='submit']"), 10)
            if not login_button:
                login_button = self._find_element((By.CSS_SELECTOR, ".login-btn"), 10)
            
            # 点击登录
            if login_button:
                self.anti_detection.human_click(login_button)
                self.anti_detection.random_delay(3, 5)
            else:
                print("未找到登录按钮")
                return False
            
            # 再次检测验证码（登录失败后可能出现）
            if self._is_captcha_present():
                print("登录失败，需要重新输入验证码")
                return self._handle_captcha_and_retry()
            
            # 验证登录是否成功
            if self._check_login_success():
                print("登录成功")
                return True
            else:
                print("登录失败，请检查账号密码")
                return False
                
        except Exception as e:
            print(f"登录失败: {e}")
            return False

    def _wait_for_page_load(self, timeout=10):
        """等待页面加载完成"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            print("页面加载超时")

    def _find_element(self, locator, timeout=10):
        """查找元素，带超时和重试"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
        except TimeoutException:
            return None

    def _check_login_success(self):
        """检查登录是否成功"""
        try:
            # 检查是否跳转到主页或是否包含用户信息
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "header"))
            )
            return True
        except TimeoutException:
            # 检查URL是否改变（不是登录页面）
            if "login" not in self.driver.current_url.lower():
                return True
            return False

    def _is_captcha_present(self):
        """检测页面是否存在验证码"""
        captcha_selectors = [
            (By.ID, "captcha"),
            (By.ID, "yzm"),
            (By.CSS_SELECTOR, ".captcha"),
            (By.CSS_SELECTOR, ".yzm"),
            (By.CSS_SELECTOR, "input[placeholder*='验证码']"),
            (By.CSS_SELECTOR, "img[src*='captcha']"),
            (By.CSS_SELECTOR, "canvas"),
            (By.ID, "nc_1_n1z"),
            (By.CSS_SELECTOR, ".nc-container"),
        ]
        
        for selector in captcha_selectors:
            try:
                element = self.driver.find_element(*selector)
                if element.is_displayed():
                    return True
            except NoSuchElementException:
                continue
        return False

    def _handle_captcha(self):
        """处理验证码 - 等待用户手动完成验证"""
        if not self._is_captcha_present():
            return True
        
        print("=" * 50)
        print("检测到验证码！请在浏览器窗口中完成验证")
        print("=" * 50)
        print("操作提示：")
        print("1. 在弹出的浏览器窗口中完成滑块/图片验证码")
        print("2. 完成后点击登录按钮")
        print("3. 脚本会自动检测验证完成状态")
        print("=" * 50)
        print("等待验证完成...")
        
        max_wait_time = 120
        check_interval = 2
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                # 检查验证码是否消失
                if not self._is_captcha_present():
                    print("验证码已处理完成")
                    return True
                
                # 检查是否已成功登录（页面跳转）
                if "login" not in self.driver.current_url.lower():
                    print("检测到页面跳转，登录可能已成功")
                    return True
                
                # 检查是否出现登录成功的元素
                try:
                    self.driver.find_element(By.ID, "header")
                    print("检测到登录成功")
                    return True
                except NoSuchElementException:
                    pass
                
                time.sleep(check_interval)
                elapsed_time += check_interval
                
                if elapsed_time % 10 == 0:
                    print(f"已等待 {elapsed_time} 秒，请尽快完成验证码...")
                    
            except Exception as e:
                print(f"轮询检测异常: {e}")
                time.sleep(check_interval)
                elapsed_time += check_interval
        
        print(f"验证码等待超时（{max_wait_time}秒）")
        return False

    def _handle_captcha_and_retry(self):
        """处理验证码并重新登录"""
        if not self._handle_captcha():
            return False
        
        try:
            # 重新查找并点击登录按钮
            login_button = self._find_element((By.ID, "loginBtn"), 10)
            if not login_button:
                login_button = self._find_element((By.CSS_SELECTOR, "button[type='submit']"), 10)
            if not login_button:
                login_button = self._find_element((By.CSS_SELECTOR, ".login-btn"), 10)
            
            if login_button:
                self.anti_detection.human_click(login_button)
                self.anti_detection.random_delay(3, 5)
                
                # 验证登录是否成功
                if self._check_login_success():
                    print("登录成功")
                    return True
            
            print("重新登录失败")
            return False
        except Exception as e:
            print(f"重新登录失败: {e}")
            return False

    def navigate_to_exam(self, exam_url=None):
        """导航到考试/作业页面"""
        if not self.driver:
            return False
            
        try:
            if exam_url:
                self.driver.get(exam_url)
            else:
                # 如果没有提供URL，等待用户手动导航
                print("请在浏览器中打开考试/作业页面，然后按回车继续...")
                input()
            
            self._wait_for_page_load()
            self.anti_detection.random_delay(2, 4)
            print("已进入考试/作业页面")
            return True
            
        except Exception as e:
            print(f"导航失败: {e}")
            return False

    def start_auto_answer(self):
        """开始自动答题"""
        if not self.driver:
            return
        
        self.start_time = time.time()
        print("=" * 50)
        print("开始自动答题")
        print("=" * 50)
        
        # 解析题目
        questions = self.question_parser.parse_page(self.driver.page_source)
        print(f"共识别到 {len(questions)} 道题目")
        
        if not questions:
            print("未识别到题目，请检查页面是否正确")
            return
        
        # 逐个答题
        for index, question in enumerate(questions, 1):
            print(f"\n--- 第 {index} 题 ({question['type']}) ---")
            print(f"题目: {question['content'][:50]}...")
            
            # 随机滚动页面
            self.anti_detection.random_scroll()
            
            # 搜索答案
            search_text = self.question_parser.format_question_for_search(question)
            answer_result = self.search_api.search_answer(search_text, question["type"])
            
            if answer_result["success"]:
                answer = answer_result["answer"]
                print(f"找到答案: {answer} (来源: {answer_result['source']})")
                
                # 填写答案
                self._fill_answer(question, answer)
                
                # 模拟修改答案（随机）
                if self.anti_detection.should_fake_modify():
                    self._fake_modify_answer(question)
            else:
                print("未找到答案，跳过此题")
            
            # 答题间隔
            delay = self.anti_detection.random_delay()
            print(f"等待 {delay:.2f} 秒...")
            
            # 检查总答题时长
            self._check_total_time(len(questions), index)
        
        print("\n" + "=" * 50)
        print("所有题目已作答完成")
        print("=" * 50)
        
        # 自动提交
        if self.auto_submit:
            self._submit_exam()

    def _fill_answer(self, question, answer):
        """填写答案"""
        try:
            if question["type"] == "单选题":
                self._fill_single_choice(question, answer)
            elif question["type"] == "多选题":
                self._fill_multiple_choice(question, answer)
            elif question["type"] == "判断题":
                self._fill_judge(question, answer)
            elif question["type"] == "填空题":
                self._fill_fill_blank(question, answer)
        except Exception as e:
            print(f"填写答案失败: {e}")

    def _fill_single_choice(self, question, answer):
        """填写单选题答案"""
        # 找到选项元素并点击
        for option in question["options"]:
            if option["key"] == answer or option["content"] in answer:
                # 查找选项对应的元素
                try:
                    # 尝试多种方式查找选项
                    option_selector = f"div[class*='option']:contains('{option['content'][:10]}')"
                    option_element = self._find_element((By.CSS_SELECTOR, option_selector), 5)
                    
                    if not option_element and question["question_id"]:
                        option_element = self._find_element(
                            (By.XPATH, f"//div[@id='{question['question_id']}']//*[contains(text(), '{option['content'][:10]}')]"),
                            5
                        )
                    
                    if option_element:
                        self.anti_detection.human_click(option_element)
                        print(f"已选择: {option['key']}.{option['content']}")
                        return
                except Exception as e:
                    print(f"选择选项失败: {e}")
        
        print("未找到匹配的选项")

    def _fill_multiple_choice(self, question, answer):
        """填写多选题答案"""
        # 答案可能是多个字母，如 "AB" 或 "A,B"
        answer_keys = []
        
        # 解析答案
        if isinstance(answer, str):
            # 提取字母
            answer_keys = [c.upper() for c in answer if c.isalpha()]
        
        print(f"多选题答案: {answer_keys}")
        
        for key in answer_keys:
            for option in question["options"]:
                if option["key"] == key:
                    try:
                        option_selector = f"div[class*='option']:contains('{option['content'][:10]}')"
                        option_element = self._find_element((By.CSS_SELECTOR, option_selector), 5)
                        
                        if option_element:
                            self.anti_detection.human_click(option_element)
                            print(f"已选择: {option['key']}.{option['content']}")
                    except Exception as e:
                        print(f"选择选项失败: {e}")

    def _fill_judge(self, question, answer):
        """填写判断题答案"""
        # 判断题答案可能是 "对"/"错"、"正确"/"错误"、"T"/"F"、"√"/"×"
        answer_lower = str(answer).lower()
        
        is_true = any(keyword in answer_lower for keyword in ["对", "正确", "true", "t", "√"])
        
        try:
            # 查找判断题选项
            if is_true:
                option_element = self._find_element((By.XPATH, "//*[contains(text(), '对') or contains(text(), '正确') or contains(text(), '√')]"), 5)
            else:
                option_element = self._find_element((By.XPATH, "//*[contains(text(), '错') or contains(text(), '错误') or contains(text(), '×')]"), 5)
            
            if option_element:
                self.anti_detection.human_click(option_element)
                print(f"已选择: {'正确' if is_true else '错误'}")
        except Exception as e:
            print(f"选择判断题答案失败: {e}")

    def _fill_fill_blank(self, question, answer):
        """填写填空题答案"""
        try:
            # 查找填空题输入框
            input_element = self._find_element((By.CSS_SELECTOR, "input[type='text']"), 5)
            
            if input_element:
                self.anti_detection.human_type(input_element, answer)
                print(f"已填写填空答案: {answer}")
        except Exception as e:
            print(f"填写填空题答案失败: {e}")

    def _fake_modify_answer(self, question):
        """模拟修改答案操作：先选错误选项，再改回正确答案"""
        print("模拟修改答案...")
        
        try:
            if question["options"] and len(question["options"]) > 1:
                # 随机选择一个错误选项
                wrong_option = random.choice(question["options"])
                
                # 点击错误选项
                option_selector = f"div[class*='option']:contains('{wrong_option['content'][:10]}')"
                option_element = self._find_element((By.CSS_SELECTOR, option_selector), 5)
                
                if option_element:
                    self.anti_detection.human_click(option_element)
                    self.anti_detection.random_delay(1, 2)
                    
                    # 再次点击取消选择（如果是单选）
                    if question["type"] == "单选题":
                        self.anti_detection.human_click(option_element)
                
                print(f"模拟修改: 先选择了错误选项 {wrong_option['key']}")
                
        except Exception as e:
            print(f"模拟修改答案失败: {e}")

    def _check_total_time(self, total_questions, current_index):
        """检查总答题时长是否达到要求"""
        elapsed_time = time.time() - self.start_time
        remaining_questions = total_questions - current_index
        
        # 计算预计剩余时间
        avg_time_per_question = elapsed_time / current_index if current_index > 0 else 1
        estimated_total_time = elapsed_time + remaining_questions * avg_time_per_question
        
        # 如果预计总时间不足，增加延迟
        if estimated_total_time < self.total_time_min * 60:
            extra_delay = random.uniform(2, 5)
            print(f"增加延迟 {extra_delay:.2f} 秒以满足总答题时长要求")
            time.sleep(extra_delay)

    def _submit_exam(self):
        """提交试卷"""
        print("\n准备提交试卷...")
        self.anti_detection.random_delay(3, 5)
        
        try:
            # 查找提交按钮
            submit_button = self._find_element((By.ID, "submitBtn"), 10)
            if not submit_button:
                submit_button = self._find_element((By.CSS_SELECTOR, "button[class*='submit']"), 10)
            if not submit_button:
                submit_button = self._find_element((By.CSS_SELECTOR, ".btn-submit"), 10)
            
            if submit_button:
                # 滚动到按钮位置
                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                self.anti_detection.random_delay(1, 2)
                
                # 点击提交
                self.anti_detection.human_click(submit_button)
                
                # 处理确认弹窗
                try:
                    confirm_button = self._find_element((By.XPATH, "//button[contains(text(), '确定')]"), 5)
                    if confirm_button:
                        self.anti_detection.human_click(confirm_button)
                        print("试卷已提交")
                except Exception as e:
                    print(f"提交确认弹窗处理失败: {e}")
            else:
                print("未找到提交按钮，请手动提交")
                
        except Exception as e:
            print(f"提交失败: {e}")

    def close_browser(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")

    def get_current_url(self):
        """获取当前页面URL"""
        if self.driver:
            return self.driver.current_url
        return ""