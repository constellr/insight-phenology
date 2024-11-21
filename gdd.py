import pandas as pd
from phenology import smoothing
import numpy as np

def get_gdd_db(country, crop, variety):

    gdd_db = pd.read_csv("gdd/gdd_sugarcane.csv", delimiter=';')
    gdd_db = gdd_db[(gdd_db['country'] == country) & (gdd_db['crop'] == crop) & (gdd_db['variety'] == variety)]

    Tmax = gdd_db['Tmax'].values[0]
    Tbase = gdd_db['Tbase'].values[0]

    return gdd_db, Tmax, Tbase

def get_gdd(
        lst,
        sos_date,
        pos_date,
        eos_date,
        inflection_points,
        acceleration_points,
        country, crop, variety
    ):

    gdd_db, Tmax, Tbase = get_gdd_db(country, crop, variety)
    lst_df = lst.copy(deep=True)

    if len(lst_df) > 0:

        lst_df['mean'] = lst_df['mean'] - 270
        lst_df['mean'] = lst_df['mean'].clip(upper=Tmax)
        lst_df['mean'] = lst_df['mean'].clip(lower=Tbase)
        lst_df['mean'] = (lst_df['mean'] - Tbase).clip(lower=0)

        lst_daily = smoothing(lst_df)

        first_inflection = inflection_points['date'].head(1).values[0]
        last_inflection = inflection_points['date'].tail(1).values[0]
        first_acceleration = acceleration_points['date'].head(1).values[0]
        last_acceleration = acceleration_points['date'].tail(1).values[0]

        gdd = pd.DataFrame()
        gdd.at['fid'] = 0

        calc = lst_daily.loc[(lst_daily['date'] >= sos_date) & (lst_daily['date'] <= first_acceleration)]
        gdd['germination'] = calc['interpol'].sum()

        calc = lst_daily.loc[(lst_daily['date'] >= sos_date) & (lst_daily['date'] <= pos_date)]
        gdd['tillering'] = calc['interpol'].sum()

        calc = lst_daily.loc[(lst_daily['date'] >= sos_date) & (lst_daily['date'] <= last_inflection)]
        gdd['grand-growth'] = calc['interpol'].sum()

        calc = lst_daily.loc[(lst_daily['date'] >= sos_date) & (lst_daily['date'] <= eos_date)]
        gdd['maturity'] = calc['interpol'].sum()

        return gdd

def vegetation_stats(
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

def get_gdd_corridors(
        lst,
        sos_date,
        eos_date,
        country, crop, variety
    ):

    gdd_db, Tmax, Tbase = get_gdd_db(country, crop, variety)
    lst_df = lst.copy(deep=True)

    if len(lst_df) > 0:

        lst_daily = smoothing(lst_df)

        gdd = lst_daily.loc[(lst_daily['date'] >= sos_date) & (lst_daily['date'] <= eos_date)]
        gdd['GDD'] = gdd['interpol'].cumsum()

        stage_1 = gdd_db[gdd_db['stage'] == 'Germination']
        stage_2 = gdd_db[gdd_db['stage'] == 'Tillering']
        stage_3 = gdd_db[gdd_db['stage'] == 'Grand Growth Phase']
        stage_4 = gdd_db[gdd_db['stage'] == 'Maturity']

        stage_1_min = int(str(stage_1.GDD.values[0]).split("-")[0])
        stage_1_max = int(str(stage_1.GDD.values[0]).split("-")[1])
        stage_2_min = int(str(stage_2.GDD.values[0]).split("-")[0])
        stage_2_max = int(str(stage_2.GDD.values[0]).split("-")[1])
        stage_3_min = int(str(stage_3.GDD.values[0]).split("-")[0])
        stage_3_max = int(str(stage_3.GDD.values[0]).split("-")[1])
        stage_4_min = int(str(stage_4.GDD.values[0]).split("-")[0])
        stage_4_max = int(str(stage_4.GDD.values[0]).split("-")[1])

        gdd['stage'] = np.select(
            [
                (gdd['GDD'] >= stage_1_min) & (gdd['GDD'] <= stage_1_max),
                (gdd['GDD'] > stage_2_min) & (gdd['GDD'] <= stage_2_max),
                (gdd['GDD'] > stage_3_min) & (gdd['GDD'] <= stage_3_max),
                (gdd['GDD'] > stage_4_min) & (gdd['GDD'] <= stage_4_max)

            ],
            [1, 2, 3, 4],
            default=np.nan
        )

        gdd['mean_LST'] = gdd['mean']
        gdd['interpol_LST'] = gdd['interpol']
        gdd['filter_LST'] = gdd['filter']
        gdd = gdd.drop(columns=['mean', 'interpol', 'filter'])

        return gdd

