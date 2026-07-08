import json

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    
print("=== 用户 15367563648 的预约配置 ===")
for i, r in enumerate(config.get('reserve', [])):
    if r.get('username') == '15367563648':
        print(f"配置 {i}:")
        print(f"  时间: {r.get('time')}")
        print(f"  房间ID: {r.get('roomid')}")
        print(f"  座位号: {r.get('seatid')}")
        print(f"  预约日期: {r.get('daysofweek')}")

print("\n=== 预约历史记录 ===")
try:
    with open('reservations.json', 'r', encoding='utf-8') as f:
        history = json.load(f)
    if '15367563648' in history:
        for date, times in history['15367563648'].items():
            print(f"日期 {date}:")
            for time_seg, reserve_id in times.items():
                print(f"  {time_seg} -> 预约ID: {reserve_id}")
    else:
        print("暂无预约历史")
except FileNotFoundError:
    print("预约历史文件不存在")