#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import sys
import time
import random
import logging
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_test_data(file_path: str) -> Dict:
    """加载测试数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"成功加载测试数据: {len(data.get('results', {}))} 条记录")
        return data
    except Exception as e:
        logger.error(f"加载测试数据失败: {e}")
        return {}

def test_qwen_api():
    """测试通义千问API"""
    try:
        from openai import OpenAI
        
        # 从环境变量获取API密钥
        api_key = os.getenv('QWEN_API_KEY')
        if not api_key:
            logger.error("环境变量 QWEN_API_KEY 未设置")
            return False
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': '你好'}
            ],
        )
        
        logger.info("通义千问API测试成功")
        logger.info(f"回复: {completion.choices[0].message.content}")
        return True
        
    except Exception as e:
        logger.error(f"通义千问API测试失败: {e}")
        return False

def test_deepseek_api():
    """测试DeepSeek API"""
    try:
        from openai import OpenAI
        
        # 从环境变量获取API密钥
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            logger.error("环境变量 DEEPSEEK_API_KEY 未设置")
            return False
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        
        completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"}
            ],
            stream=False
        )
        
        logger.info("DeepSeek API测试成功")
        logger.info(f"回复: {completion.choices[0].message.content}")
        return True
        
    except Exception as e:
        logger.error(f"DeepSeek API测试失败: {e}")
        return False

def run_batch_test(formulas: List[str], model_type: str = "qwen"):
    """批量测试公式"""
    results = []
    
    for i, formula in enumerate(formulas):
        logger.info(f"测试公式 {i+1}/{len(formulas)}: {formula}")
        
        try:
            if model_type == "qwen":
                success = test_formula_with_qwen(formula)
            else:
                success = test_formula_with_deepseek(formula)
            
            results.append({
                "formula": formula,
                "success": success,
                "timestamp": datetime.now().isoformat()
            })
            
            # 添加延迟避免API限流
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            logger.error(f"测试公式失败: {e}")
            results.append({
                "formula": formula,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'data/model_test_results_{timestamp}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"批量测试完成，结果保存到: {filename}")
    return results

def test_formula_with_qwen(formula: str) -> bool:
    """使用通义千问测试单个公式"""
    # 实现具体的测试逻辑
    return test_qwen_api()

def test_formula_with_deepseek(formula: str) -> bool:
    """使用DeepSeek测试单个公式"""
    # 实现具体的测试逻辑
    return test_deepseek_api()

def main():
    """主函数"""
    logger.info("开始API测试...")
    
    # 测试API连接
    qwen_ok = test_qwen_api()
    deepseek_ok = test_deepseek_api()
    
    if not qwen_ok and not deepseek_ok:
        logger.error("所有API测试失败")
        return
    
    # 加载测试数据
    test_data = load_test_data('data/tricks/fusion_results_all.json')
    if not test_data:
        logger.error("无法加载测试数据")
        return
    
    # 提取公式进行测试
    formulas = list(test_data.get('results', {}).keys())[:5]  # 测试前5个公式
    
    if qwen_ok:
        logger.info("开始通义千问批量测试...")
        run_batch_test(formulas, "qwen")
    
    if deepseek_ok:
        logger.info("开始DeepSeek批量测试...")
        run_batch_test(formulas, "deepseek")
    
    logger.info("所有测试完成")

if __name__ == "__main__":
    main() 