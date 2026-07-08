import pytest
import os
from question_parser import QuestionParser


class TestQuestionParser:
    """题目解析模块测试用例"""

    def test_single_choice_parsing(self, test_data_dir):
        """TC-QP-001: 单选题解析测试"""
        parser = QuestionParser()
        
        with open(os.path.join(test_data_dir, "test_single.html"), "r", encoding="utf-8") as f:
            html = f.read()
        
        questions = parser.parse_page(html)
        
        assert len(questions) == 2
        assert questions[0]["type"] == "单选题"
        assert "Python的内置数据类型" in questions[0]["content"]
        assert len(questions[0]["options"]) == 4
        assert questions[0]["options"][0]["key"] == "A"
        assert questions[0]["options"][0]["content"] == "List"

    def test_multiple_choice_parsing(self, test_data_dir):
        """TC-QP-002: 多选题解析测试"""
        parser = QuestionParser()
        
        with open(os.path.join(test_data_dir, "test_multiple.html"), "r", encoding="utf-8") as f:
            html = f.read()
        
        questions = parser.parse_page(html)
        
        assert len(questions) == 2
        assert questions[0]["type"] == "多选题"
        assert "面向对象的特性" in questions[0]["content"]
        assert len(questions[0]["options"]) == 4

    def test_judge_parsing(self, test_data_dir):
        """TC-QP-003: 判断题解析测试"""
        parser = QuestionParser()
        
        with open(os.path.join(test_data_dir, "test_judge.html"), "r", encoding="utf-8") as f:
            html = f.read()
        
        questions = parser.parse_page(html)
        
        assert len(questions) == 2
        assert questions[0]["type"] == "判断题"
        assert "Python是一种编译型语言" in questions[0]["content"]

    def test_fill_blank_parsing(self, test_data_dir):
        """TC-QP-004: 填空题解析测试"""
        parser = QuestionParser()
        
        with open(os.path.join(test_data_dir, "test_fill.html"), "r", encoding="utf-8") as f:
            html = f.read()
        
        questions = parser.parse_page(html)
        
        assert len(questions) == 2
        assert questions[0]["type"] == "填空题"
        assert "定义函数的关键字" in questions[0]["content"]

    def test_empty_html(self):
        """TC-QP-005: 空HTML测试"""
        parser = QuestionParser()
        
        questions = parser.parse_page("")
        
        assert questions == []

    def test_invalid_html(self):
        """TC-QP-006: 无效HTML测试"""
        parser = QuestionParser()
        
        questions = parser.parse_page("<html><body><div>")
        
        assert questions == []

    def test_text_cleaning(self):
        """TC-QP-007: 文本清洗测试"""
        parser = QuestionParser()
        
        test_cases = [
            ("  测试   文本  ", "测试 文本"),
            ("\u3000测试文本\u3000", "测试文本"),
            ("测试\xa0文本", "测试 文本"),
            ("<script>alert('test')</script>测试", "<script>alert('test')</script>测试"),
        ]
        
        for input_text, expected in test_cases:
            result = parser._clean_text(input_text)
            assert result == expected

    def test_format_question_for_search(self):
        """格式化题目搜索文本测试"""
        parser = QuestionParser()
        
        question = {
            "content": "测试题目",
            "options": [
                {"key": "A", "content": "选项A"},
                {"key": "B", "content": "选项B"}
            ]
        }
        
        result = parser.format_question_for_search(question)
        
        assert "测试题目" in result
        assert "A.选项A" in result
        assert "B.选项B" in result

    def test_question_id_extraction(self, test_data_dir):
        """题目ID提取测试"""
        parser = QuestionParser()
        
        with open(os.path.join(test_data_dir, "test_single.html"), "r", encoding="utf-8") as f:
            html = f.read()
        
        questions = parser.parse_page(html)
        
        assert questions[0]["question_id"] == "q1"
        assert questions[1]["question_id"] == "q2"

    def test_option_parsing_various_formats(self):
        """不同格式选项解析测试"""
        parser = QuestionParser()
        
        html = """
        <div class="question_item">
            <div class="question_content">测试题目</div>
            <div class="option">A、选项A</div>
            <div class="option">B.选项B</div>
            <div class="option">C 选项C</div>
            <div class="option">d选项D</div>
        </div>
        """
        
        questions = parser.parse_page(html)
        
        assert len(questions[0]["options"]) == 4
        assert questions[0]["options"][0]["key"] == "A"
        assert questions[0]["options"][1]["key"] == "B"
        assert questions[0]["options"][2]["key"] == "C"
        assert questions[0]["options"][3]["key"] == "D"

    def test_question_type_detection_by_keyword(self):
        """关键词题型检测测试"""
        parser = QuestionParser()
        
        test_cases = [
            ("以下哪个是正确的？（单选）", "单选题"),
            ("以下哪些是正确的？（多选）", "多选题"),
            ("判断对错：", "判断题"),
            ("填空：______", "填空题"),
        ]
        
        for content, expected_type in test_cases:
            # 构造简单HTML测试题型检测
            html = f'<div class="question_item"><div class="question_content">{content}</div></div>'
            questions = parser.parse_page(html)
            if questions:
                assert questions[0]["type"] == expected_type

    def test_long_question_content(self):
        """长题目内容测试"""
        parser = QuestionParser()
        
        long_content = "这是一个非常长的题目内容，包含很多文字，用于测试题目解析模块是否能够正确处理长文本内容。" * 10
        html = f'<div class="question_item"><div class="question_content">{long_content}</div></div>'
        
        questions = parser.parse_page(html)
        
        assert len(questions) == 1
        assert long_content in questions[0]["content"]

    def test_question_with_special_characters(self):
        """特殊字符题目测试"""
        parser = QuestionParser()
        
        html = """
        <div class="question_item">
            <div class="question_content">数学公式：a² + b² = c²，测试特殊字符！@#$%^&*()</div>
            <div class="option">A. 正确</div>
            <div class="option">B. 错误</div>
        </div>
        """
        
        questions = parser.parse_page(html)
        
        assert len(questions) == 1
        assert "a² + b² = c²" in questions[0]["content"]

    def test_mixed_question_types(self):
        """混合题型测试"""
        parser = QuestionParser()
        
        html = """
        <div class="question_item">
            <div class="question_content">单选题：测试单选</div>
            <div class="option">A. 选项1</div>
            <div class="option">B. 选项2</div>
        </div>
        <div class="question_item">
            <div class="question_content">多选题：测试多选</div>
            <div class="option">A. 选项1</div>
            <div class="option">B. 选项2</div>
            <div class="option">C. 选项3</div>
        </div>
        <div class="question_item">
            <div class="question_content">判断题：测试判断</div>
            <div class="option">对</div>
            <div class="option">错</div>
        </div>
        """
        
        questions = parser.parse_page(html)
        
        assert len(questions) == 3
        assert questions[0]["type"] == "单选题"
        assert questions[1]["type"] == "多选题"
        assert questions[2]["type"] == "判断题"