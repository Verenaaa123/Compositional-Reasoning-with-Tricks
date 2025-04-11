import sympy as sp
from sympy import factor
from sympy.abc import alpha, beta,gamma, delta, epsilon, zeta, eta, theta,iota, kappa, mu, nu, xi, omicron, pi, rho,sigma, tau, upsilon, phi, chi, psi, omega

import random
from sympy import Poly
import re
from thefuzz import fuzz 
import sys
sys.path.append('..')
from config import all_tricks
from sympy.logic.boolalg import Boolean 


class FormulaManipulator:
    def __init__(self):
        self.variable_library = list('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') + \
                               [chr(i) for i in range(0x03B1, 0x03C9 + 1)]
        self.operations_list = [1, 2, 3, 4, 5, 6, 7, 8]
        self.local_dict = {
            # 三角函数
            'sin': sp.Function('sin'),
            'cos': sp.Function('cos'),
            'tan': sp.Function('tan'),
            'cot': sp.Function('cot'),

            # 小写希腊字母
            'π': sp.Symbol('π'),          # \u03C0
            'α': sp.Symbol('α'),          # \u03B1
            'β': sp.Symbol('β'),          # \u03B2
            'γ': sp.Symbol('γ'),          # \u03B3
            'δ': sp.Symbol('δ'),          # \u03B4
            'ε': sp.Symbol('ε'),          # \u03B5
            'ζ': sp.Symbol('ζ'),          # \u03B6
            'η': sp.Symbol('η'),          # \u03B7
            'θ': sp.Symbol('θ'),          # \u03B8
            'ι': sp.Symbol('ι'),          # \u03B9
            'κ': sp.Symbol('κ'),          # \u03BA
            'λ': sp.Symbol('λ'),          # \u03BB
            'μ': sp.Symbol('μ'),          # \u03BC
            'ν': sp.Symbol('ν'),          # \u03BD
            'ξ': sp.Symbol('ξ'),          # \u03BE
            'ο': sp.Symbol('ο'),          # \u03BF
            'ρ': sp.Symbol('ρ'),          # \u03C1
            'σ': sp.Symbol('σ'),          # \u03C3
            'τ': sp.Symbol('τ'),          # \u03C4
            'υ': sp.Symbol('υ'),          # \u03C5
            'φ': sp.Symbol('φ'),          # \u03C6
            'χ': sp.Symbol('χ'),          # \u03C7
            'ψ': sp.Symbol('ψ'),          # \u03C8
            'ω': sp.Symbol('ω'),          # \u03C9

            # 大写希腊字母
            'Α': sp.Symbol('Α'),          # \u0391
            'Β': sp.Symbol('Β'),          # \u0392
            'Γ': sp.Symbol('Γ'),          # \u0393
            'Δ': sp.Symbol('Δ'),          # \u0394
            'Θ': sp.Symbol('Θ'),          # \u0398
            'Λ': sp.Symbol('Λ'),          # \u039B
            'Σ': sp.Symbol('Σ'),          # \u03A3
            'Ω': sp.Symbol('Ω'),          # \u03A9
            
            # 基础变量
            'a': sp.Symbol('a'),
            'b': sp.Symbol('b'),
            'c': sp.Symbol('c'),
            'd': sp.Symbol('d'),
            'e': sp.Symbol('e'),
            'f': sp.Symbol('f'),
            'g': sp.Symbol('g'),
            'h': sp.Symbol('h'),
            'i': sp.Symbol('i'),
            'j': sp.Symbol('j'),
            'k': sp.Symbol('k'),
            'l': sp.Symbol('l'),
            'm': sp.Symbol('m'),
            'n': sp.Symbol('n'),
            'o': sp.Symbol('o'),
            'p': sp.Symbol('p'),
            'q': sp.Symbol('q'),
            'r': sp.Symbol('r'),
            's': sp.Symbol('s'),
            't': sp.Symbol('t'),
            'u': sp.Symbol('u'),
            'v': sp.Symbol('v'),
            'w': sp.Symbol('w'),
            'x': sp.Symbol('x'),
            'y': sp.Symbol('y'),
            'z': sp.Symbol('z'),
            'A': sp.Symbol('A'),
            'B': sp.Symbol('B'),
            'C': sp.Symbol('C'),
            'D': sp.Symbol('D'),
            'E': sp.Symbol('E'),
            'F': sp.Symbol('F'),
            'G': sp.Symbol('G'),
            'H': sp.Symbol('H'),
            'I': sp.Symbol('I'),
            'J': sp.Symbol('J'),
            'K': sp.Symbol('K'),
            'L': sp.Symbol('L'),
            'M': sp.Symbol('M'),
            'N': sp.Symbol('N'),
            'O': sp.Symbol('O'),
            'P': sp.Symbol('P'),
            'Q': sp.Symbol('Q'),
            'R': sp.Symbol('R'),
            'S': sp.Symbol('S'),
            'T': sp.Symbol('T'),
            'U': sp.Symbol('U'),
            'V': sp.Symbol('V'),
            'W': sp.Symbol('W'),
            'X': sp.Symbol('X'),
            'Y': sp.Symbol('Y'),
            'Z': sp.Symbol('Z')
            
        }
        self.variable_library = [
            self.local_dict[key] 
            for key in self.local_dict 
            if isinstance(self.local_dict[key], sp.Symbol)
        ]



    def parse_user_formula(self, formula_str):
        print(f"\n=== 开始解析公式 ===")
        print(f"输入公式: '{formula_str}'")
        
        # formula_str = str(formula_str).replace('==', '=').replace('α','alpha').replace('β','beta').replace('π','pi')

        if '=' in formula_str:
            left, right = formula_str.split('=', 1)
            left_expr = sp.sympify(left, locals=self.local_dict, evaluate=False)
            right_expr = sp.sympify(right, locals=self.local_dict, evaluate=False)
            expr = sp.Eq(left_expr, right_expr, evaluate=False)  # 禁止自动化简为布尔值
        else:
            expr = sp.sympify(formula_str, locals=self.local_dict, evaluate=False)
        variables = list(expr.free_symbols)
        return expr,variables



    def separate_left(self, formula):
        formula = str(formula)
        formula = formula.replace('==', '=')
        sides = re.split(r'=(?!=)', formula)
        
        for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
            if c not in self.local_dict:
                self.local_dict[c] = sp.Symbol(c)
        lower_greek = [
    'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta',
    'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 'omicron', 'pi', 'rho',
    'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega'
]
        upper_greek = [name.capitalize() for name in lower_greek]
        greek_letters = lower_greek+upper_greek
        for letter in greek_letters:
            self.local_dict[letter] = sp.Symbol(letter)
        
        if len(sides) == 2:
            return sp.sympify(sides[0].strip(), locals=self.local_dict)
        return sp.sympify(formula, locals=self.local_dict)



    def separate_right(self, formula):
        formula = str(formula)
        formula = formula.replace('==', '=')
        sides = re.split(r'=(?!=)', formula)
        
        for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
            if c not in self.local_dict:
                self.local_dict[c] = sp.Symbol(c)
        
        lower_greek = [
    'α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ',
    'ι', 'κ', 'λ', 'μ', 'ν', 'ξ', 'ο', 'π', 'ρ',
    'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω'
]
        upper_greek = [
    'Α', 'Β', 'Γ', 'Δ', 'Ε', 'Ζ', 'Η', 'Θ',
    'Ι', 'Κ', 'Λ', 'Μ', 'Ν', 'Ξ', 'Ο', 'Π', 'Ρ',
    'Σ', 'Τ', 'Υ', 'Φ', 'Χ', 'Ψ', 'Ω'
]
        greek_letters = lower_greek+upper_greek
        for letter in greek_letters:
            self.local_dict[letter] = sp.Symbol(letter)
        
        if len(sides) == 2:
            return sp.sympify(sides[1].strip(), locals=self.local_dict)
        return sp.sympify(formula, locals=self.local_dict)
      


    def multiply_with_num(self, formula):
        """对等式两侧乘以同一个随机数/分数，返回字符串形式的等式"""
        if isinstance(formula, sp.Eq):
            lhs, rhs = formula.lhs, formula.rhs
        else:  
            if isinstance(formula, str):
                if '=' not in formula:
                    return str(formula)  # 非等式直接返回
                # 分割并解析左右两侧，禁用求值
                lhs_str, rhs_str = formula.split('=', 1)
                lhs = sp.sympify(lhs_str.strip(), locals=self.local_dict, evaluate=False)
                rhs = sp.sympify(rhs_str.strip(), locals=self.local_dict, evaluate=False)
                formula = sp.Eq(lhs, rhs, evaluate=False)
            else:
                return str(formula)  # 非字符串非等式类型
            lhs = formula.lhs
            rhs = formula.rhs
        
        multiplier = random.choice([
            random.randint(1, 10),
            sp.Rational(random.randint(1, 5), random.randint(2, 6))
        ])
        
        # 应用乘数并保持等式结构
        new_lhs = lhs * multiplier
        new_rhs = rhs * multiplier
        new_eq = sp.Eq(new_lhs, new_rhs, evaluate=False)  # 关键修改：禁用求值
        
        return f"{sp.sstr(new_eq.lhs)} = {sp.sstr(new_eq.rhs)}"
        


    def add_elements(self, expr):
        if isinstance(expr, sp.Eq):
            expr_str = f"{expr.lhs} = {expr.rhs}"
        else:
            expr_str = str(expr)  
        constant = random.randint(-5, 5)
        if constant == 0:
            constant = 1 
        if '=' in expr_str:
            left, right = expr_str.split('=', 1)
            left = left.strip()
            right = right.strip()
            
            def is_numeric(expr_str):
                try:
                    float(expr_str)
                    return True
                except ValueError:
                    return False
                
            if not is_numeric(left) and not is_numeric(right):
                left_expr = sp.sympify(left, locals=self.local_dict)
                right_expr = sp.sympify(right, locals=self.local_dict)
                if random.choice([True, False]):
                    left = left_expr + constant
                    right = right_expr + constant
                else:
                    left = left_expr - constant
                    right = right_expr - constant
                left_con = sum(term for term in left.as_ordered_terms() if term.is_number)
                left_var = sum(term for term in left.as_ordered_terms() if not term.is_number)
                combined_left = left_con + left_var
                right_con = sum(term for term in right.as_ordered_terms() if term.is_number)
                right_var = sum(term for term in right.as_ordered_terms() if not term.is_number)
                combined_right = right_con + right_var
                return f"{combined_left} = {combined_right}"           
            return expr_str
        else:
            if not any(c.isalpha() for c in expr_str):
                return f"{expr_str} = {expr_str}"
            return expr_str



    def num_replace_with_num(self, formula):
        if isinstance(formula, sp.Eq):
            eq = f"{formula.lhs} = {formula.rhs}"
        else:
            eq = str(formula)   

        if '=' in eq:
            left, right = eq.split('=', 1)
            left = left.strip()
            right = right.strip()
        else:
            left = eq
            right = eq
        # 在左右两边查找数字
        numbers = re.findall(r'\d+', left) + re.findall(r'\d+', right)
        if not numbers:
            return formula
        
        number_pool = list(range(1, 101))
        replacement_count = random.randint(1, len(numbers))
        numbers_to_replace = random.sample(numbers, replacement_count)
        
        for old_num in numbers_to_replace:
            if number_pool:
                new_num = str(random.choice(number_pool))
                number_pool.remove(int(new_num))
                # 替换左右两边的数字
                left = left.replace(old_num, new_num, 1)
                right = right.replace(old_num, new_num, 1)
        
        return f"{left} = {right}" if right else left



    def generate_unified_substitution(self, expr):
        """生成统一的变量替换规则（优先替换为符号库中的其他变量，否则替换为数字）"""
        variables = list(expr.free_symbols)
        if not variables:
            return {} 
        
        old_var = random.choice(variables)
        possible_vars = [var for var in self.variable_library if var != old_var]
        
        if possible_vars:
            new_var = random.choice(possible_vars)
            return {old_var: new_var}
        else:
            return {old_var: random.randint(1, 10)}



    def replace_with_number(self, formula):
        if isinstance(formula, sp.Eq):
            lhs, rhs = formula.lhs, formula.rhs
        elif isinstance(formula, str) and '=' in formula:
            lhs_str, rhs_str = formula.split('=', 1)
            lhs = sp.sympify(lhs_str, locals=self.local_dict, evaluate=False) 
            rhs = sp.sympify(rhs_str, locals=self.local_dict, evaluate=False) 
        else:
            return str(formula)
        
        substitution = self.generate_unified_substitution(lhs)
        new_lhs = lhs.subs(substitution)
        new_rhs = rhs.subs(substitution)
        
        return f"{sp.sstr(new_lhs)} = {sp.sstr(new_rhs)}"



    def replace_with_variable(self, formula):
        if isinstance(formula, (bool, Boolean)):
            return str(formula)
        if isinstance(formula, sp.Eq):
            lhs, rhs = formula.lhs, formula.rhs
        elif isinstance(formula, str) and '=' in formula:
            lhs_str, rhs_str = formula.split('=', 1)
            lhs = sp.sympify(lhs_str, locals=self.local_dict, evaluate=False)
            rhs = sp.sympify(rhs_str, locals=self.local_dict, evaluate=False)
        else:
            expr = sp.sympify(formula, locals=self.local_dict, evaluate=False) if isinstance(formula, str) else formula
            symbols = expr.free_symbols
            if not symbols:
                return str(expr)
            symbol_to_replace = random.choice(list(symbols))
            # 从变量库中选择新变量并转换为符号
            new_var = random.choice(self.variable_library)
            new_var_sym = sp.sympify(new_var, locals=self.local_dict)
            new_expr = expr.subs(symbol_to_replace, new_var_sym)
            return sp.sstr(new_expr)
        
        symbols = lhs.free_symbols
        if not symbols:
            return f"{sp.sstr(lhs)} = {sp.sstr(rhs)}"
        
        symbol_to_replace = random.choice(list(symbols))
        # 从变量库中选择新变量并转换为符号
        new_var = random.choice(self.variable_library)
        new_var_sym = sp.sympify(new_var, locals=self.local_dict)
        
        new_lhs = lhs.subs(symbol_to_replace, new_var_sym)
        new_rhs = rhs.subs(symbol_to_replace, new_var_sym)
        
        return f"{sp.sstr(new_lhs)} = {sp.sstr(new_rhs)}"



    def replace_with_formula(self, formula, all_tricks):
        # 解析原始公式
        formula_str = str(formula) if not isinstance(formula, str) else formula
        print(formula_str)
        if '=' in formula_str:
            orig_left, orig_right = formula_str.split('=', 1)
            orig_left_expr = sp.sympify(orig_left.strip(), locals=self.local_dict)
            orig_right_expr = sp.sympify(orig_right.strip(), locals=self.local_dict)
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
                trick_left, _ = trick_formula.split('=', 0)
                trick_left_expr = sp.sympify(trick_left.strip(), locals=self.local_dict)
            
                for var in orig_right_vars:
                    new_right = orig_right_expr.subs(var, trick_right_expr)
                    new_left = orig_left_expr.subs(var, trick_left_expr)
                    new_formula = f"{sp.sstr(new_left)} = {sp.sstr(new_right)}"
                    valid_replacements.append(new_formula)
        
        if valid_replacements:
            return random.choice(valid_replacements)
        else:
            return formula_str



    def swap_terms(self, expr, variables, pos_info=None):
        """交换项的位置（支持递归）"""
        if isinstance(expr, sp.Eq):
            expr = f"{expr.lhs} = {expr.rhs}"
        else:
            expr = str(expr)
        if pos_info is None:
            pos_info = []
        
        # 将表达式分解为项
        if isinstance(expr, sp.Add):
            terms = list(expr.args)
        elif isinstance(expr, sp.Mul):
            terms = list(expr.args)
        else:
            # 如果不是加法或乘法表达式，直接返回
            return expr, []
        
        if len(terms) < 2:
            return expr, []
       
        modified_structure = {}

        swap_times = random.randint(1, min(5, len(terms)))
        
        for i in range(swap_times):
            idx1, idx2 = random.sample(range(len(terms)), 2)
            
            terms[idx1], terms[idx2] = terms[idx2], terms[idx1]
            
            # 记录结构变化
            current_pos = pos_info + [i]
            modified_structure[tuple(current_pos)] = {
                'swapped_indices': [idx1, idx2],
                'terms': [str(term) for term in terms]
            }
            
            # 递归处理复合项
            for j, term in enumerate(terms):
                if isinstance(term, (sp.Add, sp.Mul)):
                    new_pos_info = current_pos + [j]
                    new_term, sub_changes = self.swap_terms(
                        term,
                        variables,
                        new_pos_info
                    )
                    if sub_changes:
                        modified_structure.update(sub_changes)
                    terms[j] = new_term
        if isinstance(expr, sp.Add):
            new_expr = sum(terms)
        else: 
            new_expr = terms[0]
            for term in terms[1:]:
                new_expr *= term
        
        return new_expr, modified_structure
        



    def swap_mul_terms(self, expr):
        #交换乘法表达式中的因子顺序
        # 等式
        if isinstance(expr, sp.Eq):
            lhs = expr.lhs
            rhs = expr.rhs
            
            # 只处理左边
            if isinstance(lhs, sp.Mul):
                factors = list(lhs.args)
                if len(factors) >= 2:
                    idx1, idx2 = random.sample(range(len(factors)), 2)
                    factors[idx1], factors[idx2] = factors[idx2], factors[idx1]
                    new_lhs = factors[0]
                    for factor in factors[1:]:
                        new_lhs *= factor
                    return sp.Eq(new_lhs, rhs)  # 返回新的等式对象
            
            # 左边不是乘法表达式，返回原表达式
            return expr
        
        # 非等式
        if isinstance(expr, sp.Mul):
            factors = list(expr.args)
            if len(factors) >= 2:
                idx1, idx2 = random.sample(range(len(factors)), 2)
                factors[idx1], factors[idx2] = factors[idx2], factors[idx1]
                new_expr = factors[0]
                for factor in factors[1:]:
                    new_expr *= factor
                return new_expr
        
        return expr



    def set_allowed_operations(self, allowed_operations):
        self.operations_list = allowed_operations



    def process_and_compare_formula(self, original_formula_str, modified_formula_str=None):
        result = {
            "original_structure": None,
            "modified_structure": None,
            "changes": []
        }
        
        def compare_structures(orig_struct, mod_struct, path=[]):
            changes = []
            
            # 获取所有节点的标签
            def get_labels(struct, curr_path=[]):
                labels = []
                for key, value in struct.items():
                    new_path = curr_path + [key]
                    if isinstance(value, dict):
                        if 'label' in value:
                            labels.append((value['label'], value.get('content', ''), new_path))
                        if 'terms' in value:
                            labels.extend(get_labels(value['terms'], new_path))
                return labels
            
            # 获取两个结构的所有标签
            orig_labels = get_labels(orig_struct)
            mod_labels = get_labels(mod_struct)
            
            # 按层级排序（叶到根）
            orig_labels.sort(key=lambda x: (-int(x[0].split('_')[0][1:]), x[2]))
            mod_labels.sort(key=lambda x: (-int(x[0].split('_')[0][1:]), x[2]))
            
            # 比较标签变化
            for orig_label, orig_content, orig_path in orig_labels:
                for mod_label, mod_content, mod_path in mod_labels:
                    if orig_content == mod_content and orig_label != mod_label:
                        changes.append({
                            'content': orig_content,
                            'original_label': orig_label,
                            'modified_label': mod_label,
                            'path': orig_path
                        })
            
            return changes
            
        # 解析原始公式结构
        original_expr = self.parse_formula(original_formula_str)
        if original_expr is not None:
            result["original_structure"] = self.record_structure(original_expr)
        
        # 解析修改后公式结构
        if modified_formula_str:
            modified_expr = self.parse_formula(modified_formula_str)
            if modified_expr is not None:
                result["modified_structure"] = self.record_structure(modified_expr)
        
        # 计算结构差异
        if result["original_structure"] and result["modified_structure"]:
            result["changes"] = compare_structures(
                result["original_structure"],
                result["modified_structure"]
            )
            
            # 计算编辑距离
            edit_distance = self.compute_edit_distance(
                result["original_structure"],
                result["modified_structure"]
            )
            result["edit_distance"] = edit_distance  # 直接更新复杂度字段
        
        return result



    def record_structure(self, expr):
        #结构记录函数
        structure = {}
        
        def process_term(term, current_dict, index, level=0):
            if isinstance(term, (sp.Add, sp.Mul, sp.sin, sp.cos, sp.tan, sp.cot)):
                current_dict[str(index)] = {
                    'type': term.__class__.__name__,
                    'content': str(term),
                    'label': f"L{level}_{index}",
                    'terms': {}
                }
                if hasattr(term, 'args'):
                    for i, subterm in enumerate(term.args):
                        process_term(subterm, current_dict[str(index)]['terms'], i, level + 1)
            else:
                current_dict[str(index)] = {
                    'type': 'Basic',
                    'content': str(term),
                    'label': f"L{level}_{index}"
                }
            
        if isinstance(expr, (sp.Add, sp.Mul, sp.sin, sp.cos, sp.tan, sp.cot)):
            for i, term in enumerate(expr.args):
                process_term(term, structure, i)
        else:
            process_term(expr, structure, 0)
            
        return structure
    


    def compute_edit_distance(self, struct1, struct2):
        """计算两个结构之间的编辑距离"""
        def get_structure_sequence(struct):
            sequence = []
            def traverse(d):
                if isinstance(d, dict):
                    for key in sorted(d.keys()):  # 确保顺序一致
                        if isinstance(d[key], dict) and 'type' in d[key]:
                            sequence.append(f"{d[key]['type']}_{d[key]['content']}")
                            if 'terms' in d[key]:
                                traverse(d[key]['terms'])
            
            traverse(struct)
            return sequence
        
        # 获取两个结构的序列表示
        seq1 = get_structure_sequence(struct1)
        seq2 = get_structure_sequence(struct2)
        
        return fuzz.ratio(''.join(seq1), ''.join(seq2))



    def execute_functions(self, user_formula, times=None):
        print(f"\n=== 开始执行变换 ===")
        print(f"输入公式: {user_formula}")
        
        # if times is None:
        #     times = random.randint(1, 3)
        
        results = []
        score = 0

        expr, variables = self.parse_user_formula(user_formula)
        if expr is None:
            print(f"无法解析公式: {user_formula}")
            return []
        
        combined_operations = []
        current_expr = expr
        result = {
            "formula": {
                "left": str(expr.lhs) if isinstance(expr, sp.Eq) else str(expr),
                "right": str(expr.rhs) if isinstance(expr, sp.Eq) else str(expr)
            },
            "tricks": [],
            "complexity": {
                # "edit_distance": None,
                "score": 0
            }
        }
        original_struct = self.record_structure(expr)
        # 执行变换操作
        # for _ in range(times):
        for _ in range(1):
            # 第一阶段 - 操作4和8
            pre_transformed = current_expr
            first_phase_ops = [4, 8]
            for _ in range(5):
                operationa = random.choice(first_phase_ops)
              
                if operationa == 4:
                    pre_transformed = self.multiply_with_num(pre_transformed)
                    score += 1
                elif operationa == 8:
                    pre_transformed = self.add_elements(pre_transformed) 
                    score += 1
                combined_operations.append((operationa,pre_transformed))
            # 第二阶段 - 执行6 or 7
            post_transformed = pre_transformed
            second_phase_ops = [6, 7]  
            for _ in range(3):
                operationb = random.choice(second_phase_ops)
                combined_operations.append(operationb)
                if operationb == 6:
                    new_expr = self.swap_mul_terms(post_transformed)
                    if new_expr != post_transformed:
                        post_transformed = new_expr
                        score += 1
                elif operationb == 7:
                    new_expr, success = self.swap_terms(post_transformed, variables)
                    if success:
                        post_transformed = new_expr
                        score += 1
                combined_operations.append((operationb,post_transformed))
            # 第三阶段 
            final_transformed = post_transformed
            if '=' in final_transformed:
                lhs, rhs = final_transformed.split('=')
                lhs_expr = sp.sympify(lhs.strip(), locals=self.local_dict)
                rhs_expr = sp.sympify(rhs.strip(), locals=self.local_dict)
                current_vars = lhs_expr.free_symbols.union(rhs_expr.free_symbols)  # 合并左右变量
                var_count = len(current_vars)
                final_transformed = f"{sp.sstr(lhs_expr)} = {sp.sstr(rhs_expr)}"
            else:
                expr = sp.sympify(final_transformed.strip(), locals=self.local_dict)
                current_vars = expr.free_symbols
                var_count = len(current_vars)
                final_transformed = sp.sstr(expr)

            third_phase_ops = [1, 2]
            weights = [0.05, 0.95] if var_count > 1 else [0.0, 1.0]  # 简化判断

            for _ in range(1):
                operationc = random.choices(third_phase_ops, weights=weights, k=1)[0]
                combined_operations.append(operationc)
                if operationc == 1:
                    final_transformed = self.replace_with_number(final_transformed)
                elif operationc == 2:
                    final_transformed = self.replace_with_variable(final_transformed)
                combined_operations.append((operationc,final_transformed))
            if final_transformed is not None:
                result['tricks'].append({
                    "operation": combined_operations,
                    "formula_after": str(final_transformed)
                })
                # result['complexity']= score
                current_expr = final_transformed
        
        modified_struct = self.record_structure(current_expr)
        edit_distance = self.compute_edit_distance(original_struct, modified_struct)
        result['complexity'] = edit_distance + score

        results.append(result)
        return results
    
    

    def calculate_formula_replace_score(self, orig_formula, formula):
        # 解析 formula
        if isinstance(formula, str) and '=' in formula:
            formula_str = formula.split('=')[1].strip()
        else:
            formula_str = str(formula)
        formula_expr = sp.sympify(formula_str, locals=self.local_dict, evaluate=False)
        
        # 解析 orig_formula
        if isinstance(orig_formula, (list, tuple)):
            orig_formula = orig_formula[0]
        if isinstance(orig_formula, str) and '=' in orig_formula:
            orig_str = orig_formula.split('=')[1].strip()
        else:
            orig_str = str(orig_formula)
        orig_expr = sp.sympify(orig_str, locals=self.local_dict, evaluate=False)
        
        orig_vars = list(orig_expr.free_symbols)
        formula_vars = list(formula_expr.free_symbols)
        overlap_vars = [var for var in orig_vars if var in formula_vars]
        new_vars = [var for var in formula_vars if var not in orig_vars]
        
        # 调整后的得分：重叠变量数 - 新增变量数
        return len(overlap_vars) - len(new_vars)