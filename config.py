import sympy as sp

# 三角函数符号
α, β = sp.symbols('α β')
# 基础代数符号
a, b, n, pi, k = sp.symbols('a b n pi k')
# 数列相关符号
S_n, a_1, q, d = sp.symbols('S_n a_1 q d')

# 所有技巧公式
all_tricks = {
    # 完全平方公式
        f"({a}+{b})*({a}-{b})={a}**2-{b}**2": "squa_diff",
        f"({a}+{b})**2={a}**2+2*{a}*{b}+{b}**2": "sum_of_perf_squa_n_diff",
        f"({a}-{b})**2={a}**2-2*{a}*{b}+{b}**2": "sum_of_perf_squa_n_diff",
        
        # 立方公式
        f"({a}+{b})**3={a}**3+3*{a}**2*{b}+3*{a}*{b}**2+{b}**3": "perf_cube_n_the_form",
        f"({a}-{b})**3={a}**3-3*{a}**2*{b}+3*{a}*{b}**2-{b}**3": "perf_cube_n_the_form",
        f"{a}**3+{b}**3=({a}+{b})*({a}**2-{a}*{b}+{b}**2)": "cubi_sum_diff",
        f"{a}**3-{b}**3=({a}-{b})*({a}**2+{a}*{b}+{b}**2)": "cubi_sum_diff",
        
        # f"{S_n} = {n} * {a_1} + ({n} * ({n} - 1) * {d}) / 2":"arit_prog",
        # f"({a_1}*(1 - {q}**{n}))/(1 - {q})": "geom_prog",

        f"sin(2*{k}*{pi} + {α}) = sin({α})": "indu_form",
        f"sin(-{α}) = -sin({α})": "indu_form",
        f"sin(2*{pi} - {α}) = -sin({α})": "indu_form",
        f"sin({pi}/2 + {α}) = cos({α})": "indu_form",
        f"cos(2*{k}*pi + {α}) = cos({α})": "indu_form",
        f"cos(-{α}) = cos({α})": "indu_form",
        f"cos(2*{pi} - {α}) = cos({α})": "indu_form",
        f"sin({pi}/2 - {α}) = cos({α})": "indu_form",
        f"tan(2*{k}*{pi} + {α}) = tan({α})": "indu_form",
        f"tan(-{α}) = -tan({α})": "indu_form",
        f"tan(2*{pi} - {α}) = -tan({α})": "indu_form",
        f"cos({pi}/2 + {α}) = -sin({α})": "indu_form",
        f"cot(2*{k}*{pi} + {α}) = cot({α})": "indu_form",
        f"cot(-{α}) = -cot({α})": "indu_form",
        f"cot(2*{pi} - {α}) = -cot({α})": "indu_form",
        f"cos({pi}/2 - {α}) = sin({α})": "indu_form",
        f"sin({pi} + {α}) = -sin({α})": "indu_form",
        f"sin({pi} - {α}) = sin({α})": "indu_form",
        f"cos({pi} + {α}) = -cos({α})": "indu_form",
        f"cos({pi} - {α}) = -cos({α})": "indu_form",
        f"tan({pi} + {α}) = tan({α})": "indu_form",
        f"tan({pi} - {α}) = -tan({α})": "indu_form",
        f"cot({pi} + {α}) = cot({α})": "indu_form",
        f"cot({pi} - {α}) = -cot({α})": "indu_form",
        f"cot({pi}/2 + {α}) = -tan({α})": "indu_form",
        f"cot({pi}/2 - {α}) = cot({α})": "indu_form",
        f"tan({pi}/2 + {α}) = -cot({α})": "indu_form",
        f"tan({pi}/2 - {α}) = cot({α})": "indu_form",

        f"cos({α} + {β}) = cos({α}) * cos({β}) - sin({α}) * sin({β})": "sum_n_diff_of_two_angl",
        f"cos({α} - {β}) = cos({α}) * cos({β}) + sin({α}) * sin({β})": "sum_n_diff_of_two_angl",
        f"sin({α} + {β}) = sin({α}) * cos({β}) + cos({α}) * sin({β})": "sum_n_diff_of_two_angl",
        f"sin({α} - {β}) = sin({α}) * cos({β}) - cos({α}) * sin({β})": "sum_n_diff_of_two_angl",
        
        f"sin({α}) * cos({β}) = (sin({α} + {β}) + sin({α} - {β})) / 2": "prod_n_diff",
        f"cos({α}) * sin({β}) = (sin({α} + {β}) - sin({α} - {β})) / 2": "prod_n_diff",
        f"cos({α}) * cos({β}) = (cos({α} + {β}) + cos({α} - {β})) / 2": "prod_n_diff",
        f"sin({α}) * sin({β}) = -(cos({α} + {β}) - cos({α} - {β})) / 2": "prod_n_diff",
        
        f"sin({α}) + sin({β}) = 2 * sin(({α} + {β}) / 2) * cos(({α} - {β}) / 2)": "sum_n_diff_prod",
        f"sin({α}) - sin({β}) = 2 * cos(({α} + {β}) / 2) * sin(({α} - {β}) / 2)": "sum_n_diff_prod",
        f"cos({α}) + cos({β}) = 2 * cos(({α} + {β}) / 2) * cos(({α} - {β}) / 2)": "sum_n_diff_prod",
        f"cos({α}) - cos({β}) = -2 * sin(({α} + {β}) / 2) * sin(({α} - {β}) / 2)": "sum_n_diff_prod",
        
        # f"{a}-({a}**(-1)+({b}**(-1)-{a})**(-1))**(-1) = {a}*{b}*{a}": "hua_equ",
        # f"{a} = ({b}**(-1)-({a}-1)**(-1)*{b}**(-1)*({a}-1))({a}**(-1)*{b}**(-1)*({a}-1))*(-1)": "hua_equ_2"
}