import pandas as pd
import geopandas as gpd

from phenology import *
from canopy import *
from plotting import *
from gdd import *

pd.set_option('mode.chained_assignment', None)

if __name__ == '__main__':

    ##############################################################################
    ##############################################################################

    # rasterfiles
    dir_ndvi = r"C:\Users\DimoDimov\Documents\DATA\LST_Syngenta\Landsat\NDVI"
    dir_clip = r"C:\Users\DimoDimov\Documents\DATA\LST_Syngenta\Landsat\NDVI\CLIP"
    dir_lsti = r"C:\Users\DimoDimov\Documents\DATA\LST_Syngenta\LST"

    # input data
    aoi = r"C:\Users\DimoDimov\Documents\DATA\LST_Syngenta\syngenta_parcels.geojson"
    utm = r"C:\Users\DimoDimov\Documents\DATA\utm_zones.geojson"

    # output
    output_csv = r"phenology_features.csv"
    output_csv_timeseries = r"phenology_timeseries.csv"

    # params
    country = "India"
    crop = "sugarcane"
    variety = "Co 86033"

    ##############################################################################
    ##############################################################################

    aoi = gpd.read_file(aoi)
    utm = gpd.read_file(utm)

    xf = pd.DataFrame()
    yf = pd.DataFrame()

    aoi = get_crs(aoi,utm)

    gids = aoi.id.unique()
    for gid in gids:

        ### NDVI ###
        veg = aggregation(dir_ndvi, aoi, gid)
        ndvi_timeseries = preprocess_df(veg)
        ndvi_timeseries = smoothing(ndvi_timeseries)

        if len(ndvi_timeseries) > 0:

            peak_dates, peak_values, pos_date, pos_value = get_peaks(ndvi_timeseries)

            try:
                sos_date, sos_value, eos_date, eos_value = get_markers(ndvi_timeseries, pos_date)
            except:
                sos_date = ndvi_timeseries['date'].head(1).values[0]
                sos_value = ndvi_timeseries['filter'].head(1).values[0]
                eos_date = ndvi_timeseries['date'].tail(1).values[0]
                eos_value = ndvi_timeseries['filter'].tail(1).values[0]

            inflection_points, acceleration_points = get_derivatives(ndvi_timeseries, sos_date, pos_date, eos_date)
            growth_rate = get_growth_rate(sos_value, pos_value)
            plateaus = get_plateau(ndvi_timeseries)

            ### LST ###
            lst_timeseries = aggregation(dir_lsti, aoi, gid)
            lst_timeseries = preprocess_df(lst_timeseries)

            gdd_timeseries = get_gdd_corridors(
                lst_timeseries,
                sos_date,
                eos_date,
                country, crop, variety
            )

            gdd_features = get_gdd(
                lst_timeseries,
                sos_date,
                pos_date,
                eos_date,
                inflection_points,
                acceleration_points,
                country, crop, variety
            )

            ard_df = vegetation_stats(
                ndvi_timeseries,
                sos_date,
                pos_date,
                eos_date,
                inflection_points,
                acceleration_points
            )

            gdd_features['id'] = gid
            gdd_timeseries['id'] = gid
            ard_df['id'] = gid

            ard_df["growth_rate"] = growth_rate
            ard_df["SOS_date"] = sos_date
            ard_df["POS_date"] = pos_date
            ard_df["EOS_date"] = eos_date
            ard_df["SOS_value"] = sos_value
            ard_df["POS_value"] = pos_value
            ard_df["EOS_value"] = eos_value

            ard_df['first_inflection_date'] = inflection_points['date'].head(1).values[0]
            ard_df['first_inflection_value'] = inflection_points['filter'].head(1).values[0]
            ard_df['last_inflection_date'] = inflection_points['date'].tail(1).values[0]
            ard_df['last_inflection_value'] = inflection_points['filter'].tail(1).values[0]

            ard_df['first_acceleration_date'] = acceleration_points['date'].head(1).values[0]
            ard_df['first_acceleration_value'] = acceleration_points['filter'].head(1).values[0]
            ard_df['last_acceleration_date'] = acceleration_points['date'].tail(1).values[0]
            ard_df['last_acceleration_value'] = acceleration_points['filter'].tail(1).values[0]

            #################################
            #################################

            ndvi_timeseries['mean_NDVI'] = ndvi_timeseries['mean']
            ndvi_timeseries['interpol_NDVI'] = ndvi_timeseries['interpol']
            ndvi_timeseries['filter_NDVI'] = ndvi_timeseries['filter']
            ndvi_timeseries = ndvi_timeseries.drop(columns=['mean', 'interpol', 'filter'])

            merge_timeseries = pd.merge(ndvi_timeseries, gdd_timeseries, on=['id','date'])
            merge_features = pd.merge(ard_df, gdd_features, on='id')

            #plot_gdd(merge_timeseries)

            xf = pd.concat([merge_timeseries,xf])
            yf = pd.concat([merge_features,yf])

    xf.to_csv(output_csv_timeseries, sep=';', index=False)
    yf.to_csv(output_csv, sep=';', index=False)
