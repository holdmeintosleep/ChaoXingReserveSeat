import urllib.request
import json
import time

# 测试预约执行和轮询
print("=== 测试预约执行 ===")
req = urllib.request.Request(
    'http://localhost:5000/api/reservation/execute',
    data=json.dumps({"config_index": 2}).encode('utf-8'),  # 用户15367563648的配置索引
    headers={'Content-Type': 'application/json'},
    method='POST'
)
resp = urllib.request.urlopen(req)
data = json.loads(resp.read().decode())
print(f"启动响应: {data}")

task_id = data.get("task_id")
if task_id:
    print(f"\n=== 轮询任务状态 ===")
    for i in range(10):
        try:
            status_resp = urllib.request.urlopen(f'http://localhost:5000/api/reservation/status/{task_id}')
            status = json.loads(status_resp.read().decode())
            print(f"轮询 {i+1}: {json.dumps(status, ensure_ascii=False)}")
            
            if status.get("data", {}).get("status") == "done":
                results = status.get("data", {}).get("results", [])
                print(f"\n=== 最终结果 ===")
                for r in results:
                    print(f"用户: {r.get('username')}, 成功: {r.get('success')}, 消息: {r.get('message')}")
                break
        except Exception as e:
            print(f"轮询失败: {e}