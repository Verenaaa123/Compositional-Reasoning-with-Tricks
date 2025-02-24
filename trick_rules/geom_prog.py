import sympy
import random
from trick_rules.rule_module import FormulaManipulator

class geom_prog(FormulaManipulator):
    def __init__(self):
        super().__init__()
        self.set_allowed_operations([1, 2, 3, 4, 5, 6])

    def generate_left_side(self, a_1, q, n):
      
        replace_a_1 = random.choice([True, False])
        replace_n = random.choice([True, False])
        replace_q = random.choice([True, False])
        if replace_a_1 and replace_n and replace_q:
            replace_n = False  # 至少保留一个变量

        new_a_1 = self.random_variable_or_constant(a_1, replace_a_1)
        new_q = self.random_variable_or_constant(q, replace_q)
        new_n = self.random_variable_or_constant(n, replace_n)

        left_side = f"{new_a_1}, "
        for i in range(1, 5):
            left_side += f"{new_a_1}+{i}, " if i < 4 else f"{new_a_1}+{i}..."

        # 如果左式存在被替换为常数的 a_1, an，则将右式对应的变量换元
        if replace_a_1 or replace_n or replace_q:
            right_side = self.generate_right_side(new_a_1, new_q, new_n)
        else:
            right_side = f"{a_1}*({1 - {q}**{n}})/(1 - {q})"

        return left_side, right_side


    def generate_right_side(self, a_1, q, n):
        # 右式变换器
        right_side = f"({a_1}*(1 - {q}**{n}))/(1 - {q})"
        return right_side


    def random_variable_or_constant(self, variable, replace):
        if replace:
            if random.choice([True, False]):
                return f"{random.randint(1, 10)}"
            else:
                return self.variable_library[random.randint(0, len(self.variable_library) - 1)]
        else:
            return variable


    def run(self, data):
        result_list = {}
        
        # 解析输入的公式
        formula, variables = self.parse_user_formula(data)
        
        # 生成左右两边
        a_1_sym, q_sym, n_sym = sympy.symbols('a_1 q n')
        left_side, right_side = self.generate_left_side(a_1_sym, q_sym, n_sym)
        
        # 执行变换操作
        results = self.execute_functions(data)
        
        # 构建返回结果
        for idx, result in enumerate(results):
            result_list[str(idx + 1)] = {
                "formula": {
                    "left": left_side,
                    "right": right_side
                },
                "tricks": result.get("tricks", []),
                "complexity": result.get("complexity", {})
            }
        
        return result_list
    
