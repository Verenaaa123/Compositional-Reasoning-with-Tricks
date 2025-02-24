import random
import re
from .rule_module import FormulaManipulator

class indu_form(FormulaManipulator):
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

        # 定义数字范围
        min_val, max_val = 1, 100

        # 随机选择一个数字
        random_number = random.randint(min_val, max_val)

        # 替换等式中的'k'字符为随机数字
        user_formula_k = formula.replace('k', str(random_number))

        return user_formula_k                                                      

    def run(self, data):
        result_list = {}
        
        # 解析输入的公式
        expr, variables = self.parse_user_formula(data)
        print(f"处理公式: {data}")
        print(f"变量列表: {[str(v) for v in variables]}")
        
        # 执行变换操作
        results = self.execute_functions(data)
        
        # 构建返回结果
        for idx, result in enumerate(results):
            result_list[str(idx + 1)] = {
                "formula": result["formula"],
                "tricks": result["tricks"],
                "complexity": result["complexity"]
            }
        
        return result_list