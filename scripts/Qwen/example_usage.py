#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通义千问 自动化工具使用示例

使用前请确保：
1. 在config.json中设置正确的配置项
2. 安装必要依赖：pip install beautifulsoup4 selenium webdriver-manager
"""

from qwen_automation import QwenAutomation
import json
from datetime import datetime


def example_single_question():
    """示例1：处理单个问题"""
    print("=" * 50)
    print("示例1：处理单个问题")
    print("=" * 50)
    
    # 创建自动化实例 - 指定配置文件路径
    import os
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    automation = QwenAutomation(config_path)
    
    try:
        # 初始化浏览器和登录
        if not automation.initialize():
            print("初始化失败")
            return
        
        # 提问 - 使用与 load_test_data 和 generate_prompt 一致的格式
        formula = "1+1=?"
        question = automation.generate_prompt(formula)
        result = automation.ask_question(question)
        
        if result:
            print(f"时间戳: {result['timestamp']}")
            print(f"问题: {result['question']}")
            print(f"思考过程: {result['thinking_process']}")
            print(f"正式回答: {result['formal_answer']}")
            
            # 保存结果到文件
            with open(f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            return result
        else:
            print("获取回复失败")
            return None
            
    finally:
        automation.close()


def example_multiple_questions():
    """示例2：批量处理多个问题"""
    print("=" * 50)
    print("示例2：批量处理多个问题")
    print("=" * 50)
    
    # 创建自动化实例 - 指定配置文件路径
    import os
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    automation = QwenAutomation(config_path)
    
    try:
        # 初始化浏览器和登录
        if not automation.initialize():
            print("初始化失败")
            return
        
        # 准备问题列表 - 使用与 load_test_data 一致的公式格式
        formulas = [
            "1+1=?",
            "9.11和9.9哪个大"
        ]
        
        # 生成标准格式的问题
        questions = [automation.generate_prompt(formula) for formula in formulas]
        
        # 批量处理
        results = automation.ask_multiple_questions(questions)
        
        print(f"成功处理了 {len(results)}/{len(questions)} 个问题")
        
        # 保存所有结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        with open(f"batch_results_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 打印摘要
        for i, result in enumerate(results, 1):
            print(f"\n问题 {i}: {result['question'][:50]}...")
            print(f"思考过程长度: {len(result.get('thinking_process', ''))} 字符")
            print(f"正式回答长度: {len(result.get('formal_answer', ''))} 字符")
        
        return results
        
    finally:
        automation.close()


def example_test_data_automation():
    """示例3：使用测试数据文件进行自动化测试"""
    print("=" * 50)
    print("示例3：使用测试数据文件进行自动化测试")
    print("=" * 50)
    
    # 创建自动化实例 - 指定配置文件路径
    import os
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    automation = QwenAutomation(config_path)
    
    try:
        # 初始化浏览器和登录
        if not automation.initialize():
            print("初始化失败")
            return
        
        # 运行自动化测试（使用与 load_test_data 一致的数据文件）
        automation.run_automation('data/tricks/fusion_results_all.json')
        
        print("自动化测试完成")
        
    finally:
        automation.close()


def main():
    """主函数：选择运行哪个示例"""
    print("通义千问 自动化工具使用示例")
    print("请选择运行的示例：")
    print("1. 单个问题处理")
    print("2. 批量问题处理")
    print("3. 测试数据自动化")
    
    choice = input("请输入选择 (1-3): ").strip()
    
    if choice == "1":
        example_single_question()
    elif choice == "2":
        example_multiple_questions()
    elif choice == "3":
        example_test_data_automation()
    else:
        print("无效选择")


if __name__ == "__main__":
    main() 