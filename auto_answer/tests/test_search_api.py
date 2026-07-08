import pytest
import requests_mock
from search_api import SearchAPI


class TestSearchAPI:
    """搜题API模块测试用例"""

    def test_api_search_success(self, api_config):
        """TC-SA-001: API搜索正常测试"""
        with requests_mock.Mocker() as m:
            m.post(
                api_config["search_api"]["api_url"],
                json={"success": True, "answer": "A", "confidence": 0.95}
            )
            
            search_api = SearchAPI(api_config)
            result = search_api.search_answer("测试题目", "单选题")
            
            assert result["success"] is True
            assert result["answer"] == "A"
            assert result["source"] == "api"
            assert result["confidence"] == 0.95

    def test_api_search_fail(self, api_config):
        """TC-SA-002: API搜索失败测试"""
        with requests_mock.Mocker() as m:
            m.post(
                api_config["search_api"]["api_url"],
                json={"success": False, "answer": ""}
            )
            
            search_api = SearchAPI(api_config)
            result = search_api.search_answer("测试题目", "单选题")
            
            assert result["success"] is False
            assert result["answer"] == ""

    def test_api_timeout(self, api_config):
        """TC-SA-003: 网络超时测试"""
        with requests_mock.Mocker() as m:
            m.post(
                api_config["search_api"]["api_url"],
                exc=requests_mock.exceptions.Timeout
            )
            
            search_api = SearchAPI(api_config)
            result = search_api.search_answer("测试题目", "单选题")
            
            assert result["success"] is False
            assert result["answer"] == ""

    def test_local_database_search(self, local_db_config):
        """TC-SA-004: 本地数据库搜索测试"""
        search_api = SearchAPI(local_db_config)
        
        search_api.add_to_local_database(
            "测试题目内容",
            "A",
            "单选题",
            "A.选项1|B.选项2"
        )
        
        result = search_api.search_answer("测试题目内容", "单选题")
        
        assert result["success"] is True
        assert result["answer"] == "A"
        assert result["source"] == "local"

    def test_local_database_empty(self, local_db_config):
        """TC-SA-005: 本地数据库空测试"""
        search_api = SearchAPI(local_db_config)
        
        result = search_api.search_answer("不存在的题目", "单选题")
        
        assert result["success"] is False
        assert result["answer"] == ""

    def test_add_to_local_database(self, local_db_config):
        """TC-SA-006: 添加题目到本地数据库测试"""
        search_api = SearchAPI(local_db_config)
        
        search_api.add_to_local_database(
            "Python的创始人是谁？",
            "Guido van Rossum",
            "单选题",
            "A.Guido|B.Tim|C.Larry|D.Dennis"
        )
        
        result = search_api.search_answer("Python的创始人", "单选题")
        
        assert result["success"] is True
        assert result["answer"] == "Guido van Rossum"

    def test_get_local_statistics(self, local_db_config):
        """TC-SA-007: 获取统计信息测试"""
        search_api = SearchAPI(local_db_config)
        
        search_api.add_to_local_database("题目1", "A", "单选题")
        search_api.add_to_local_database("题目2", "AB", "多选题")
        search_api.add_to_local_database("题目3", "对", "判断题")
        
        stats = search_api.get_local_statistics()
        
        assert stats["total"] == 3
        assert stats.get("单选题", 0) >= 1
        assert stats.get("多选题", 0) >= 1
        assert stats.get("判断题", 0) >= 1

    def test_api_with_data_field(self, api_config):
        """API返回包含data字段测试"""
        with requests_mock.Mocker() as m:
            m.post(
                api_config["search_api"]["api_url"],
                json={"code": 0, "data": {"answer": "B"}}
            )
            
            search_api = SearchAPI(api_config)
            result = search_api.search_answer("测试题目")
            
            assert result["success"] is True
            assert result["answer"] == "B"

    def test_api_with_invalid_response(self, api_config):
        """API返回无效格式测试"""
        with requests_mock.Mocker() as m:
            m.post(
                api_config["search_api"]["api_url"],
                json={"random_key": "value"}
            )
            
            search_api = SearchAPI(api_config)
            result = search_api.search_answer("测试题目")
            
            assert result["success"] is False

    def test_api_disabled_falls_back_to_local(self, local_db_config):
        """API禁用时回退到本地数据库测试"""
        search_api = SearchAPI(local_db_config)
        
        search_api.add_to_local_database("测试题目", "C", "单选题")
        
        result = search_api.search_answer("测试题目")
        
        assert result["success"] is True
        assert result["source"] == "local"

    def test_local_database_duplicate_entry(self, local_db_config):
        """本地数据库重复条目测试"""
        search_api = SearchAPI(local_db_config)
        
        search_api.add_to_local_database("重复题目", "A", "单选题")
        search_api.add_to_local_database("重复题目", "B", "多选题")
        
        result = search_api.search_answer("重复题目")
        
        assert result["success"] is True
        assert result["answer"] == "B"

    def test_search_with_empty_question(self, api_config):
        """空题目搜索测试"""
        with requests_mock.Mocker() as m:
            m.post(
                api_config["search_api"]["api_url"],
                json={"success": True, "answer": ""}
            )
            
            search_api = SearchAPI(api_config)
            result = search_api.search_answer("")
            
            assert result["answer"] == ""

    def test_search_with_none_question(self, api_config):
        """None题目搜索测试"""
        search_api = SearchAPI(api_config)
        result = search_api.search_answer(None)
        
        assert result["success"] is False

    def test_local_database_special_characters(self, local_db_config):
        """本地数据库特殊字符测试"""
        search_api = SearchAPI(local_db_config)
        
        search_api.add_to_local_database(
            "题目包含特殊字符：!@#$%^&*()",
            "答案",
            "单选题"
        )
        
        result = search_api.search_answer("特殊字符")
        
        assert result["success"] is True

    def test_api_network_error(self, api_config):
        """API网络错误测试"""
        with requests_mock.Mocker() as m:
            m.post(
                api_config["search_api"]["api_url"],
                exc=Exception("Network error")
            )
            
            search_api = SearchAPI(api_config)
            result = search_api.search_answer("测试题目")
            
            assert result["success"] is False

    def test_config_disabled_both(self, config):
        """API和本地数据库都禁用测试"""
        search_api = SearchAPI(config)
        
        result = search_api.search_answer("测试题目")
        
        assert result["success"] is False