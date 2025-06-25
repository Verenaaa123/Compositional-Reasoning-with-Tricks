#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import signal
import time
sys.path.append('.')

from fusion.operations import Operations
from config import all_tricks

def timeout_handler(signum, frame):
    raise TimeoutError("操作超时")

def main():
    """主程序 - 安全版本"""
    print("开始运行安全版本的融合程序...")
    
    # 创建Operations实例
    ops = Operations()
    
    # 转换sympy公式为字符串
    formula_strings = {}
    for formula, rule in all_tricks.items():
        try:
            # 将sympy公式转换为字符串
            formula_str = str(formula)
            formula_strings[formula_str] = rule
        except Exception as e:
            print(f"转换公式失败: {formula}, 错误: {e}")
            continue
    
    print(f"成功转换了 {len(formula_strings)} 个公式")
    
    results = {}
    success_count = 0
    error_count = 0
    
    for i, (formula, rule) in enumerate(formula_strings.items()):
        print(f"\n处理公式 {i+1}/{len(formula_strings)}: {formula}")
        
        try:
            # 设置超时（60秒）
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)
            
            # 执行操作
            formula_results = ops.execute_operations(formula, all_tricks, complexity=30)
            
            # 取消超时
            signal.alarm(0)
            
            if formula_results:
                results[formula] = {
                    "rule": rule,
                    "operations": formula_results
                }
                success_count += 1
                
                # 分析第一个结果
                first_result = formula_results['0']
                operands = first_result['fusion_operands']
                print(f"  成功生成 {len(operands)} 个操作")
                
                # 统计操作类型
                operation_counts = {
                    'concatenate_formulas': 0,
                    'replace_formula': 0,
                    'power_transform': 0,
                    'combining_similar_terms': 0,
                    'find_right_operand': 0,
                    'generate_formulas': 0
                }
                
                for operand in operands:
                    operation = operand['operation']
                    if operation == 2:
                        operation_counts['concatenate_formulas'] += 1
                    elif operation == 4:
                        operation_counts['replace_formula'] += 1
                    elif operation == 6:
                        operation_counts['power_transform'] += 1
                    elif operation == 5:
                        operation_counts['combining_similar_terms'] += 1
                    elif operation == 1:
                        operation_counts['find_right_operand'] += 1
                    elif operation == 3:
                        operation_counts['generate_formulas'] += 1
                
                # 检查是否符合要求
                valid = (operation_counts['concatenate_formulas'] >= 3 and
                        operation_counts['replace_formula'] >= 3 and
                        operation_counts['power_transform'] >= 3 and
                        operation_counts['combining_similar_terms'] == 1)
                
                print(f"  符合要求: {valid}")
                
            else:
                print(f"  没有生成结果")
                error_count += 1
                
        except TimeoutError:
            print(f"  处理超时，跳过")
            error_count += 1
            signal.alarm(0)  # 取消超时
        except Exception as e:
            print(f"  处理失败: {e}")
            error_count += 1
            signal.alarm(0)  # 取消超时
        
        # 每处理10个公式保存一次中间结果
        if (i + 1) % 10 == 0:
            temp_file = f'data/tricks/fusion_results_temp_{i+1}.json'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump({"results": results}, f, ensure_ascii=False, indent=4)
            print(f"  已保存中间结果到: {temp_file}")
    
    # 保存最终结果
    output_file = 'data/tricks/fusion_results_safe.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"results": results}, f, ensure_ascii=False, indent=4)
    
    print(f"\n程序完成!")
    print(f"成功处理: {success_count} 个公式")
    print(f"处理失败: {error_count} 个公式")
    print(f"结果已保存到: {output_file}")
    
    # 分析结果
    if results:
        total_operations = 0
        valid_sequences = 0
        
        for formula, result in results.items():
            for op_key, operation in result['operations'].items():
                operands = operation.get('fusion_operands', [])
                total_operations += len(operands)
                
                # 检查是否符合要求
                operation_counts = {}
                for operand in operands:
                    op = operand['operation']
                    operation_counts[op] = operation_counts.get(op, 0) + 1
                
                if (operation_counts.get(2, 0) >= 3 and
                    operation_counts.get(4, 0) >= 3 and
                    operation_counts.get(6, 0) >= 3 and
                    operation_counts.get(5, 0) == 1):
                    valid_sequences += 1
        
        print(f"\n结果分析:")
        print(f"总操作数: {total_operations}")
        print(f"符合要求的序列: {valid_sequences}")

if __name__ == "__main__":
    main() 