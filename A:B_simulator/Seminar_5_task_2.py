import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy import stats


class Design(BaseModel):
    """Дата-класс с описание параметров эксперимента.

    statistical_test - тип статтеста. ['ttest', 'bootstrap']
    effect - размер эффекта в процентах
    alpha - уровень значимости
    beta - допустимая вероятность ошибки II рода
    bootstrap_iter - количество итераций бутстрепа
    bootstrap_ci_type - способ построения доверительного интервала. ['normal', 'percentile', 'pivotal']
    bootstrap_agg_func - метрика эксперимента. ['mean', 'quantile 95']
    """
    statistical_test: str
    effect: float
    alpha: float = 0.05
    beta: float = 0.1
    bootstrap_iter: int = 1000
    bootstrap_ci_type: str
    bootstrap_agg_func: str


class ExperimentsService:

    def _generate_bootstrap_metrics(self, data_one, data_two, design):
        """Генерирует значения метрики, полученные с помощью бутстрепа.

        :param data_one, data_two (np.array): значения метрик в группах.
        :param design (Design): объект с данными, описывающий параметры эксперимента
        :return bootstrap_metrics, pe_metric:
            bootstrap_metrics (np.array) - значения статистики теста псчитанное по бутстрепным подвыборкам
            pe_metric (float) - значение статистики теста посчитанное по исходным данным
        """
        bootstrap_data_one = np.random.choice(data_one, (len(data_one), design.bootstrap_iter))
        bootstrap_data_two = np.random.choice(data_two, (len(data_two), design.bootstrap_iter))
        if design.bootstrap_agg_func == 'mean':
            bootstrap_metrics = bootstrap_data_two.mean(axis=0) - bootstrap_data_one.mean(axis=0)
            pe_metric = data_two.mean() - data_one.mean()
            return bootstrap_metrics, pe_metric
        elif design.bootstrap_agg_func == 'quantile 95':
            bootstrap_metrics = (
                    np.quantile(bootstrap_data_two, 0.95, axis=0)
                    - np.quantile(bootstrap_data_one, 0.95, axis=0)
            )
            pe_metric = np.quantile(data_two, 0.95) - np.quantile(data_one, 0.95)
            return bootstrap_metrics, pe_metric
        else:
            raise ValueError('Неверное значение design.bootstrap_agg_func')

    def _run_bootstrap(self, bootstrap_metrics, pe_metric, design):
        """Строит доверительный интервал и проверяет значимость отличий с помощью бутстрепа.

        :param bootstrap_metrics (np.array): статистика теста, посчитанная на бутстрепных выборках.
        :param pe_metric (float): значение статистики теста посчитанное по исходным данным.
        :return ci, pvalue:
            ci [float, float] - границы доверительного интервала
            pvalue (float) - 0 если есть статистически значимые отличия, иначе 1.
                Настоящее pvalue для произвольного способа построения доверительного интервала с помощью
                бутстрепа вычислить не тривиально. Поэтому мы будем использовать краевые значения 0 и 1.
        """
        # YOUR_CODE_HERE
        ci_type = design.bootstrap_ci_type
        alpha = design.alpha

        if ci_type == 'normal':
            c = stats.norm.ppf(1 - alpha / 2)
            se = np.std(bootstrap_metrics)
            ci = pe_metric - c * se, pe_metric + c * se
        elif ci_type == 'percentile':
            ci = np.quantile(bootstrap_metrics, [alpha / 2, 1 - alpha / 2])
        elif ci_type == 'pivotal':
            right, left = 2 * pe_metric - np.quantile(bootstrap_metrics, [alpha / 2, 1 - alpha / 2])
            ci = left, right

        pvalue = 1 if ci[0] < 0 or ci[1] > 0 else 0
        return ci, pvalue




    def get_pvalue(self, metrics_a_group, metrics_b_group, design):
        """Применяет статтест, возвращает pvalue.

        :param metrics_a_group (np.array): массив значений метрик группы A
        :param metrics_a_group (np.array): массив значений метрик группы B
        :param design (Design): объект с данными, описывающий параметры эксперимента
        :return (float): значение p-value
        """
        if design.statistical_test == 'ttest':
            _, pvalue = stats.ttest_ind(metrics_a_group, metrics_b_group)
            return pvalue
        elif design.statistical_test == 'bootstrap':
            bootstrap_metrics, pe_metric = self._generate_bootstrap_metrics(metrics_a_group, metrics_b_group, design)
            _, pvalue = self._run_bootstrap(bootstrap_metrics, pe_metric, design)
            return pvalue
        else:
            raise ValueError('Неверный design.statistical_test')


if __name__ == '__main__':
    bootstrap_metrics = np.arange(-490, 510)
    pe_metric = 5.
    design = Design(
        statistical_test='bootstrap',
        effect=5,
        bootstrap_ci_type='normal',
        bootstrap_agg_func='mean'
    )
    ideal_ci = (-560.79258, 570.79258)
    ideal_pvalue = 1.

    experiments_service = ExperimentsService()
    ci, pvalue = experiments_service._run_bootstrap(bootstrap_metrics, pe_metric, design)
    np.testing.assert_almost_equal(ideal_ci, ci, decimal=4, err_msg='Неверный доверительный интервал')
    assert ideal_pvalue == pvalue, 'Неверный pvalue'
    print('simple test passed')
