import pandas as pd
from phenology import smoothing
import numpy as np

def get_gdd_db(country, crop, variety):

    gdd_db = pd.read_csv("gdd/gdd_crops.csv", delimiter=';')
    gdd_db = gdd_db[(gdd_db['country'] == country) & (gdd_db['crop'] == crop) & (gdd_db['variety'] == variety)]

    Tmax = gdd_db['Tmax'].values[0]
    Tbase = gdd_db['Tbase'].values[0]
    stagenames = gdd_db['stage'].values

    return gdd_db, Tmax, Tbase, stagenames

def get_lst_stages(
        lst,
        sos_date,
        pos_date,
        eos_date,
        inflection_points,
        acceleration_points,
        country, crop, variety
    ):

    gdd_db, Tmax, Tbase, stagenames = get_gdd_db(country, crop, variety)
    lst_df = lst.copy(deep=True)

    if len(lst_df) > 0:

        lst_daily = smoothing(lst_df)

        lst_daily['interpol'] = lst_daily['interpol'] - 273.15
        lst_daily['interpol'] = lst_daily['interpol'].clip(upper=Tmax)
        lst_daily['interpol'] = lst_daily['interpol'].clip(lower=Tbase)
        lst_daily['interpol'] = (lst_daily['interpol'] - Tbase).clip(lower=0)

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

def get_gdd_corridors(
        lst,
        meteo_data,
        sos_date,
        eos_date,
        country,
        crop,
        variety
    ):

    gdd_db, Tmax, Tbase, stagenames = get_gdd_db(country, crop, variety)
    lst_df = lst.copy(deep=True)

    stagenames = stagenames.tolist()

    if len(lst_df) > 0:

        lst_daily = smoothing(lst_df)
        lst_daily['date'] = pd.to_datetime(lst_daily['date'])
        meteo_data['date'] = pd.to_datetime(meteo_data['date'])

        lst_merge = pd.merge(lst_daily, meteo_data, on='date')
        
        targets = ['VWST_mean', 'interpol']
        for target in targets:

            lst_merge[target] = lst_merge[target] - 273.15
            lst_merge[target] = lst_merge[target].clip(upper=Tmax)
            lst_merge[target] = lst_merge[target].clip(lower=Tbase)
            lst_merge[target] = (lst_merge[target] - Tbase).clip(lower=0)

        """
        lst_df['mean'] = lst_df['mean'] - 273.15
        lst_df['mean'] = lst_df['mean'].clip(upper=Tmax)
        lst_df['mean'] = lst_df['mean'].clip(lower=Tbase)
        lst_df['mean'] = (lst_df['mean'] - Tbase).clip(lower=0)

        lst_daily = smoothing(lst_df)
        """

        gdd = lst_merge.loc[(lst_merge['date'] >= sos_date) & (lst_merge['date'] <= eos_date)]

        gdd['GDD'] = gdd['VWST_mean'].cumsum()
        gdd['GDD_LST'] = gdd['interpol'].cumsum()

        if crop == "sugarcane":
            stage_1 = gdd_db[gdd_db['stage'] == 'Germination']
            stage_2 = gdd_db[gdd_db['stage'] == 'Tillering']
            stage_3 = gdd_db[gdd_db['stage'] == 'Grand Growth Phase']
            stage_4 = gdd_db[gdd_db['stage'] == 'Maturity']
        if crop == "corn":
            stage_1 = gdd_db[gdd_db['stage'] == 'V6 (Six-leaf stage)']
            stage_2 = gdd_db[gdd_db['stage'] == 'VT (Tasseling)']
            stage_3 = gdd_db[gdd_db['stage'] == 'R1 (Silking)']
            stage_4 = gdd_db[gdd_db['stage'] == 'R6 (Maturity)']

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
            choicelist=stagenames,
            default='NULL'
        )

        gdd['mean_LST'] = gdd['mean']
        gdd['interpol_LST'] = gdd['interpol']
        gdd['filter_LST'] = gdd['filter']
        gdd = gdd.drop(columns=['mean', 'interpol', 'filter'])

        return gdd



