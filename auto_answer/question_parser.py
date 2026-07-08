from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any


class QuestionParser:
    def __init__(self):
        self.question_type_map = {
            "single": "单选题",
            "multiple": "多选题",
            "judge": "判断题",
            "fill": "填空题"
        }

    def parse_page(self, page_source: str) -> List[Dict[str, Any]]:
        """解析页面中的所有题目"""
        soup = BeautifulSoup(page_source, "lxml")
        questions = []

        # 查找所有题目容器
        question_containers = soup.find_all(attrs={"class": re.compile(r"question_item|question-item|question")})
        
        if not question_containers:
            question_containers = soup.find_all("div", class_=re.compile(r"question"))

        for index, container in enumerate(question_containers, 1):
            question = self._parse_single_question(container, index)
            if question:
                questions.append(question)

        return questions

    def _parse_single_question(self, container, index: int) -> Dict[str, Any]:
        """解析单个题目"""
        question = {
            "index": index,
            "type": "",
            "content": "",
            "options": [],
            "answer_area": None,
            "question_id": ""
        }

        try:
            # 获取题目内容
            content_element = container.find("div", class_=re.compile(r"question_content|question-content|q-content"))
            if not content_element:
                content_element = container.find("div", class_=re.compile(r"q-title|question-title"))
            if not content_element:
                content_element = container.find("span", class_=re.compile(r"question"))

            if content_element:
                question["content"] = self._clean_text(content_element.get_text(strip=True))

            # 获取题目类型
            question["type"] = self._detect_question_type(container, question["content"])

            # 获取选项
            if question["type"] in ["单选题", "多选题", "判断题"]:
                question["options"] = self._parse_options(container)

            # 获取题目ID（用于定位元素）
            question["question_id"] = container.get("id", "")
            if not question["question_id"]:
                question["question_id"] = container.get("data-id", "")

            # 如果是填空题，找到输入框
            if question["type"] == "填空题":
                answer_input = container.find("input", type="text")
                if answer_input:
                    question["answer_area"] = {
                        "type": "input",
                        "selector": f'input[placeholder*="请输入"]' if answer_input.get("placeholder") else f'input[type="text"]'
                    }

            # 如果题目内容为空，尝试其他方式获取
            if not question["content"]:
                all_text = container.get_text(strip=True)
                if all_text:
                    question["content"] = all_text[:200]

        except Exception as e:
            print(f"解析题目 {index} 失败: {e}")

        # 只有当题目内容不为空时才返回
        return question if question["content"] else None

    def _detect_question_type(self, container, content: str) -> str:
        """检测题目类型"""
        # 优先从题目内容判断
        content_lower = content.lower()
        
        # 判断判断题
        if any(keyword in content_lower for keyword in ["判断", "正确", "错误", "true", "false"]):
            # 检查是否有对勾/叉选项
            options_text = container.get_text()
            if "√" in options_text or "×" in options_text or "对" in options_text or "错" in options_text:
                return "判断题"

        # 判断单选题
        if any(keyword in content_lower for keyword in ["单选", "唯一", "下列选项"]):
            return "单选题"

        # 判断多选题
        if any(keyword in content_lower for keyword in ["多选", "至少", "哪些"]):
            return "多选题"

        # 判断填空题
        if any(keyword in content_lower for keyword in ["填空", "填写", "__", "___", "____"]):
            return "填空题"

        # 从HTML结构判断
        option_count = len(container.find_all(attrs={"class": re.compile(r"option|choice")}))
        if option_count == 2:
            return "判断题"
        elif option_count <= 5:
            return "单选题"
        elif option_count > 5:
            return "多选题"

        # 默认返回单选题
        return "单选题"

    def _parse_options(self, container) -> List[Dict[str, str]]:
        """解析选项列表"""
        options = []
        
        # 查找选项元素
        option_elements = container.find_all(attrs={"class": re.compile(r"option|choice|answer-item")})
        
        if not option_elements:
            option_elements = container.find_all("div", recursive=False)
        
        for option in option_elements:
            option_text = self._clean_text(option.get_text(strip=True))
            if option_text and len(option_text) > 0:
                # 提取选项标识（A、B、C、D等）
                match = re.match(r"^([A-Da-d])[\.\uff0e、\s]", option_text)
                option_key = match.group(1).upper() if match else ""
                option_content = re.sub(r"^[A-Da-d][\.\uff0e、\s]", "", option_text)

                options.append({
                    "key": option_key,
                    "content": option_content.strip(),
                    "full_text": option_text
                })

        return options

    def _clean_text(self, text: str) -> str:
        """清洗文本，去除多余空格和特殊字符"""
        if not text:
            return ""
        
        # 去除多余空格
        text = re.sub(r"\s+", " ", text)
        # 去除首尾空格
        text = text.strip()
        # 去除特殊字符
        text = text.replace("\u3000", "").replace("\xa0", " ")
        
        return text

    def format_question_for_search(self, question: Dict[str, Any]) -> str:
        """格式化题目内容用于搜索"""
        formatted = question["content"]
        
        # 如果是选择题，添加选项
        if question["options"]:
            for opt in question["options"]:
                formatted += f" {opt['key']}.{opt['content']}"
        
        return formatted