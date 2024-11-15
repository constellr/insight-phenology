import pandas as pd
import geopandas as gpd

from phenology import *
from canopy import *
from plotting import *
from gdd import *

pd.set_option('mode.chained_assignment', None)

if __name__ == '__main__':

    # rasterfiles
    dir_ndvi = r"C:\Users\DimoDimov\Documents\DATA\LST_Syngenta\Landsat\NDVI"
    dir_clip = r"C:\Users\DimoDimov\Documents\DATA\LST_Syngenta\Landsat\NDVI\CLIP"
    dir_lsti = r"C:\Users\DimoDimov\Documents\DATA\LST_Syngenta\LST"

    # input data
    aoi = r"C:\Users\DimoDimov\Documents\DATA\LST_Syngenta\syngenta_parcels.geojson"
    utm = r"C:\Users\DimoDimov\Documents\DATA\utm_zones.geojson"

    # output
    output_csv = r"phenology_gdd.csv"

    aoi = gpd.read_file(aoi)
    utm = gpd.read_file(utm)

    final_df = pd.DataFrame()

    ### GDD parameters
    Tbase = 10
    Tmax = 40
    Tmin = 10

    aoi = get_crs(aoi,utm)

    gids = aoi.id.unique()
    for gid in gids:

        ### NDVI ###

        veg = aggregation(dir_ndvi, aoi, gid)
        df = preprocess_df(veg)
        df = smoothing(df)

        if len(df) > 0:

            peak_dates, peak_values, pos_date, pos_value = get_peaks(df)

            try:
                sos_date, sos_value, eos_date, eos_value = get_markers(df, pos_date)
            except:
                sos_date = df['date'].head(1).values[0]
                sos_value = df['filter'].head(1).values[0]
                eos_date = df['date'].tail(1).values[0]
                eos_value = df['filter'].tail(1).values[0]

            inflection_points, acceleration_points = get_derivatives(df, sos_date, pos_date, eos_date)
            growth_rate = get_growth_rate(sos_value, pos_value)
            plateaus = get_plateau(df)

            ### LST ###

            lst = aggregation(dir_lsti, aoi, gid)
            lst = preprocess_df(lst)

            gdd = get_gdd(
                lst,
                sos_date,
                pos_date,
                eos_date,
                inflection_points,
                acceleration_points
            )

            gdd['id'] = gid

            ### merge both dataframes on date

            df['NDVI'] = df['filter']
            df = df.drop(columns=['mean', 'min', 'max', 'doy', 'interpol', 'filter'])

            ard_df = df.groupby('id').agg(
                sum_ndvi=('NDVI', 'sum'),
                std_ndvi=('NDVI', 'std'),
                mean_ndvi=('NDVI', 'mean')
            ).reset_index()

            ard_df["growth_rate"] = growth_rate
            ard_df["SOS"] = sos_date
            ard_df["POS"] = pos_date
            ard_df["EOS"] = eos_date

            for i in range(0,len(inflection_points)):
                if i == 2:
                    ard_df[f"inflection_date_{i}"] = inflection_points['date'].values[i]
                    ard_df[f"inflection_value_{i}"] = inflection_points['filter'].values[i]
                break

            merge = pd.merge(ard_df, gdd, on='id')

            final_df = pd.concat([merge,final_df])

    final_df.to_csv(output_csv, sep=';')
