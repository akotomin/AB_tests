import pandas as pd
from pydantic import BaseModel
import numpy as np


class Design(BaseModel):
    """Дата-класс с описание параметров эксперимента.

    statistical_test - тип статтеста. ['ttest', 'bootstrap']
    effect - размер эффекта в процентах
    alpha - уровень значимости
    beta - допустимая вероятность ошибки II рода
    bootstrap_iter - количество итераций бутстрепа
    bootstrap_ci_type - способ построения доверительного интервала. ['normal', 'percentile', 'pivotal']
    bootstrap_agg_func - метрика эксперимента. ['mean', 'quantile 95']
    metric_name - название целевой метрики эксперимента
    metric_outlier_lower_bound - нижняя допустимая граница метрики, всё что ниже считаем выбросами
    metric_outlier_upper_bound - верхняя допустимая граница метрики, всё что выше считаем выбросами
    metric_outlier_process_type - способ обработки выбросов. ['drop', 'clip'].
        'drop' - удаляем измерение, 'clip' - заменяем выброс на значение ближайшей границы (lower_bound, upper_bound).
    """
    statistical_test: str = 'ttest'
    effect: float = 3.
    alpha: float = 0.05
    beta: float = 0.1
    bootstrap_iter: int = 1000
    bootstrap_ci_type: str = 'normal'
    bootstrap_agg_func: str = 'mean'
    metric_name: str
    metric_outlier_lower_bound: float
    metric_outlier_upper_bound: float
    metric_outlier_process_type: str


class MetricsService:

    def process_outliers(self, metrics, design):
        """Возвращает новый датафрейм с обработанными выбросами в измерениях метрики.

        :param metrics (pd.DataFrame): таблица со значениями метрики, columns=['user_id', 'metric'].
        :param design (Design): объект с данными, описывающий параметры эксперимента.
        :return df: columns=['user_id', 'metric']
        """
        # YOUR_CODE_HERE
        lower_outlier = design.metric_outlier_lower_bound
        upper_outlier = design.metric_outlier_upper_bound
        method = design.metric_outlier_process_type

        if method == 'drop':
            metrics = metrics[
                (metrics['metric'] >= lower_outlier)
                & (metrics['metric'] <= upper_outlier)
            ]
        elif method == 'clip':
            metrics['metric'] = metrics['metric'].mask(
                metrics['metric'] <= lower_outlier
                , lower_outlier)
            metrics['metric'] = metrics['metric'].mask(
                metrics['metric'] >= upper_outlier
                , upper_outlier)

        return metrics


def _chech_df(df, df_ideal, sort_by, reindex=False, set_dtypes=False):
    assert isinstance(df, pd.DataFrame), 'Функция вернула не pd.DataFrame.'
    assert len(df) == len(df_ideal), 'Неверное количество строк.'
    assert len(df.T) == len(df_ideal.T), 'Неверное количество столбцов.'
    columns = df_ideal.columns
    assert df.columns.isin(columns).sum() == len(df.columns), 'Неверное название столбцов.'
    df = df[columns].sort_values(sort_by)
    df_ideal = df_ideal.sort_values(sort_by)
    if reindex:
        df_ideal.index = range(len(df_ideal))
        df.index = range(len(df))
    if set_dtypes:
        for column, dtype in df_ideal.dtypes.to_dict().items():
            df[column] = df[column].astype(dtype)
    assert df_ideal.equals(df), 'Итоговый датафрейм не совпадает с верным результатом.'


if __name__ == '__main__':
    metrics = pd.DataFrame({
        'user_id': ['1', '2', '3'],
        'metric': [1., 2, 3]
    })
    design = Design(
        metric_name='response_time',
        metric_outlier_lower_bound=0.1,
        metric_outlier_upper_bound=2.2,
        metric_outlier_process_type='drop',
    )
    ideal_processed_metrics = pd.DataFrame({
        'user_id': ['1', '2'],
        'metric': [1., 2]
    })

    metrics_service = MetricsService()
    processed_metrics = metrics_service.process_outliers(metrics, design)
    _chech_df(processed_metrics, ideal_processed_metrics, ['user_id', 'metric'], True, True)
    print('simple test passed')