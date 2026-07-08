import sys
import os
import unittest
import json
import time

sys.path.insert(0, os.path.dirname(__file__))

from tests.test_anti_detection_simple import TestAntiDetection
from tests.test_question_parser_simple import TestQuestionParser
from tests.test_search_api_simple import TestSearchAPI


def run_tests():
    """运行所有测试用例"""
    print("=" * 60)
    print("  超星学习通自动答题工具 - 测试运行器")
    print("=" * 60)
    print()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestAntiDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestQuestionParser))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchAPI))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    print(f"  总测试数: {result.testsRun}")
    print(f"  通过数: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败数: {len(result.failures)}")
    print(f"  错误数: {len(result.errors)}")
    
    if result.failures:
        print("\n  失败详情:")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"    {i}. {test}: {traceback[:200]}")
    
    if result.errors:
        print("\n  错误详情:")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"    {i}. {test}: {traceback[:200]}")

    print("=" * 60)
    
    generate_report(result)


def generate_report(result):
    """生成测试报告"""
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tests": result.testsRun,
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failed": len(result.failures),
        "errors": len(result.errors),
        "pass_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100 if result.testsRun > 0 else 0
    }

    report_path = os.path.join(os.path.dirname(__file__), "test_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n  JSON报告已保存到: {report_path}")

    html_report = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>超星学习通自动答题工具 - 测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 15px; }}
        .summary {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; margin: 30px 0; }}
        .stat {{ text-align: center; padding: 20px; border-radius: 8px; background-color: #ecf0f1; }}
        .stat strong {{ display: block; font-size: 28px; margin-bottom: 5px; }}
        .total strong {{ color: #2c3e50; }}
        .passed strong {{ color: #27ae60; }}
        .failed strong {{ color: #e74c3c; }}
        .errors strong {{ color: #f39c12; }}
        .rate strong {{ color: #3498db; }}
        .timestamp {{ color: #7f8c8d; font-style: italic; }}
        .section {{ margin-top: 40px; }}
        .section h2 {{ color: #34495e; }}
        .detail-list {{ list-style: none; padding: 0; }}
        .detail-list li {{ padding: 10px; border-bottom: 1px solid #eee; color: #555; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>超星学习通自动答题工具 - 测试报告</h1>
        <p class="timestamp">生成时间: {report['timestamp']}</p>
        
        <div class="summary">
            <div class="stat total">总测试数<br><strong>{report['total_tests']}</strong></div>
            <div class="stat passed">通过数<br><strong>{report['passed']}</strong></div>
            <div class="stat failed">失败数<br><strong>{report['failed']}</strong></div>
            <div class="stat errors">错误数<br><strong>{report['errors']}</strong></div>
            <div class="stat rate">通过率<br><strong>{report['pass_rate']:.2f}%</strong></div>
        </div>
        
        <div class="section">
            <h2>测试覆盖模块</h2>
            <ul class="detail-list">
                <li>✅ 防检测模块 (AntiDetection)</li>
                <li>✅ 题目解析模块 (QuestionParser)</li>
                <li>✅ 搜题API模块 (SearchAPI)</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>测试类型覆盖</h2>
            <ul class="detail-list">
                <li>✅ 正常测试 - 验证基本功能正确性</li>
                <li>✅ 边界值测试 - 验证参数边界情况</li>
                <li>✅ 异常测试 - 验证异常情况处理</li>
                <li>✅ 空值/None测试 - 验证空值处理</li>
                <li>✅ 参数组合测试 - 验证参数组合覆盖</li>
            </ul>
        </div>
    </div>
</body>
</html>"""

    html_path = os.path.join(os.path.dirname(__file__), "test_report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_report)
    
    print(f"  HTML报告已保存到: {html_path}")


if __name__ == "__main__":
    run_tests()