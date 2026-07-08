import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from question_parser import QuestionParser


class TestQuestionParser(unittest.TestCase):
    def setUp(self):
        self.parser = QuestionParser()
        self.test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")

    def test_single_choice_parsing(self):
        with open(os.path.join(self.test_data_dir, "test_single.html"), "r", encoding="utf-8") as f:
            html = f.read()
        
        questions = self.parser.parse_page(html)
        
        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0]["type"], "单选题")
        self.assertIn("Python的内置数据类型", questions[0]["content"])
        self.assertEqual(len(questions[0]["options"]), 4)
        self.assertEqual(questions[0]["options"][0]["key"], "A")

    def test_multiple_choice_parsing(self):
        with open(os.path.join(self.test_data_dir, "test_multiple.html"), "r", encoding="utf-8") as f:
            html = f.read()
        
        questions = self.parser.parse_page(html)
        
        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0]["type"], "多选题")

    def test_judge_parsing(self):
        with open(os.path.join(self.test_data_dir, "test_judge.html"), "r", encoding="utf-8") as f:
            html = f.read()
        
        questions = self.parser.parse_page(html)
        
        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0]["type"], "判断题")

    def test_fill_blank_parsing(self):
        with open(os.path.join(self.test_data_dir, "test_fill.html"), "r", encoding="utf-8") as f:
            html = f.read()
        
        questions = self.parser.parse_page(html)
        
        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0]["type"], "填空题")

    def test_empty_html(self):
        questions = self.parser.parse_page("")
        self.assertEqual(questions, [])

    def test_invalid_html(self):
        questions = self.parser.parse_page("<html><body><div>")
        self.assertEqual(questions, [])

    def test_text_cleaning(self):
        test_cases = [
            ("  测试   文本  ", "测试 文本"),
            ("\u3000测试文本\u3000", "测试文本"),
            ("测试\xa0文本", "测试 文本"),
        ]
        
        for input_text, expected in test_cases:
            result = self.parser._clean_text(input_text)
            self.assertEqual(result, expected)

    def test_question_id_extraction(self):
        with open(os.path.join(self.test_data_dir, "test_single.html"), "r", encoding="utf-8") as f:
            html = f.read()
        
        questions = self.parser.parse_page(html)
        
        self.assertEqual(questions[0]["question_id"], "q1")
        self.assertEqual(questions[1]["question_id"], "q2")