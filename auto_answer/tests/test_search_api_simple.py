import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from search_api import SearchAPI


class TestSearchAPI(unittest.TestCase):
    def setUp(self):
        self.local_db_config = {
            "search_api": {"enabled": False, "api_url": "", "api_key": "", "timeout": 10},
            "local_database": {"enabled": True, "file_path": ":memory:"}
        }

    def test_local_database_search(self):
        search_api = SearchAPI(self.local_db_config)
        
        search_api.add_to_local_database(
            "测试题目内容",
            "A",
            "单选题",
            "A.选项1|B.选项2"
        )
        
        result = search_api.search_answer("测试题目内容", "单选题")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["answer"], "A")
        self.assertEqual(result["source"], "local")

    def test_local_database_empty(self):
        search_api = SearchAPI(self.local_db_config)
        
        result = search_api.search_answer("不存在的题目", "单选题")
        
        self.assertFalse(result["success"])
        self.assertEqual(result["answer"], "")

    def test_add_to_local_database(self):
        search_api = SearchAPI(self.local_db_config)
        
        search_api.add_to_local_database(
            "Python的创始人是谁？",
            "Guido van Rossum",
            "单选题",
            "A.Guido|B.Tim|C.Larry|D.Dennis"
        )
        
        result = search_api.search_answer("Python的创始人", "单选题")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["answer"], "Guido van Rossum")

    def test_get_local_statistics(self):
        search_api = SearchAPI(self.local_db_config)
        
        search_api.add_to_local_database("题目1", "A", "单选题")
        search_api.add_to_local_database("题目2", "AB", "多选题")
        search_api.add_to_local_database("题目3", "对", "判断题")
        
        stats = search_api.get_local_statistics()
        
        self.assertEqual(stats["total"], 3)

    def test_config_disabled_both(self):
        config = {
            "search_api": {"enabled": False, "api_url": "", "api_key": "", "timeout": 10},
            "local_database": {"enabled": False, "file_path": ":memory:"}
        }
        search_api = SearchAPI(config)
        
        result = search_api.search_answer("测试题目")
        
        self.assertFalse(result["success"])

    def test_local_database_duplicate_entry(self):
        search_api = SearchAPI(self.local_db_config)
        
        search_api.add_to_local_database("重复题目", "A", "单选题")
        search_api.add_to_local_database("重复题目", "B", "多选题")
        
        result = search_api.search_answer("重复题目")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["answer"], "B")