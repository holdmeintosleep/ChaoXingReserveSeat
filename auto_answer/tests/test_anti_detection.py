import pytest
import time
import random
from unittest.mock import Mock, patch
from anti_detection import AntiDetection


class TestAntiDetection:
    """防检测模块测试用例"""

    def test_random_delay_normal(self, config, mock_driver):
        """TC-AD-001: 随机延迟测试"""
        ad = AntiDetection(mock_driver, config)
        
        delays = []
        for _ in range(10):
            start = time.time()
            delay = ad.random_delay()
            elapsed = time.time() - start
            delays.append(delay)
            
            assert config["delay"]["min_delay"] <= elapsed <= config["delay"]["max_delay"] + 0.1
        
        assert len(set(delays)) > 1

    def test_random_delay_boundary_min(self, config, mock_driver):
        """TC-AD-002: 最小延迟边界测试"""
        config["delay"]["min_delay"] = 0.1
        config["delay"]["max_delay"] = 0.2
        ad = AntiDetection(mock_driver, config)
        
        start = time.time()
        ad.random_delay()
        elapsed = time.time() - start
        
        assert 0.08 <= elapsed <= 0.22

    def test_random_delay_boundary_max(self, config, mock_driver):
        """TC-AD-003: 最大延迟边界测试"""
        config["delay"]["min_delay"] = 5
        config["delay"]["max_delay"] = 10
        ad = AntiDetection(mock_driver, config)
        
        start = time.time()
        ad.random_delay()
        elapsed = time.time() - start
        
        assert 4.8 <= elapsed <= 10.2

    def test_bezier_curve_generation(self, config, mock_driver):
        """TC-AD-004: 贝塞尔曲线轨迹生成测试"""
        ad = AntiDetection(mock_driver, config)
        
        points = ad._generate_bezier_curve(0, 0, 100, 100, num_points=10)
        
        assert len(points) == 11
        assert points[0] == (0.0, 0.0)
        assert points[-1] == (100.0, 100.0)
        
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        assert sorted(x_coords) == x_coords
        assert sorted(y_coords) == y_coords

    def test_random_scroll(self, config, mock_driver):
        """TC-AD-005: 随机滚动测试"""
        config["anti_detection"]["random_scroll"] = True
        ad = AntiDetection(mock_driver, config)
        
        mock_driver.execute_script.side_effect = [100, 1000, 500]
        
        try:
            ad.random_scroll()
        except Exception as e:
            pytest.fail(f"随机滚动失败: {e}")

    def test_random_scroll_disabled(self, config, mock_driver):
        """随机滚动禁用测试"""
        config["anti_detection"]["random_scroll"] = False
        ad = AntiDetection(mock_driver, config)
        
        ad.random_scroll()
        
        mock_driver.execute_script.assert_not_called()

    def test_fake_modify_probability(self, config, mock_driver):
        """TC-AD-006: 修改答案概率测试"""
        config["anti_detection"]["fake_modify_rate"] = 0.5
        ad = AntiDetection(mock_driver, config)
        
        results = [ad.should_fake_modify() for _ in range(100)]
        true_count = sum(results)
        
        assert 30 <= true_count <= 70

    def test_fake_modify_rate_zero(self, config, mock_driver):
        """修改答案概率为0测试"""
        config["anti_detection"]["fake_modify_rate"] = 0.0
        ad = AntiDetection(mock_driver, config)
        
        results = [ad.should_fake_modify() for _ in range(100)]
        
        assert all(r is False for r in results)

    def test_fake_modify_rate_one(self, config, mock_driver):
        """修改答案概率为1测试"""
        config["anti_detection"]["fake_modify_rate"] = 1.0
        ad = AntiDetection(mock_driver, config)
        
        results = [ad.should_fake_modify() for _ in range(100)]
        
        assert all(r is True for r in results)

    def test_human_mouse_move_enabled(self, config, mock_driver, mock_element):
        """鼠标移动启用测试"""
        config["anti_detection"]["mouse_move"] = True
        ad = AntiDetection(mock_driver, config)
        
        with patch('anti_detection.ActionChains') as mock_actions_class:
            mock_actions = Mock()
            mock_actions_class.return_value = mock_actions
            
            try:
                ad.human_mouse_move(mock_element)
            except Exception as e:
                pytest.fail(f"鼠标移动失败: {e}")

    def test_human_mouse_move_disabled(self, config, mock_driver, mock_element):
        """鼠标移动禁用测试"""
        config["anti_detection"]["mouse_move"] = False
        ad = AntiDetection(mock_driver, config)
        
        ad.human_mouse_move(mock_element)
        
        assert True

    def test_human_click(self, config, mock_driver, mock_element):
        """人类点击测试"""
        ad = AntiDetection(mock_driver, config)
        
        with patch('anti_detection.ActionChains'):
            try:
                ad.human_click(mock_element)
            except Exception as e:
                pytest.fail(f"人类点击失败: {e}")

    def test_human_type(self, config, mock_driver, mock_element):
        """人类输入测试"""
        ad = AntiDetection(mock_driver, config)
        
        with patch('anti_detection.ActionChains'):
            try:
                ad.human_type(mock_element, "test")
            except Exception as e:
                pytest.fail(f"人类输入失败: {e}")

    def test_smooth_scroll(self, config, mock_driver):
        """平滑滚动测试"""
        ad = AntiDetection(mock_driver, config)
        
        try:
            ad._smooth_scroll(500)
        except Exception as e:
            pytest.fail(f"平滑滚动失败: {e}")

    def test_random_delay_custom_range(self, config, mock_driver):
        """自定义延迟范围测试"""
        ad = AntiDetection(mock_driver, config)
        
        start = time.time()
        delay = ad.random_delay(min_delay=0.5, max_delay=1.0)
        elapsed = time.time() - start
        
        assert 0.48 <= elapsed <= 1.02

    def test_bezier_curve_negative_coordinates(self, config, mock_driver):
        """负坐标贝塞尔曲线测试"""
        ad = AntiDetection(mock_driver, config)
        
        points = ad._generate_bezier_curve(-100, -100, 50, 50)
        
        assert len(points) == 16
        assert points[0] == (-100.0, -100.0)
        assert points[-1] == (50.0, 50.0)