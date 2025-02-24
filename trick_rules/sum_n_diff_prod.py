import random
import re
from .rule_module import FormulaManipulator

class sum_n_diff_prod(FormulaManipulator):
    def __init__(self):
        super().__init__()
        self.set_allowed_operations([1, 2, 3, 4, 5, 6])

    def swap_factors(expr_str):
        pattern = r'\(([^\(\)]+) \+ ([^\(\)]+)\)'

        # 函数用于交换匹配的两个项
        def swap(match):
            terms = match.groups()  # 获取两个匹配的项
            return f'({terms[1]} + {terms[0]})'  # 返回交换后的项

        # 使用re.sub()函数替换匹配的项
        new_equation = re.sub(pattern, swap, expr_str)

        return new_equation

    def replace_with_number(self, formula):
        if isinstance(formula, str):
            min_val, max_val = 1, 100
            random_number = random.randint(min_val, max_val)
            return formula.replace('k', str(random_number))
        return str(formula)
       

    def run(self, data):
        result_list = {}
        
        # 解析输入的公式
        expr, variables = self.parse_user_formula(data)
        if expr is None:
            return {}
        
        print(f"处理公式: {data}")
        print(f"变量列表: {[str(v) for v in variables]}")
        
        # 执行变换操作
        results = self.execute_functions(data)
        
        # 构建返回结果
        for idx, result in enumerate(results):
            if isinstance(result, dict):
                result_list[str(idx + 1)] = {
                    "formula": result.get("formula", {}),
                    "tricks": result.get("tricks", []),
                    "complexity": result.get("complexity", {})
                }
        
        return result_list