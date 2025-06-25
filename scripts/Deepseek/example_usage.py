#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek 自动化工具使用示例

使用前请确保：
1. 在config.json中设置正确的邮箱和密码
2. 安装必要依赖：pip install beautifulsoup4 selenium webdriver-manager pyautogui
"""

from deepseek_automation import DeepSeekAutomation
import json
from datetime import datetime


def example_single_question():
    """示例1：处理单个问题"""
    print("=" * 50)
    print("示例1：处理单个问题")
    print("=" * 50)
    
    # 创建自动化实例
    automation = DeepSeekAutomation()
    
    try:
        # 初始化浏览器和登录
        if not automation.initialize():
            print("初始化失败")
            return
        
        # 提问
        question = "一句話回答我純數學上1+1=?"
        result = automation.ask_question(question)
        
        if result:
            print(f"时间戳: {result['timestamp']}")
            print(f"问题: {result['question']}")
            print(f"深度思考过程: {result['deep_thinking']}")
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
    
    # 创建自动化实例
    automation = DeepSeekAutomation()
    
    try:
        # 初始化浏览器和登录
        if not automation.initialize():
            print("初始化失败")
            return
        
        # 准备问题列表
        questions = [
            "1+1=?",
            "9.11和9.9哪个大"
        ]
        
        # 批量处理
        results = automation.ask_multiple_questions(questions)
        
        print(f"成功处理了 {len(results)}/{len(questions)} 个问题")
        
        # 保存所有结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        with open(f"batch_results_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 打印摘要
        for i, result in enumerate(results, 1):
            print(f"\n问题 {i}: {result['question']}")
            print(f"深度思考过程长度: {len(result['deep_thinking'])} 字符")
            print(f"正式回答长度: {len(result['formal_answer'])} 字符")
        
        return results
        
    finally:
        automation.close()

def main():
    """主函数：选择运行哪个示例"""
    print("DeepSeek 自动化工具使用示例")
    print("请选择运行的示例：")
    print("1. 单个问题处理")
    print("2. 批量问题处理")
    
    choice = input("请输入选择 (1-2): ").strip()
    
    if choice == "1":
        example_single_question()
    elif choice == "2":
        example_multiple_questions()
    else:
        print("无效选择")


if __name__ == "__main__":
    main() 