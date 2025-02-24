from .rule_module import FormulaManipulator

class cubi_sum_diff(FormulaManipulator):
    def __init__(self):
        super().__init__()
        self.set_allowed_operations([1, 2, 3, 4, 5, 6])

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