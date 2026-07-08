import os
import sys
import json
import argparse
import time

"""
================================================================================
                           合规风险提示
================================================================================

**本工具仅用于Web自动化技术学习与研究目的**

严禁用于以下违规场景：
- 考试作弊、违规答题
- 违反学校规章制度
- 违反超星学习通平台服务协议
- 任何其他违法违规行为

**使用本工具造成的一切后果由使用者自行承担**，开发者不承担任何法律责任。

================================================================================
"""


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"配置文件未找到: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"配置文件格式错误: {config_path}")
        sys.exit(1)


def save_config(config: dict, config_path: str):
    """保存配置文件"""
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"配置已保存到: {config_path}")
    except Exception as e:
        print(f"保存配置失败: {e}")


def configure_login(config: dict):
    """配置登录信息"""
    print("\n=== 配置登录信息 ===")
    username = input("请输入超星学习通用户名（手机号或学号）: ").strip()
    password = input("请输入超星学习通密码: ").strip()
    
    if username and password:
        config["login"]["username"] = username
        config["login"]["password"] = password
        save_config(config, get_config_path())
        print("登录信息配置成功")
    else:
        print("用户名或密码不能为空")


def configure_browser(config: dict):
    """配置浏览器"""
    print("\n=== 配置浏览器 ===")
    print("请选择浏览器类型:")
    print("1. Chrome (推荐)")
    print("2. Edge")
    
    choice = input("请输入选择 (1/2): ").strip()
    if choice == "1":
        config["browser"]["type"] = "chrome"
    elif choice == "2":
        config["browser"]["type"] = "edge"
    else:
        print("无效选择，使用默认值 Chrome")
        config["browser"]["type"] = "chrome"
    
    headless = input("是否使用无头模式（不显示浏览器窗口）? (y/n): ").strip().lower()
    config["browser"]["headless"] = headless == "y"
    
    save_config(config, get_config_path())
    print("浏览器配置成功")


def configure_delay(config: dict):
    """配置延迟参数"""
    print("\n=== 配置延迟参数 ===")
    
    try:
        min_delay = float(input(f"输入最小答题间隔（秒，默认 {config['delay']['min_delay']}）: ").strip() or config["delay"]["min_delay"])
        max_delay = float(input(f"输入最大答题间隔（秒，默认 {config['delay']['max_delay']}）: ").strip() or config["delay"]["max_delay"])
        total_time_min = int(input(f"输入总答题时长下限（分钟，默认 {config['delay']['total_time_min']}）: ").strip() or config["delay"]["total_time_min"])
        
        config["delay"]["min_delay"] = min_delay
        config["delay"]["max_delay"] = max_delay
        config["delay"]["total_time_min"] = total_time_min
        
        save_config(config, get_config_path())
        print("延迟参数配置成功")
        
    except ValueError:
        print("输入格式错误，请输入数字")


def configure_search_api(config: dict):
    """配置搜题API"""
    print("\n=== 配置搜题API ===")
    
    enabled = input("是否启用搜题API? (y/n): ").strip().lower()
    config["search_api"]["enabled"] = enabled == "y"
    
    if config["search_api"]["enabled"]:
        api_url = input("请输入搜题API地址: ").strip()
        api_key = input("请输入API密钥（如果需要）: ").strip()
        
        config["search_api"]["api_url"] = api_url
        config["search_api"]["api_key"] = api_key
    
    # 配置本地数据库
    local_enabled = input("是否启用本地题库? (y/n): ").strip().lower()
    config["local_database"]["enabled"] = local_enabled == "y"
    
    save_config(config, get_config_path())
    print("搜题API配置成功")


def get_config_path() -> str:
    """获取配置文件路径（支持相对路径，兼容U盘运行）"""
    if getattr(sys, 'frozen', False):
        # 打包后运行，使用exe所在目录
        return os.path.join(os.path.dirname(sys.executable), "config.json")
    else:
        # 开发模式运行，使用当前目录
        return os.path.join(os.path.dirname(__file__), "config.json")


def print_config(config: dict):
    """打印当前配置"""
    print("\n=== 当前配置 ===")
    print(json.dumps(config, indent=2, ensure_ascii=False))


def run_auto_answer(config: dict):
    """运行自动答题"""
    from browser_automation import BrowserAutomation
    
    print("\n" + "=" * 50)
    print("  超星学习通自动答题工具")
    print("=" * 50)
    print("提示: 本工具仅用于技术学习研究")
    print("=" * 50 + "\n")
    
    # 检查必要配置
    if not config["login"]["username"] or not config["login"]["password"]:
        print("错误: 请先配置登录信息")
        configure_login(config)
        return
    
    # 创建浏览器自动化实例
    automation = BrowserAutomation(config)
    
    try:
        # 初始化浏览器
        if not automation.init_browser():
            print("浏览器初始化失败")
            return
        
        # 登录
        if not automation.login():
            print("登录失败")
            automation.close_browser()
            return
        
        # 导航到考试页面
        exam_url = input("请输入考试/作业页面URL（或按回车手动打开）: ").strip()
        if not automation.navigate_to_exam(exam_url):
            print("导航失败")
            automation.close_browser()
            return
        
        # 开始自动答题
        automation.start_auto_answer()
        
        # 等待用户确认后关闭浏览器
        print("\n答题完成！按回车关闭浏览器...")
        input()
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        automation.close_browser()


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description="超星学习通自动答题工具 - 仅用于技术学习研究",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py run              # 运行自动答题
  python main.py config login     # 配置登录信息
  python main.py config browser   # 配置浏览器
  python main.py config delay     # 配置延迟参数
  python main.py config api       # 配置搜题API
  python main.py config show      # 显示当前配置
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # run 命令
    subparsers.add_parser("run", help="运行自动答题")
    
    # config 命令
    config_parser = subparsers.add_parser("config", help="配置工具")
    config_subparsers = config_parser.add_subparsers(dest="config_command", help="配置项")
    config_subparsers.add_parser("login", help="配置登录信息")
    config_subparsers.add_parser("browser", help="配置浏览器")
    config_subparsers.add_parser("delay", help="配置延迟参数")
    config_subparsers.add_parser("api", help="配置搜题API")
    config_subparsers.add_parser("show", help="显示当前配置")
    
    args = parser.parse_args()
    
    # 加载配置
    config_path = get_config_path()
    config = load_config(config_path)
    
    # 执行命令
    if args.command == "run":
        run_auto_answer(config)
    elif args.command == "config":
        if args.config_command == "login":
            configure_login(config)
        elif args.config_command == "browser":
            configure_browser(config)
        elif args.config_command == "delay":
            configure_delay(config)
        elif args.config_command == "api":
            configure_search_api(config)
        elif args.config_command == "show":
            print_config(config)
        else:
            config_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()