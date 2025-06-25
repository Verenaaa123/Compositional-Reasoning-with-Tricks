#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版本的 DeepSeek 自动化运行脚本
"""

import os
import sys
import time
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def fix_chromedriver_path():
    """修复 ChromeDriver 路径问题"""
    try:
        # 使用 ChromeDriverManager 获取路径
        driver_path = ChromeDriverManager().install()
        
        # 检查路径是否正确
        if driver_path.endswith('THIRD_PARTY_NOTICES.chromedriver'):
            # 修正路径，指向实际的 chromedriver 文件
            correct_path = driver_path.replace('THIRD_PARTY_NOTICES.chromedriver', 'chromedriver')
            if os.path.exists(correct_path):
                print(f"修正 ChromeDriver 路径: {correct_path}")
                return correct_path
        
        return driver_path
    except Exception as e:
        print(f"获取 ChromeDriver 路径失败: {e}")
        return None

def test_chromedriver():
    """测试 ChromeDriver 是否工作"""
    try:
        driver_path = fix_chromedriver_path()
        if not driver_path:
            return False
            
        options = Options()
        options.add_argument('--headless')  # 无头模式测试
        service = Service(driver_path)
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.get('https://www.google.com')
        print("ChromeDriver 测试成功！")
        driver.quit()
        return True
        
    except Exception as e:
        print(f"ChromeDriver 测试失败: {e}")
        return False

def run_deepseek_automation():
    """运行 DeepSeek 自动化"""
    # 先测试 ChromeDriver
    if not test_chromedriver():
        print("ChromeDriver 无法正常工作，请检查安装")
        return
    
    # 修改 DeepSeekAutomation 类中的 ChromeDriver 路径
    import deepseek_automation
    
    # 保存原始的 _setup_driver 方法
    original_setup_driver = deepseek_automation.DeepSeekAutomation._setup_driver
    
    def fixed_setup_driver(self):
        """修复版本的 setup_driver 方法"""
        options = Options()
        
        # 基本设置
        if self.config['browser']['headless']:
            options.add_argument('--headless')
        
        # 窗口大小
        window_size = self.config['browser']['window_size']
        options.add_argument(f'--window-size={window_size}')
        
        # 用户数据目录
        user_data_dir = self.config['browser']['user_data_dir']
        if user_data_dir:
            options.add_argument(f'--user-data-dir={os.path.abspath(user_data_dir)}')
        
        # 其他有用的选项
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 使用修复后的 ChromeDriver 路径
        driver_path = fix_chromedriver_path()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        # 执行反检测脚本
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    # 替换方法
    deepseek_automation.DeepSeekAutomation._setup_driver = fixed_setup_driver
    
    # 现在运行自动化
    from deepseek_automation import DeepSeekAutomation
    import json
    from datetime import datetime
    
    print("=" * 50)
    print("DeepSeek 自动化工具")
    print("=" * 50)
    
    automation = DeepSeekAutomation()
    
    try:
        # 初始化浏览器和登录
        if not automation.initialize():
            print("初始化失败")
            return
        
        # 提问
        question = "一句話回答我純數學上1+1=?"
        print(f"提问: {question}")
        
        result = automation.ask_question(question)
        
        if result:
            print(f"\n时间戳: {result['timestamp']}")
            print(f"问题: {result['question']}")
            print(f"思考时间: {result.get('thinking_time', 'N/A')}")
            print(f"深度思考过程: {result['deep_thinking'][:200]}...")
            print(f"正式回答: {result['formal_answer']}")
            
            # 保存结果到文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"result_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存到: {filename}")
            
        else:
            print("获取回复失败")
            
    except KeyboardInterrupt:
        print("\n用户中断执行")
    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 安全的用户输入处理
        while True:
            try:
                choice = input("\n是否关闭浏览器？(y/n): ").strip().lower()
                if choice in ['y', 'yes', 'n', 'no']:
                    break
                else:
                    print("请输入 'y' 或 'n'")
            except (EOFError, KeyboardInterrupt):
                print("\n程序被中断")
                choice = 'y'  # 默认关闭浏览器
                break
            except Exception as e:
                print(f"输入错误: {e}")
                choice = 'y'  # 默认关闭浏览器
                break

if __name__ == "__main__":
    run_deepseek_automation() 