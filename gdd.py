import pandas as pd
from phenology import smoothing

def get_gdd_db(country, crop, variety):

    gdd_db = pd.read_csv("gdd/gdd_sugarcane.csv", delimiter=';')

    gdd_db = gdd_db[(gdd_db['country'] == country) & (gdd_db['crop'] == crop) & (gdd_db['variety'] == variety)]

    Tmax = gdd_db['Tmax'].values[0]
    Tbase = gdd_db['Tbase'].values[0]

    return Tmax, Tbase

def get_gdd(
        lst,
        sos_date,
        pos_date,
        eos_date,
        inflection_points,
        acceleration_points
    ):

    country = "India"
    crop = "sugarcane"
    variety = "Co 86033"

    Tmax, Tbase = get_gdd_db(country, crop, variety)

    if len(lst) > 0:

        lst['mean'] = lst['mean'] - 270
        lst['max'] = lst['max'] - 270
        lst['min'] = lst['min'] - 270

        lst['Tmax'] = lst['max'].clip(upper=Tmax)
        lst['mean'] = (lst['mean'] - Tbase).clip(lower=0)

        first_inflection = inflection_points['date'].head(1).values[0]
        last_inflection = inflection_points['date'].tail(1).values[0]
        first_acceleration = acceleration_points['date'].head(1).values[0]
        last_acceleration = acceleration_points['date'].tail(1).values[0]

        lst_daily = smoothing(lst)

        gdd = pd.DataFrame()
        gdd.at['fid'] = 0

        calc = lst_daily.loc[(lst_daily['date'] >= sos_date) & (lst_daily['date'] <= first_acceleration)]
        gdd['germination'] = calc['interpol'].sum()

        calc = lst_daily.loc[(lst_daily['date'] >= sos_date) & (lst_daily['date'] <= pos_date)]
        gdd['tillering'] = calc['interpol'].sum()

        calc = lst_daily.loc[(lst_daily['date'] >= sos_date) & (lst_daily['date'] <= last_inflection)]
        gdd['maturity'] = calc['interpol'].sum()

        calc = lst_daily.loc[(lst_daily['date'] >= sos_date) & (lst_daily['date'] <= eos_date)]
        gdd['harvest'] = calc['interpol'].sum()

        return gdd



