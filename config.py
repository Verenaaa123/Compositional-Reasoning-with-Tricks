import sympy as sp

# 三角函数符号
alpha, beta = sp.symbols('α β')
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

        f"sin(2*{k}*{pi} + {alpha}) = sin({alpha})": "indu_form",
        f"sin(-{alpha}) = -sin({alpha})": "indu_form",
        f"sin(2*{pi} - {alpha}) = -sin({alpha})": "indu_form",
        f"sin({pi}/2 + {alpha}) = cos({alpha})": "indu_form",
        f"cos(2*{k}*pi + {alpha}) = cos({alpha})": "indu_form",
        f"cos(-{alpha}) = cos({alpha})": "indu_form",
        f"cos(2*{pi} - {alpha}) = cos({alpha})": "indu_form",
        f"sin({pi}/2 - {alpha}) = cos({alpha})": "indu_form",
        f"tan(2*{k}*{pi} + {alpha}) = tan({alpha})": "indu_form",
        f"tan(-{alpha}) = -tan({alpha})": "indu_form",
        f"tan(2*{pi} - {alpha}) = -tan({alpha})": "indu_form",
        f"cos({pi}/2 + {alpha}) = -sin({alpha})": "indu_form",
        f"cot(2*{k}*{pi} + {alpha}) = cot({alpha})": "indu_form",
        f"cot(-{alpha}) = -cot({alpha})": "indu_form",
        f"cot(2*{pi} - {alpha}) = -cot({alpha})": "indu_form",
        f"cos({pi}/2 - {alpha}) = sin({alpha})": "indu_form",
        f"sin({pi} + {alpha}) = -sin({alpha})": "indu_form",
        f"sin({pi} - {alpha}) = sin({alpha})": "indu_form",
        f"cos({pi} + {alpha}) = -cos({alpha})": "indu_form",
        f"cos({pi} - {alpha}) = -cos({alpha})": "indu_form",
        f"tan({pi} + {alpha}) = tan({alpha})": "indu_form",
        f"tan({pi} - {alpha}) = -tan({alpha})": "indu_form",
        f"cot({pi} + {alpha}) = cot({alpha})": "indu_form",
        f"cot({pi} - {alpha}) = -cot({alpha})": "indu_form",
        f"cot({pi}/2 + {alpha}) = -tan({alpha})": "indu_form",
        f"cot({pi}/2 - {alpha}) = cot({alpha})": "indu_form",
        f"tan({pi}/2 + {alpha}) = -cot({alpha})": "indu_form",
        f"tan({pi}/2 - {alpha}) = cot({alpha})": "indu_form",

        f"cos({alpha} + {beta}) = cos({alpha}) * cos({beta}) - sin({alpha}) * sin({beta})": "sum_n_diff_of_two_angl",
        f"cos({alpha} - {beta}) = cos({alpha}) * cos({beta}) + sin({alpha}) * sin({beta})": "sum_n_diff_of_two_angl",
        f"sin({alpha} + {beta}) = sin({alpha}) * cos({beta}) + cos({alpha}) * sin({beta})": "sum_n_diff_of_two_angl",
        f"sin({alpha} - {beta}) = sin({alpha}) * cos({beta}) - cos({alpha}) * sin({beta})": "sum_n_diff_of_two_angl",
        
        f"sin({alpha}) * cos({beta}) = (sin({alpha} + {beta}) + sin({alpha} - {beta})) / 2": "prod_n_diff",
        f"cos({alpha}) * sin({beta}) = (sin({alpha} + {beta}) - sin({alpha} - {beta})) / 2": "prod_n_diff",
        f"cos({alpha}) * cos({beta}) = (cos({alpha} + {beta}) + cos({alpha} - {beta})) / 2": "prod_n_diff",
        f"sin({alpha}) * sin({beta}) = -(cos({alpha} + {beta}) - cos({alpha} - {beta})) / 2": "prod_n_diff",
        
        f"sin({alpha}) + sin({beta}) = 2 * sin(({alpha} + {beta}) / 2) * cos(({alpha} - {beta}) / 2)": "sum_n_diff_prod",
        f"sin({alpha}) - sin({beta}) = 2 * cos(({alpha} + {beta}) / 2) * sin(({alpha} - {beta}) / 2)": "sum_n_diff_prod",
        f"cos({alpha}) + cos({beta}) = 2 * cos(({alpha} + {beta}) / 2) * cos(({alpha} - {beta}) / 2)": "sum_n_diff_prod",
        f"cos({alpha}) - cos({beta}) = -2 * sin(({alpha} + {beta}) / 2) * sin(({alpha} - {beta}) / 2)": "sum_n_diff_prod",
        
        # f"{a}-({a}**(-1)+({b}**(-1)-{a})**(-1))**(-1) = {a}*{b}*{a}": "hua_equ",
        # f"{a} = ({b}**(-1)-({a}-1)**(-1)*{b}**(-1)*({a}-1))({a}**(-1)*{b}**(-1)*({a}-1))*(-1)": "hua_equ_2"
}