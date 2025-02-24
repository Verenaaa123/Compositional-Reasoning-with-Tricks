from trick_rules.rule_module import FormulaManipulator
from config import all_tricks 
import argparse
import json
import sympy
import random

from trick_rules import *
from fusion.operations import Operations

alpha, beta = sympy.symbols('α β')
a, b, n, pi, k = sympy.symbols('a b n pi k')
S_n, a_1, q, d = sympy.symbols('S_n a_1 q d')

def tricks_fusion():
    print("开始执行 tricks_fusion...")
    formula_manipulator = FormulaManipulator()
    all_rules_results = {}
    
    total_tricks = len(all_tricks)
    current_trick = 0
    
    # 按规则类型分组处理公式
    grouped_tricks = {}
    for trick_expr, rule_name in all_tricks.items():
        if rule_name not in grouped_tricks:
            grouped_tricks[rule_name] = []
        grouped_tricks[rule_name].append(trick_expr)
    
    # 处理每个规则类型下的所有公式
    for rule_name, formulas in grouped_tricks.items():
        all_results = []
        
        for trick_expr in formulas:
            current_trick += 1
            print(f"\n处理规则: {rule_name} ({current_trick}/{total_tricks})")
            print(f"原始公式: {trick_expr}")
            
            # 检查表达式是否为空
            if not trick_expr or not isinstance(trick_expr, str):
                print(f"跳过无效公式: {trick_expr}")
                continue

            expr, variables = formula_manipulator.parse_user_formula(trick_expr)
            if expr is None:
                print(f"无法解析公式: {trick_expr}")
                continue
                
            print(f"解析结果: expr={expr}, variables={variables}")
            
            formula_results = []
            for transformation_round in range(10):
                print(f"执行第 {transformation_round + 1}/10 轮变换...")
                
                num_operations = random.randint(1, 10)
                print(f"本轮将执行 {num_operations} 次操作...")
                
                results = formula_manipulator.execute_functions(trick_expr, times=num_operations)
                
                if results:
                    formula_results.append({
                        "transformation_round": transformation_round + 1,
                        "num_operations": num_operations,
                        "results": results
                    })
            
            all_results.append({
                "original_expression": trick_expr,
                "executions": formula_results
            })
                
        
        all_rules_results[rule_name] = {
            "rule_name": rule_name,
            "formulas": all_results
        }
        
        print(f"完成 {rule_name} 的所有公式融合")
    
    filepath = '/Users/wyl/Desktop/pythonProject_3/data/tricks/fusion_results_all.json'
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(all_rules_results, f, ensure_ascii=False, indent=4)
    print(f"所有规则的融合结果已保存到 {filepath}")


def tricks_construction(trick_name=None):
    ops = Operations()
    
    fusion_file = f'/Users/wyl/Desktop/pythonProject_3/data/tricks/fusion_results_all.json'
    with open(fusion_file, 'r', encoding='utf-8') as f:
        fusion_results = json.load(f)
    
    all_formulas = {}
    
    # 首先添加 all_tricks 中的公式
    for formula, rule in all_tricks.items():
        all_formulas[formula] = rule
    
    # 从 fusion_results 中提取 formula_after
    for rule_name, rule_data in fusion_results.items():
        if trick_name and rule_name != trick_name:
            continue
            
        for formula_info in rule_data.get('formulas', []):
            for execution in formula_info.get('executions', []):
                for result in execution.get('results', []):
                    for trick in result.get('tricks', []):
                        if 'formula_after' in trick:
                            all_formulas[trick['formula_after']] = rule_name
    
    # 使用收集到的所有公式执行操作
    results = {}
    for formula, rule in all_formulas.items():
        operation_results = ops.execute_operations(formula, all_formulas)
        if formula not in results:
            results[formula] = {
                "rule": rule,
                "operations": operation_results
            }
    
    file_dir = '/Users/wyl/Desktop/pythonProject_3/data/composition'
    filename = 'construct_result_all.json' 
    filepath = f'{file_dir}/{filename}'

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({
            "results": results
        }, f, ensure_ascii=False, indent=4)
    print(f"Construction results saved in {filepath}")

# 命令行参数解析
parser = argparse.ArgumentParser(description='Template scripts. function 1: Hello World')
parser.add_argument('--function', type=str, default=0, help='use this to specify function!')
parser.add_argument('--v1', type=int, default=0, help='int value')
parser.add_argument('--s1', type=str, default='none', help='string 1')

args = parser.parse_args()

if __name__ == "__main__":
    if args.function == '0':
        print("no function indicate")
    elif args.function == '1':
        rule_name = args.s1 if args.s1 != 'none' else None
        tricks_construction(rule_name)
    elif args.function == '2':
        tricks_fusion() 