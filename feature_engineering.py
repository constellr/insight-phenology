import pandas as pd
from scipy.stats import skew, kurtosis

def feature_engineering(
        gid,
        gdd_timeseries,
        gdd_features,
        ndvi_features,
        ndvi_timeseries,
        growth_rate,
        sos_date,
        sos_value,
        pos_date,
        pos_value,
        eos_date,
        eos_value,
        inflection_points,
        acceleration_points
    ):

    gdd_features['id'] = gid
    gdd_timeseries['id'] = gid
    ndvi_features['id'] = gid

    ndvi_features["growth_rate"] = growth_rate
    ndvi_features["SOS_date"] = sos_date
    ndvi_features["POS_date"] = pos_date
    ndvi_features["EOS_date"] = eos_date
    ndvi_features["SOS_value"] = sos_value
    ndvi_features["POS_value"] = pos_value
    ndvi_features["EOS_value"] = eos_value

    ndvi_features['first_inflection_date'] = inflection_points['date'].head(1).values[0]
    ndvi_features['first_inflection_value'] = inflection_points['filter'].head(1).values[0]
    ndvi_features['last_inflection_date'] = inflection_points['date'].tail(1).values[0]
    ndvi_features['last_inflection_value'] = inflection_points['filter'].tail(1).values[0]

    ndvi_features['first_acceleration_date'] = acceleration_points['date'].head(1).values[0]
    ndvi_features['first_acceleration_value'] = acceleration_points['filter'].head(1).values[0]
    ndvi_features['last_acceleration_date'] = acceleration_points['date'].tail(1).values[0]
    ndvi_features['last_acceleration_value'] = acceleration_points['filter'].tail(1).values[0]

    ndvi_timeseries['mean_NDVI'] = ndvi_timeseries['mean']
    ndvi_timeseries['interpol_NDVI'] = ndvi_timeseries['interpol']
    ndvi_timeseries['filter_NDVI'] = ndvi_timeseries['filter']
    ndvi_timeseries = ndvi_timeseries.drop(columns=['mean', 'interpol', 'filter'])

    ard_timeseries = pd.merge(ndvi_timeseries, gdd_timeseries, on=['id', 'date'])
    ard_features = pd.merge(ndvi_features, gdd_features, on='id')

    return ard_timeseries, ard_features

def summary_stats(
        gid,
        ndvi_timeseries,
        lst_timeseries,
        sos_date,
        eos_date
    ):

    ndvi_timeseries = ndvi_timeseries[(ndvi_timeseries['date'] >= sos_date) & (ndvi_timeseries['date'] <= eos_date)]
    lst_timeseries = lst_timeseries[(lst_timeseries['date'] >= sos_date) & (lst_timeseries['date'] <= eos_date)]

    ndvi_timeseries['id'] = gid
    lst_timeseries['id'] = gid

    ndvi_timeseries['NDVI'] = ndvi_timeseries['filter']
    lst_timeseries['LST'] = lst_timeseries['mean']

    ard = pd.merge(ndvi_timeseries, lst_timeseries, on='id')

    ard = ard.groupby('id').agg(
        sum_ndvi=('NDVI', 'sum'),
        std_ndvi=('NDVI', 'std'),
        mean_ndvi=('NDVI', 'mean'),
        max_ndvi=('NDVI', 'max'),
        min_ndvi=('NDVI', 'min'),
        skew_ndvi=('NDVI', lambda x: skew(x, nan_policy='omit')),
        kurt_ndvi=('NDVI', lambda x: kurtosis(x, nan_policy='omit')),
        sum_lst=('LST', 'sum'),
        std_lst=('LST', 'std'),
        mean_lst=('LST', 'mean'),
        max_lst=('LST', 'max'),
        min_lst=('LST', 'min'),
        skew_lst=('LST', lambda x: skew(x, nan_policy='omit')),
        kurt_lst=('LST', lambda x: kurtosis(x, nan_policy='omit'))
    ).reset_index()

    return ard

def get_ndvi_stages(
        df,
        sos_date,
        pos_date,
        eos_date,
        inflection_points,
        acceleration_points
    ):

    first_inflection = inflection_points['date'].head(1).values[0]
    last_inflection = inflection_points['date'].tail(1).values[0]
    first_acceleration = acceleration_points['date'].head(1).values[0]
    last_acceleration = acceleration_points['date'].tail(1).values[0]

    df['NDVI'] = df['interpol']
    df = df.drop(columns=['mean', 'interpol', 'filter'])

    calc_1 = df.loc[(df['date'] >= sos_date) & (df['date'] <= first_acceleration)]
    calc_2 = df.loc[(df['date'] >= sos_date) & (df['date'] <= pos_date)]
    calc_3 = df.loc[(df['date'] >= sos_date) & (df['date'] <= last_inflection)]
    calc_4 = df.loc[(df['date'] >= sos_date) & (df['date'] <= eos_date)]

    ard_1 = calc_1.groupby('id').agg(
        sum_ndvi_germination=('NDVI', 'sum'),
        std_ndvi_germination=('NDVI', 'std'),
        mean_ndvi_germination=('NDVI', 'mean'),
        max_ndvi_germination=('NDVI', 'max'),
        min_ndvi_germination=('NDVI', 'min')
    ).reset_index()

    ard_2 = calc_2.groupby('id').agg(
        sum_ndvi_tillering=('NDVI', 'sum'),
        std_ndvi_tillering=('NDVI', 'std'),
        mean_ndvi_tillering=('NDVI', 'mean'),
        max_ndvi_tillering=('NDVI', 'max'),
        min_ndvi_tillering=('NDVI', 'min')
    ).reset_index()

    ard_3 = calc_3.groupby('id').agg(
        sum_ndvi_grand=('NDVI', 'sum'),
        std_ndvi_grand=('NDVI', 'std'),
        mean_ndvi_grand=('NDVI', 'mean'),
        max_ndvi_grand=('NDVI', 'max'),
        min_ndvi_grand=('NDVI', 'min')
    ).reset_index()

    ard_4 = calc_4.groupby('id').agg(
        sum_ndvi_maturity=('NDVI', 'sum'),
        std_ndvi_maturity=('NDVI', 'std'),
        mean_ndvi_maturity=('NDVI', 'mean'),
        max_ndvi_maturity=('NDVI', 'max'),
        min_ndvi_maturity=('NDVI', 'min')
    ).reset_index()

    ard_ndvi = ard_1.merge(ard_2, on='id', how='outer') \
                    .merge(ard_3, on='id', how='outer') \
                    .merge(ard_4, on='id', how='outer')

    return ard_ndvi

def get_timeseries_stats(
        gid,
        lst_timeseries,
        ndvi_timeseries,
    ):

    ndvi_timeseries['id'] = gid
    lst_timeseries['id'] = gid

    ndvi = pd.DataFrame()
    lst = pd.DataFrame()

    ndvi['id'] = ndvi_timeseries['id']
    ndvi['NDVI_date'] = ndvi_timeseries['date']
    ndvi['NDVI_mean'] = ndvi_timeseries['mean_NDVI']
    ndvi['NDVI_min'] = ndvi_timeseries['min']
    ndvi['NDVI_max'] = ndvi_timeseries['max']

    lst['id'] = lst_timeseries['id']
    lst['LST_date'] = lst_timeseries['date']
    lst['LST_mean'] = lst_timeseries['mean']
    lst['LST_min'] = lst_timeseries['min']
    lst['LST_max'] = lst_timeseries['max']

    #ard_timeseries = pd.merge(ndvi, lst, on=['id', 'date'])
    ard_timeseries = pd.merge(ndvi, lst, on=['id'])

    return ard_timeseries

def get_sequential_features(df, resampling):

    resampled_df = df

    if resampling == "weekly":
        df.set_index('LST_date', inplace=True)
        resampled_df = df.groupby('id').resample('W').mean()
        resampled_df = resampled_df.drop(columns='id')
        resampled_df = resampled_df.reset_index()
        resampled_df['month_year'] = resampled_df['LST_date'].dt.strftime('%B-%Y')

    if resampling == "monthly":
        df.set_index('LST_date', inplace=True)
        resampled_df = df.groupby('id').resample('MS').mean()
        resampled_df = resampled_df.drop(columns='id')
        resampled_df = resampled_df.reset_index()
        resampled_df['month_year'] = resampled_df['LST_date'].dt.strftime('%B-%Y')

    pivot_lst = resampled_df.pivot_table(index='id', columns='LST_date', values='LST_max').reset_index()
    pivot_ndvi = resampled_df.pivot_table(index='id', columns='NDVI_date', values='NDVI_max').reset_index()

    pivot_lst.columns = ['id'] + [f'LST_{col}' for col in pivot_lst.columns if col != 'id']
    pivot_ndvi.columns = ['id'] + [f'NDVI_{col}' for col in pivot_ndvi.columns if col != 'id']

    ard = pd.merge(pivot_lst, pivot_ndvi, on=['id'])

    return ard
