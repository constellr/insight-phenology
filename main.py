import pandas as pd
import geopandas as gpd

from phenology import *
from cropland import *
from plotting import *

pd.set_option('mode.chained_assignment', None)

if __name__ == '__main__':

    # rasterfiles
    dir_ndvi = r"folder-to-NDVI"
    dir_clip = r"folder-to-clipped-NDVI"
    dir_lsti = r"folder-to-LST"

    # input data
    aoi = r"syngenta_parcels.geojson"
    utm = r"utm_zones.geojson"

    # output
    output_csv = r"phenology_gdd.csv"

    aoi = gpd.read_file(aoi)
    utm = gpd.read_file(utm)

    final_df = pd.DataFrame()

    ### GDD parameters
    Tbase = 10
    Tmax = 25
    Tmin = 10

    aoi = get_crs(aoi,utm)

    gids = aoi.id.unique()
    for gid in gids:

        try:

            ### NDVI ###

            veg = aggregation(dir_ndvi,aoi,gid)
            df = preprocess_df(veg)
            df = smoothing(df)

            if len(df) > 0:

                peaks, peak_dates, max_val = get_peaks(df)
                sos, pos, eos = get_markers(df,peak_dates)
                plateaus = get_plateau(df)
                inflection_points, acceleration_1, acceleration_2, acceleration_3, acceleration_4 = get_derivatives(df,sos,pos,eos)
                rate = get_growth_rate(acceleration_3,acceleration_1)

                ### LST ###

                lst = aggregation(dir_lsti,aoi,gid)
                lst = preprocess_df(lst)
                gdd = get_gdd(lst,sos,eos,Tbase,Tmax,Tmin)

                ### merge both dataframes on date

                df['NDVI'] = df['gaussian']
                df = df.drop(columns=['id', 'mean', 'min', 'max', 'doy', 'interpol', 'gaussian'])
                gdd = gdd.drop(columns=['id', 'mean', 'min', 'max', 'doy', 'Tmax', 'interpol', 'gaussian'])

                merge = pd.merge(gdd, df, on='date')
                merge["id"] = gid
                merge["growth_rate"] = rate
                merge["SOS"] = sos
                merge["POS"] = pos
                merge["EOS"] = eos

                final_df = pd.concat([merge,final_df])

        except:
            pass

    final_df.to_csv(output_csv, sep=';')
