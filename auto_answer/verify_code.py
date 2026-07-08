import sys
import os
import ast
import json

print("=" * 60)
print("  超星学习通自动答题工具 - 代码验证")
print("=" * 60)
print()

files_to_verify = [
    "anti_detection.py",
    "question_parser.py",
    "search_api.py",
    "browser_automation.py",
    "main.py",
    "config.json",
    "run_tests.py",
    "tests/test_anti_detection_simple.py",
    "tests/test_question_parser_simple.py",
    "tests/test_search_api_simple.py",
]

success_count = 0
fail_count = 0
results = []

for file_path in files_to_verify:
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    
    if not os.path.exists(full_path):
        results.append(f"❌ {file_path}: 文件不存在")
        fail_count += 1
        continue
    
    try:
        if file_path.endswith(".py"):
            with open(full_path, "r", encoding="utf-8") as f:
                source = f.read()
            
            ast.parse(source)
            results.append(f"✅ {file_path}: 语法正确")
            success_count += 1
            
            lines = source.split("\n")
            classes = [node.name for node in ast.walk(ast.parse(source)) if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in ast.walk(ast.parse(source)) if isinstance(node, ast.FunctionDef)]
            
            if classes or functions:
                details = []
                if classes:
                    details.append(f"类: {', '.join(classes)}")
                if functions:
                    details.append(f"函数: {', '.join(functions[:5])}{'...' if len(functions) > 5 else ''}")
                results.append(f"   → {'; '.join(details)}")
        
        elif file_path.endswith(".json"):
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            results.append(f"✅ {file_path}: JSON格式正确")
            success_count += 1
            
            if isinstance(data, dict):
                keys = list(data.keys())[:5]
                results.append(f"   → 配置项: {', '.join(keys)}{'...' if len(data.keys()) > 5 else ''}")
    
    except SyntaxError as e:
        results.append(f"❌ {file_path}: 语法错误 - {e.msg}")
        fail_count += 1
    except json.JSONDecodeError as e:
        results.append(f"❌ {file_path}: JSON格式错误 - {e.msg}")
        fail_count += 1
    except Exception as e:
        results.append(f"❌ {file_path}: 验证失败 - {str(e)[:50]}")
        fail_count += 1

print("\n验证结果:")
print("-" * 60)
for result in results:
    print(result)

print()
print("=" * 60)
print(f"  总文件数: {len(files_to_verify)}")
print(f"  通过: {success_count}")
print(f"  失败: {fail_count}")
print(f"  通过率: {(success_count / len(files_to_verify) * 100):.2f}%")
print("=" * 60)

# 验证目录结构
print("\n目录结构验证:")
print("-" * 60)
project_dir = os.path.dirname(__file__)
test_data_dir = os.path.join(project_dir, "tests", "test_data")

if os.path.exists(test_data_dir):
    test_files = os.listdir(test_data_dir)
    print(f"✅ 测试数据目录存在: {len(test_files)} 个文件")
    for f in test_files:
        print(f"   → {f}")
else:
    print("❌ 测试数据目录不存在")

# 生成验证报告
report = {
    "timestamp": __import__('time').strftime("%Y-%m-%d %H:%M:%S"),
    "total_files": len(files_to_verify),
    "passed": success_count,
    "failed": fail_count,
    "pass_rate": (success_count / len(files_to_verify) * 100) if files_to_verify else 0,
    "results": results
}

report_path = os.path.join(project_dir, "verification_report.json")
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\n验证报告已保存到: {report_path}")