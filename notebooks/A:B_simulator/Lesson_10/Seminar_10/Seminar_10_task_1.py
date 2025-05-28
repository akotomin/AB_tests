import numpy as np
from scipy.stats import ttest_ind, norm

all_clients = 10000
alpha = 0.05
beta = 0.1
mde = 0.03
mu = 100
sigma = 10

def estimate_sample_size(effect, std, alpha, beta):
    """Оценка необходимого размер групп."""
    t_alpha = norm.ppf(1 - alpha / 2, loc=0, scale=1)
    t_beta = norm.ppf(1 - beta, loc=0, scale=1)
    var = 2 * std ** 2
    sample_size = int((t_alpha + t_beta) ** 2 * var / (effect ** 2))
    return sample_size


# оценим необходимый размер групп
sample_size = estimate_sample_size(mde * 100, 10, alpha, beta)
# вычислим количество экспериментов
exp_cnt = all_clients / (sample_size * 2)
print(f'Количество экспериментов равно = {exp_cnt:0.1f}')

exp_cnt = int(exp_cnt)

test_power = float('inf')

while test_power:
    p_values = []
    group_size = all_clients // exp_cnt // 2
    bonf_alpha = alpha / exp_cnt

    for _ in range(1000):
        a = np.random.normal(mu, sigma, group_size)
        b = np.random.normal(mu, sigma, group_size) * (1 + mde)
        p_values.append(ttest_ind(a, b).pvalue < bonf_alpha)

    test_power = sum(p_values) / len(p_values)
    if test_power < 1 - beta:
        break
    exp_cnt += 1

print(f"Ошибка второго рода контролируется на уровне {beta} при {exp_cnt} количестве экспериментов")