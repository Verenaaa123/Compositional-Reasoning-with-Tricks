import sympy as sp
from sympy import expand, Eq
import random
import re
from sympy import UnevaluatedExpr
from trick_rules.rule_module import FormulaManipulator



class Operations():
    #import pdb;
    def __init__(self):
        self.reset_counters()
        self.operations_list = [1,2,3,4,5,6]
        self.formula_manipulator = FormulaManipulator()
        self.local_dict = self.formula_manipulator.local_dict
        self.variable_library = list('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') + \
                               [chr(i) for i in range(0x03B1, 0x03C9 + 1)]
        self.variable_library = [
            self.local_dict[key] 
            for key in self.local_dict 
            if isinstance(self.local_dict[key], sp.Symbol)
        ]


    def get_right_str(self, expr) -> str:
        # 处理 SymPy 等式对象
        if isinstance(expr, sp.Eq):
            return str(expr.rhs)
        
        # 处理旧逻辑（字符串/列表/元组）
        if isinstance(expr, (list, tuple)):
            expr_ = expr[0]  # 提取第一个元素
            return str(expr_)
        if isinstance(expr, str) and '=' in expr:
            return expr.split('=', 1)[1].strip()  # 分割右侧表达式
        
        # 其他类型抛出明确错误
        raise TypeError(f"不支持的表达式类型: {type(expr)}")
    
    
    def get_str_expr(self, expr) -> str:
        if isinstance(expr, (list,tuple)):
            expr = expr[0]
        
        if isinstance(expr, sp.Eq):
            # 检查是否意外得到了布尔值结果
            if isinstance(expr.rhs, (sp.logic.boolalg.BooleanTrue, sp.logic.boolalg.BooleanFalse)):
                print(f"警告：检测到布尔值结果 {expr.rhs}，这可能表示前面的操作有问题")
                # 返回原始等式而不是布尔值
                return f"{str(expr.lhs)} = {str(expr.rhs)}"
            expr_str = f"{str(expr.lhs)} = {str(expr.rhs)}"
        elif isinstance(expr, str):
            expr_str = expr
        else:
            expr_str = str(expr)
        
        # 确保输出是标准等式格式
        if '==' in expr_str:
            expr_str = expr_str.replace('==', '=')
        
        return expr_str


    # def get_sp_expr(self, expr_str) -> sp.Eq:
    #     if isinstance(expr_str, (list,tuple)):
    #         expr = expr[0].split('=')[1] if '=' in expr[0] else expr
    #     elif isinstance(expr_str, str):
    #         expr = sp.sympify(expr_str.replace("=", "=="),locals=self.local_dict)
    #     expr = sp.sympify(expr_str.replace("=", "=="),locals=self.local_dict)  
    #     return expr


    def get_sp_expr(self, expr_str) -> sp.Eq:
        # 统一处理输入类型（支持字符串/列表/元组）
        if isinstance(expr_str, (list, tuple)):
            # 提取第一个元素作为待解析的字符串
            expr_str = expr_str[0]
        if isinstance(expr_str, sp.Eq):
            return expr_str
        # 确保输入是字符串类型
        if not isinstance(expr_str, str):
            raise TypeError(f"输入类型必须为 str/list/tuple，实际类型: {type(expr_str)}")

        # 检查等号是否存在
        if '=' not in expr_str:
            raise ValueError(f"输入字符串必须包含等号: {expr_str}")

        # 分割左右表达式
        left_str, right_str = expr_str.split('=', 1) 
        
        lhs = sp.sympify(left_str.strip(), locals=self.local_dict)
        rhs = sp.sympify(right_str.strip(), locals=self.local_dict)
        return sp.Eq(lhs, rhs, evaluate=False)  # 添加 evaluate=False 防止自动求值
        



    def reset_counters(self):
        self.counters = {
            'find_right_operand': 0,
            'concatenate_formulas': 0,
            'generate_formulas': 0,
            'replace_with_formula':0,
            'combining_similar_terms':0,
            'power_transform': 0
        }


    #表达式展开
    def find_right_operand(self, expr):
        if isinstance(expr, tuple):
            expr = expr[0]
        if not isinstance(expr, sp.Eq):
            expr = self.get_sp_expr(expr)
        
        try:
            # 只对右侧表达式进行展开，而不是整个等式
            expanded_rhs = sp.expand(expr.rhs, locals=self.local_dict)
            # 构造新的等式
            return f"{str(expr.lhs)} = {str(expanded_rhs)}"
        except:
            # 如果直接展开失败，返回原始等式
            return f"{str(expr.lhs)} = {str(expr.rhs)}"


    # 合并同类项
    def combining_similar_terms(self, expr):
        expr_sp = self.get_sp_expr(expr)
        combined = sp.collect(expr_sp.rhs, self.variable_library)
        # 确保返回标准等式格式
        return f"{str(expr_sp.lhs)} = {str(combined)}"


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
        formula_str = self.get_str_expr(formula)
        if '=' in formula_str:
            sp_expr = self.get_sp_expr(formula_str)
            orig_left_expr = sp_expr.lhs
            orig_right_expr = sp_expr.rhs
        else:
            orig_expr = sp.sympify(formula_str, locals=self.local_dict)
            orig_left_expr = orig_expr
            orig_right_expr = sp.Integer(0)

        valid_replacements = []
        orig_right_vars = orig_right_expr.free_symbols

        # 遍历所有技巧公式的右侧
        for trick_formula in all_tricks:
            if '=' in trick_formula:
                _, trick_right = trick_formula.split('=', 1)
                trick_right_expr = sp.sympify(trick_right.strip(), locals=self.local_dict)
                # 使用 UnevaluatedExpr 包裹表达式以保留括号
                trick_right_paren = UnevaluatedExpr(trick_right_expr)

                for var in orig_right_vars:
                    # 替换变量为带括号的表达式
                    new_right = orig_right_expr.subs(var, trick_right_paren)
                    # 转换为字符串时自动添加括号
                    new_formula = f"{sp.sstr(orig_left_expr)} = {sp.sstr(new_right)}"
                    valid_replacements.append(new_formula)
        
        return random.choice(valid_replacements) if valid_replacements else formula_str
            

    def power_transform(self, formula, all_tricks):
        
        if isinstance(formula, (list, tuple)):
            formula = formula[0]
        
        # 获取输入等式的字符串表示
        formula_str = self.get_str_expr(formula)
        
        # 随机选择转换方式
        transform_type = random.choice(['number', 'trick'])
        
        if transform_type == 'number':
            # 随机选择一个2到10之间的数字作为底数
            base = random.randint(2, 10)
            # 构造新的等式
            new_formula = f"{base}^{formula_str}"
        else:
            # 从all_tricks中随机选择一个等式
            valid_tricks = [trick for trick in all_tricks.keys() if '=' in trick]
            if not valid_tricks:
                return formula_str
            
            selected_trick = random.choice(valid_tricks)
            # 只使用等式的右侧作为底数
            base = selected_trick.split('=', 1)[1].strip()
            # 构造新的等式
            new_formula = f"({base})^{formula_str}"
        
        return new_formula

    def execute_operations(self, user_formula, all_tricks, complexity):
        results = {}
        times = random.randint(1, 10)
        
        operation_counters = {
            'find_right_operand': 0,
            'concatenate_formulas': 0,
            'generate_formulas': 0,
            'replace_formula': 0,
            'combining_similar_terms': 0,
            'power_transform': 0
        }
        
        # 检查是否为纯数字表达式
        def is_numeric(expr_str):
            cleaned = expr_str.replace(' ', '').replace('+', '').replace('-', '').replace('*', '').replace('/', '').replace('=', '').replace('**', '').replace('*', '').replace('(', '').replace(')', '')
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
                'composition_complexity': 0,
                'fusion_complexity': 0,
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
                operation_counters['replace_formula'] += 1
            elif operation == 5:
                operand_result = self.combining_similar_terms(formula)
                operation_counters['combining_similar_terms'] += 1
            elif operation == 6:
                operand_result = self.power_transform(formula, all_tricks)
                operation_counters['power_transform'] += 1
            
            if operand_result is not None:
                # 确保结果经过 get_str_expr 处理
                formatted_result = self.get_str_expr(operand_result)
                result['fusion_operands'].append({
                    "operation": operation,
                    "result": formatted_result
                })

            result['fusion_complexity'] = operation_counters.copy()
            results[str(i)] = result
            # 处理 complexity 为 None 的情况
            if complexity is None:
                complexity = 0
            result['composition_complexity'] = complexity + result['composition_complexity']
        return results
        # 此处需要修改
        # complexity中存在等式只有单侧数据，需要排查原因
        


    # def get_counters(self):
    #         return self.counters


    # def get_operation_name(self, operation):
    #     operations = {
    #         1: 'find_right_operand',
    #         2: 'concatenate_formulas',
    #         3: 'generate_formulas',
    #         4: 'replace_formula',
    #         5: 'combining_similar_terms'
    #     }
    #     return operations.get(operation, 'unknown')


manipulator = FormulaManipulator()





