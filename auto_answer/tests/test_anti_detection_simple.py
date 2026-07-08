import unittest
import time
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from anti_detection import AntiDetection


class TestAntiDetection(unittest.TestCase):
    def setUp(self):
        self.config = {
            "delay": {"min_delay": 1, "max_delay": 3, "total_time_min": 1},
            "anti_detection": {"mouse_move": True, "random_scroll": True, "fake_modify_rate": 0.2}
        }
        self.mock_driver = Mock()
        self.mock_driver.execute_script = Mock(return_value="complete")

    def test_random_delay_normal(self):
        ad = AntiDetection(self.mock_driver, self.config)
        
        delays = []
        for _ in range(10):
            start = time.time()
            delay = ad.random_delay()
            elapsed = time.time() - start
            delays.append(delay)
            
            self.assertGreaterEqual(elapsed, self.config["delay"]["min_delay"] - 0.1)
            self.assertLessEqual(elapsed, self.config["delay"]["max_delay"] + 0.1)
        
        self.assertGreater(len(set(delays)), 1)

    def test_random_delay_boundary(self):
        self.config["delay"]["min_delay"] = 0.1
        self.config["delay"]["max_delay"] = 0.2
        ad = AntiDetection(self.mock_driver, self.config)
        
        start = time.time()
        ad.random_delay()
        elapsed = time.time() - start
        
        self.assertGreaterEqual(elapsed, 0.08)
        self.assertLessEqual(elapsed, 0.22)

    def test_bezier_curve_generation(self):
        ad = AntiDetection(self.mock_driver, self.config)
        
        points = ad._generate_bezier_curve(0, 0, 100, 100, num_points=10)
        
        self.assertEqual(len(points), 11)
        self.assertEqual(points[0], (0.0, 0.0))
        self.assertEqual(points[-1], (100.0, 100.0))

    def test_fake_modify_probability(self):
        self.config["anti_detection"]["fake_modify_rate"] = 0.5
        ad = AntiDetection(self.mock_driver, self.config)
        
        results = [ad.should_fake_modify() for _ in range(100)]
        true_count = sum(results)
        
        self.assertGreaterEqual(true_count, 30)
        self.assertLessEqual(true_count, 70)

    def test_random_scroll_disabled(self):
        self.config["anti_detection"]["random_scroll"] = False
        ad = AntiDetection(self.mock_driver, self.config)
        
        ad.random_scroll()
        
        self.mock_driver.execute_script.assert_not_called()

    def test_human_mouse_move_disabled(self):
        self.config["anti_detection"]["mouse_move"] = False
        ad = AntiDetection(self.mock_driver, self.config)
        
        mock_element = Mock()
        mock_element.rect = {"x": 100, "y": 100, "width": 100, "height": 50}
        
        ad.human_mouse_move(mock_element)

    def test_smooth_scroll(self):
        ad = AntiDetection(self.mock_driver, self.config)
        
        try:
            ad._smooth_scroll(500)
        except Exception as e:
            self.fail(f"平滑滚动失败: {e}")