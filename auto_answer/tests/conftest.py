import pytest
import os
import json
from unittest.mock import Mock, MagicMock
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


@pytest.fixture
def base_dir():
    return os.path.dirname(os.path.dirname(__file__))


@pytest.fixture
def test_data_dir(base_dir):
    return os.path.join(base_dir, "tests", "test_data")


@pytest.fixture
def config():
    return {
        "login": {
            "username": "test_user",
            "password": "test_pass",
            "login_url": "https://passport2.chaoxing.com/mlogin"
        },
        "browser": {
            "type": "chrome",
            "headless": True,
            "window_size": "1920,1080"
        },
        "delay": {
            "min_delay": 1,
            "max_delay": 3,
            "total_time_min": 1
        },
        "anti_detection": {
            "mouse_move": True,
            "random_scroll": True,
            "fake_modify_rate": 0.2
        },
        "search_api": {
            "enabled": False,
            "api_url": "",
            "api_key": "",
            "timeout": 10
        },
        "local_database": {
            "enabled": False,
            "file_path": ":memory:"
        },
        "auto_submit": True
    }


@pytest.fixture
def mock_driver():
    driver = Mock(spec=WebDriver)
    driver.execute_script = Mock(return_value="complete")
    driver.get = Mock()
    driver.quit = Mock()
    driver.set_window_size = Mock()
    driver.current_url = "https://www.example.com"
    return driver


@pytest.fixture
def mock_element():
    element = Mock(spec=WebElement)
    element.rect = {"x": 100, "y": 100, "width": 100, "height": 50}
    element.click = Mock()
    element.send_keys = Mock()
    return element


@pytest.fixture
def mock_actions():
    actions = Mock()
    actions.move_to_element_with_offset = Mock(return_value=actions)
    actions.move_by_offset = Mock(return_value=actions)
    actions.perform = Mock()
    return actions


@pytest.fixture
def api_config():
    return {
        "search_api": {
            "enabled": True,
            "api_url": "https://api.example.com/search",
            "api_key": "test_key",
            "timeout": 10
        },
        "local_database": {
            "enabled": False,
            "file_path": ":memory:"
        }
    }


@pytest.fixture
def local_db_config():
    return {
        "search_api": {
            "enabled": False,
            "api_url": "",
            "api_key": "",
            "timeout": 10
        },
        "local_database": {
            "enabled": True,
            "file_path": ":memory:"
        }
    }