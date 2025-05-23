import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class DataService:

    def __init__(self, table_name_2_table):
        self.table_name_2_table = table_name_2_table

    def get_data_subset(self, table_name, begin_date, end_date, user_ids=None, columns=None):
        df = self.table_name_2_table[table_name]
        if begin_date:
            df = df[df['date'] >= begin_date]
        if end_date:
            df = df[df['date'] < end_date]
        if user_ids:
            df = df[df['user_id'].isin(user_ids)]
        if columns:
            df = df[columns]
        return df.copy()


class MetricsService:

    def __init__(self, data_service):
        """Класс для вычисления метрик.

        :param data_service (DataService): объект класса, предоставляющий доступ с данным.
        """
        self.data_service = data_service

    def _get_data_subset(self, table_name, begin_date, end_date, user_ids=None, columns=None):
        """Возвращает часть таблицы с данными."""
        return self.data_service.get_data_subset(table_name, begin_date, end_date, user_ids, columns)

    def _calculate_revenue_web(self, begin_date, end_date, user_ids):
        """Вычисляет метрику суммарная выручка с пользователя за указанный период
        для заходивших на сайт в указанный период.

        Эта метрика нужна для экспериментов на сайте, когда в эксперимент попадают только те, кто заходил на сайт.
        
        Нужно вернуть значения user_id и суммарной выручки (sum(price)).
        Данный о ценах в таблице 'sales'. Данные о заходивших на сайт в таблице 'web-logs'.
        Если пользователь зашёл на сайт и ничего не купил, его суммарная стоимость покупок равна нулю.
        Для каждого user_id должно быть ровно одно значение.

        :param begin_date, end_date (datetime): период времени, за который нужно считать метрику.
            Также за этот период времени нужно выбирать пользователей, которые заходили на сайт.
        :param user_id (None, list[str]): id пользователей, по которым нужно отфильтровать полученные значения.
        
        :return (pd.DataFrame): датафрейм с двумя столбцами ['user_id', 'metric']
        """
        user_ids_ = (
            self._get_data_subset('web-logs', begin_date, end_date, user_ids, ['user_id'])
            ['user_id'].unique()
        )
        df = (
            self._get_data_subset('sales', begin_date, end_date, user_ids, ['user_id', 'price'])
            .groupby('user_id')[['price']].sum().reset_index() 
            .rename(columns={'price': 'metric'})
        )
        df = pd.merge(pd.DataFrame({'user_id': user_ids_}), df, on='user_id', how='left').fillna(0)
        return df[['user_id', 'metric']]

    @staticmethod
    def _calculate_theta(y, x):
        """Вычисляем Theta по данным двух групп.

        y - значения метрики во время пилота
        x - ковариата до пилота
        """
        covariance = np.cov(x, y)[0, 1]
        variance = np.var(x)
        theta = covariance / variance
        return theta

    def calculate_metric(self, metric_name, begin_date, end_date, cuped, user_ids=None):
        """Считает значения метрики.

        :param metric_name (str): название метрики
        :param begin_date (datetime): дата начала периода (включая границу)
        :param end_date (datetime): дата окончания периода (не включая границу)
        :param cuped (str): применение CUPED. ['off', 'on (previous week revenue)']
            'off' - не применять CUPED
            'on (previous week revenue)' - применяем CUPED, в качестве ковариаты
                используем выручку за прошлые 7 дней
        :param user_ids (list[str], None): список пользователей.
            Если None, то вычисляет метрику для всех пользователей.
        :return df: columns=['user_id', 'metric']
        """
        if metric_name == 'revenue (web)':
            if cuped == 'off':
                return self._calculate_revenue_web(begin_date, end_date, user_ids)
            elif cuped == 'on (previous week revenue)':
                # YOUR_CODE_HERE
                exp_df = self._calculate_revenue_web(begin_date, end_date, user_ids)
                covariate_date = begin_date - timedelta(days=7)
                covariate_df = self._calculate_revenue_web(
                    covariate_date, begin_date, user_ids
                ).rename(columns={"metric": "cov_7_days"})
                df = exp_df.merge(covariate_df, how='left', on='user_id').fillna(0)

                theta = self._calculate_theta(df.metric, df.cov_7_days)
                df['metric'] = df['metric'] - theta * (df['cov_7_days'] - df.cov_7_days.mean())

                return df[['user_id', 'metric']]

            else:

                raise ValueError('Wrong cuped')
        else:
            raise ValueError('Wrong metric name')


def _chech_df(df, df_ideal, sort_by, reindex=False, set_dtypes=False, decimal=None):
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
    if decimal:
        ideal_values = df_ideal.astype(float).values
        values = df.astype(float).values
        np.testing.assert_almost_equal(ideal_values, values, decimal=decimal)
    else:
        assert df_ideal.equals(df), 'Итоговый датафрейм не совпадает с верным результатом.'


if __name__ == '__main__':
    df_sales = pd.DataFrame({
        'sale_id': [1, 2, 3, 4, 5],
        'date': [datetime(2022, 3, day, 11) for day in range(10, 15)],
        'price': [1100, 1500, 2000, 2500, 3000],
        'user_id': ['1', '2', '1', '2', '3'],
    })
    df_web_logs = pd.DataFrame({
        'date': [datetime(2022, 3, day, 11) for day in range(10, 15)],
        'user_id': ['1', '2', '1', '2', '3'],
    })
    begin_date = datetime(2022, 3, 12, 0)
    end_date = datetime(2022, 3, 19, 0)

    ideal_metrics = pd.DataFrame({
        'user_id': ['1', '2', '3'],
        'metric': [2159.5303, 2933.0110, 2407.45856],
    })

    data_service = DataService({'sales': df_sales, 'web-logs': df_web_logs})
    metrics_service = MetricsService(data_service)
    metrics = metrics_service.calculate_metric(
        'revenue (web)', begin_date, end_date, 'on (previous week revenue)'
    )

    _chech_df(metrics, ideal_metrics, ['user_id', 'metric'], True, True, decimal=1)
    print('simple test passed')
