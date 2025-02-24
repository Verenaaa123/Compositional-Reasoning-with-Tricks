import sympy as sp
from sympy import expand, parse_expr
import random
import re
from trick_rules.rule_module import FormulaManipulator



class Operations():
    #import pdb;
    def __init__(self):
        self.reset_counters()
        self.operations_list = [1, 1, 2, 2,2,2, 3, 3, 4, 4,4,4, 4, 4]
        self.formula_manipulator = FormulaManipulator()
        

    def reset_counters(self):
        self.counters = {
            'find_right_operand': 0,
            'concatenate_formulas': 0,
            'generate_formulas': 0,
        }


    #表达式展开
    def find_right_operand(self, expression):
        if isinstance(expression, list):
            expr = expression[0]
        elif isinstance(expression, tuple):
            expr = expression[0]
        else:
            expr = expression

        if isinstance(expr, sp.Eq):
            expr = expr.rhs 
        
        expr_str = str(expr)
        local_dict = {
            'sin': sp.sin,
            'cos': sp.cos,
            'tan': sp.Function('tan'),
            'cot': sp.Function('cot'),
            'pi': sp.Symbol('pi'),
            'alpha': sp.Symbol('alpha'),
            'beta': sp.Symbol('beta'),
            'a': sp.Symbol('a'),
            'b': sp.Symbol('b'),
            'n': sp.Symbol('n'),
            'k': sp.Symbol('k')
        }

        # 移除表达式外层括号
        if expr_str.startswith('(') and expr_str.endswith(')'):
            expr_str = expr_str[1:-1]
        
        # 处理乘法表达式
        if '*' in expr_str:
            parts = expr_str.split('*')
            processed_parts = []
            for part in parts:
                part = part.strip()
                if part.startswith('(') and part.endswith(')'):
                    part = part[1:-1]
                processed_parts.append(part)
            expr_str = '*'.join(processed_parts)
        
        try:
            # 尝试直接解析
            sympy_expr = parse_expr(expr_str, local_dict=local_dict)
            expanded = expand(sympy_expr)
            return str(expanded)
        except:
            # 如果直接解析失败，尝试分段处理
            try:
                parts = expr_str.split('*')
                processed_parts = []
                for part in parts:
                    part = part.strip()
                    part_expr = parse_expr(part, local_dict=local_dict)
                    processed_parts.append(part_expr)
                
                # 重新组合表达式
                result = processed_parts[0]
                for part in processed_parts[1:]:
                    result = result * part
                    
                expanded = expand(result)
                return str(expanded)
            except:
                # 如果所有尝试都失败，返回原始表达式
                return expr_str
       
   

    #拼接
    def concatenate_formulas(self, formula, all_tricks, results=None):
        # 如果输入是列表或元组，获取第一个元素
        if isinstance(formula, list):
            formula = formula[0]
        elif isinstance(formula, tuple):
            formula = formula[0]
        
        # 获取原始等式的左右两边
        if isinstance(formula, sp.Eq):
            orig_left = str(formula.lhs)
            orig_right = str(formula.rhs)
        else:
            formula_str = str(formula)
            parts = formula_str.split('=', 1)
            if len(parts) < 2:
                return formula_str
            orig_left = parts[0].strip()
            orig_right = parts[1].strip()
        
        # 收集所有有效的等式
        valid_tricks = []
        
        # 添加 all_tricks 中的等式
        for trick in all_tricks.keys():
            if '=' in trick:
                valid_tricks.append(trick)
        
        # 只在 results 存在时添加之前的结果
        if results:
            for result in results.values():
                for operand in result.get('fusion_operands', []):
                    if operand.get('operation') == 2:
                        formula = operand.get('result', '')
                        if '=' in formula:
                            valid_tricks.append(formula)
        
        if not valid_tricks:
            return f"{orig_left} = {orig_right}"
        
        # 随机选择要添加的公式数量
        max_additions = min(len(valid_tricks), 3)
        num_additions = random.randint(1, max_additions)
        
        # 随机选择公式并分别处理左右两边
        new_left_parts = [orig_left]
        new_right_parts = [orig_right]
        
        # 随机选择不重复的公式
        selected_tricks = random.sample(valid_tricks, num_additions)
        
        for trick in selected_tricks:
            parts = trick.split('=', 1)
            if len(parts) == 2:
                trick_left, trick_right = parts
                new_left_parts.append(trick_left.strip())
                new_right_parts.append(trick_right.strip())
        
        # 组合新的等式
        new_left = ' + '.join(new_left_parts)
        new_right = ' + '.join(new_right_parts)
        
        return f"{new_left} = {new_right}"
       
    

    # 乱序因子
    def generate_formulas(self, formula):
        if isinstance(formula, list):
            formula = formula[0]
        elif isinstance(formula, tuple):
            formula = formula[0]
 
        formula_str = str(formula)
        
        if '==' in formula_str:
            left_side, right_side = formula_str.split('==', 1)
        elif '=' in formula_str:
            left_side, right_side = formula_str.split('=', 1)
        else:
            return formula_str
        
        left_factors = re.findall(r'\((.*?)\)', left_side)
        if not left_factors:
            return formula_str
        
        # 生成新的左边表达式
        if len(left_factors) >= 2:
            # 随机打乱因子顺序
            random.shuffle(left_factors)
            new_left = f"({')('.join(left_factors)})"
        else:
            new_left = left_side.strip()
        
        # 返回完整的等式字符串
        return f"{new_left} = {right_side.strip()}"
        
        

    def replace_with_formula(self, formula, all_tricks):
        # 如果输入是列表或元组，获取第一个元素
        if isinstance(formula, list):
            formula = formula[0]
        elif isinstance(formula, tuple):
            formula = formula[0]
        
        # 获取原始等式的左右两边
        if isinstance(formula, sp.Eq):
            # 将 Eq 对象转换为字符串格式的等式
            orig_left = str(formula.lhs)
            orig_right = str(formula.rhs)
            formula_str = f"{orig_left} = {orig_right}"
        else:
            formula_str = str(formula)
            if '=' not in formula_str:
                return formula_str
            orig_left, orig_right = formula_str.split('=', 1)
            orig_left = orig_left.strip()
            orig_right = orig_right.strip()
        
        # 随机选择一个替换公式
        if all_tricks:
            replacement = random.choice(list(all_tricks.keys()))
            if '=' in replacement:
                repl_left, repl_right = replacement.split('=', 1)
                repl_left = repl_left.strip()
                repl_right = repl_right.strip()
                
                # 随机决定替换左边还是右边，并返回字符串格式
                if random.choice([True, False]):
                    return f"{repl_left} = {orig_right}"
                else:
                    return f"{orig_left} = {repl_right}"
        
        return formula_str
            


    def execute_operations(self, user_formula, all_tricks):
        results = {}
        times = random.randint(1, 10)
        
        # 为每个公式重置计数器
        operation_counters = {
            'find_right_operand': 0,
            'concatenate_formulas': 0,
            'generate_formulas': 0,
            'replace_formula': 0
        }
        
        # 检查是否为纯数字表达式
        def is_numeric(expr_str):
            cleaned = expr_str.replace(' ', '').replace('+', '').replace('-', '').replace('*', '').replace('/', '').replace('=', '')
            try:
                float(cleaned)
                return True
            except ValueError:
                return False

        if is_numeric(str(user_formula)):
            return results
        
        for i in range(times):
            result = {
                "formula": {
                    "left": None,
                    "right": None,
                },
                'fusion_operands': [],
                'complexity': None,
            }
            
            # 解析公式
            formula = self.formula_manipulator.parse_user_formula(user_formula)
            if formula is None:
                continue
            
            result['formula']['left'] = str(self.formula_manipulator.separate_left(user_formula))
            result['formula']['right'] = str(self.formula_manipulator.separate_right(user_formula))
      
            operation = random.choice(self.operations_list)
            operand_result = None
            
            if operation == 1:
                if not is_numeric(str(formula)):
                    operand_result = self.find_right_operand(formula)
                    operation_counters['find_right_operand'] += 1
            elif operation == 2:
                if not is_numeric(str(formula)):
                    operand_result = self.concatenate_formulas(formula, all_tricks, results)
                    operation_counters['concatenate_formulas'] += 1
            elif operation == 3:
                if not is_numeric(str(formula)):
                    operand_result = self.generate_formulas(formula)
                    operation_counters['generate_formulas'] += 1
            elif operation == 4:
                operand_result = self.replace_with_formula(formula, all_tricks)
                operation_counters['replace_formula'] = manipulator.calculate_formula_replace_score(formula, operand_result)
            if operand_result is not None:
                result['fusion_operands'].append({
                    "operation": operation,
                    "result": str(operand_result)
                })

            result['complexity'] = operation_counters.copy()
            results[str(i)] = result
        
        return results


    def get_counters(self):
            return self.counters


    def get_operation_name(self, operation):
        operations = {
            1: 'find_right_operand',
            2: 'concatenate_formulas',
            3: 'generate_formulas',
            4: 'replace_formula'  # 添加新操作名称
        }
        return operations.get(operation, 'unknown')


manipulator = FormulaManipulator()





