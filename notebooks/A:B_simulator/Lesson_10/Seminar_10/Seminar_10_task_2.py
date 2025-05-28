import numpy as np
from scipy.stats import ttest_ind

all_clients = 10000
alpha = 0.05
beta = 0.1
mde = 0.03
mu = 100
sigma = 10

def method_holm(pvalues, alpha=0.05):
    """Применяет метод Холма для проверки значимости изменений.

    pvalues - List[float] - список pvalue.
    alpha - float, уровень значимости.
    return - np.array, массив из нулей и единиц, 0 - эффекта нет, 1 - эффект есть.
    """
    m = len(pvalues)
    array_alpha = np.arange(m, 0, -1)
    array_alpha = alpha / array_alpha
    sorted_pvalue_indexes = np.argsort(pvalues)
    res = np.zeros(m)
    for idx, pvalue_index in enumerate(sorted_pvalue_indexes):
        pvalue = pvalues[pvalue_index]
        alpha_ = array_alpha[idx]
        if pvalue < alpha_:
            res[pvalue_index] = 1
        else:
            break
    res = res.astype(int)
    return res

# Начнем сразу с 2х экспериментов
exp_cnt = 2
test_power = float('inf')

while True:
    group_size = all_clients // exp_cnt // 2
    errors_ab = []

    for _ in range(1000):
        ab_exps = [
            np.random.normal(mu, sigma, (2, group_size))
            for _ in range(exp_cnt)
        ]
        ab_exps[0][1] *= 1 + mde
        p_values = [ttest_ind(a, b).pvalue for a, b in ab_exps]
        holm_effect = method_holm(p_values, alpha)
        if np.sum(holm_effect) == 0:
            # если эффектов не найдено, то это ошибка 2 рода
            errors_ab.append(True)
        else:
            # если эффект найден где его нет, то это ошибка
            errors_ab.append(np.min(p_values) != p_values[0])

    second_type_error = np.mean(errors_ab)

    if second_type_error > beta:
        exp_cnt -= 1
        break
    exp_cnt += 1

print(f"Ошибка второго рода контролируется на уровне {beta} при {exp_cnt} количестве экспериментов")