from .rule_module import FormulaManipulator
from trick_rules import arit_prog
from trick_rules import cubi_sum_diff
from trick_rules import geom_prog
from trick_rules import indu_form
from trick_rules import perf_cube_n_the_form
from trick_rules import prod_n_diff
from trick_rules import squa_diff
from trick_rules import sum_n_diff_of_two_angl
from trick_rules import sum_n_diff_prod
from trick_rules import sum_of_perf_squa_n_diff



def get_generator(name, data):
    if name == "arit_prog":
        generator = arit_prog.arit_prog()
        return generator.run(data)
    elif name == "cubi_sum_diff":
        generator = cubi_sum_diff.cubi_sum_diff()
        return generator.run(data)
    elif name == "geom_prog":
        generator = geom_prog.geom_prog()
        return generator.run(data)
    elif name == "indu_form":
        generator = indu_form.indu_form()
        return generator.run(data)
    elif name == "perf_cube_n_the_form":
        generator = perf_cube_n_the_form.perf_cube_n_the_form()
        return generator.run(data)
    elif name == "prod_n_diff":
        generator = prod_n_diff.prod_n_diff()
        return generator.run(data)
    elif name == "squa_diff":
        generator = squa_diff.squa_diff()
        return generator.run(data)
    elif name == "sum_n_diff_of_two_angl":
        generator = sum_n_diff_of_two_angl.sum_n_diff_of_two_angl()
        return generator.run(data)
    elif name == "sum_n_diff_prod":
        generator = sum_n_diff_prod.sum_n_diff_prod()
        return generator.run(data)
    elif name == "sum_of_perf_squa_n_diff":
        generator = sum_of_perf_squa_n_diff.sum_of_perf_squa_n_diff()
        return generator.run(data)
    else:
        print(f"未知的规则名称: {name}")
        return None