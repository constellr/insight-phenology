import pandas as pd
import geopandas as gpd

from preprocessing import *
from phenology import *
from feature_engineering import *
from canopy import *
from plotting import *
from gdd import *

pd.set_option('mode.chained_assignment', None)

if __name__ == '__main__':

    ##############################################################################
    ##############################################################################
    ### =============================== Params =============================== ###

    # rasterfiles
    dir_ndvi = r"C:\Users\DimoDimov\Documents\DATA\LST_Swan\Landsat\NDVI"
    dir_clip = r"C:\Users\DimoDimov\Documents\DATA\LST_Swan\Landsat\NDVI-CLIP"
    dir_lsti = r"C:\Users\DimoDimov\Documents\DATA\LST_Swan\LST"

    # input data
    aoi = r"C:\Users\DimoDimov\Documents\DATA\LST_Swan\swan_2024-10-24_poc_edit_WGS.geojson"
    #aoi = r"C:\Users\DimoDimov\Documents\DATA\LST_Syngenta\syngenta_parcels.geojson"

    utm = r"C:\Users\DimoDimov\Documents\DATA\utm_zones.geojson"

    # output
    output_1 = r"summary_stats.csv"
    output_2 = r"phenology_stats.csv"
    output_3 = r"ncf_stats.csv"

    # params
    country = "India"
    crop = "sugarcane"
    variety = "Co 89003"

    startdate = '2021-09-01'
    enddate = '2022-07-01'

    slicing = True
    plotting = True
    ### =============================== Params =============================== ###
    ##############################################################################
    ##############################################################################

    aoi = gpd.read_file(aoi)
    utm = gpd.read_file(utm)

    xf = pd.DataFrame()
    yf = pd.DataFrame()
    zf = pd.DataFrame()

    aoi = get_crs(aoi,utm)

    for i, row in aoi.iterrows():

        gid = row['id']

        try:
            startdate = row['Sowing_3']
            enddate = row['Harvesting_4']
            startdate = datetime.strptime(startdate, '%d-%b-%Y')
            enddate = datetime.strptime(enddate, '%d-%b-%Y')
        except:
            startdate = '2023-04-15'
            enddate = '2023-10-01'
            startdate = datetime.strptime(startdate, '%Y-%m-%d')
            enddate = datetime.strptime(enddate, '%Y-%m-%d')

        startdate = startdate.strftime('%Y-%m-%dT%H:%M:%S')
        enddate = enddate.strftime('%Y-%m-%dT%H:%M:%S')

        ### ================================ NDVI ================================ ###

        veg = aggregation(dir_ndvi, aoi, gid)
        ndvi_timeseries = preprocess_df(veg)
        ndvi_timeseries = smoothing(ndvi_timeseries)

        if slicing == True:
            ndvi_timeseries = ndvi_timeseries[(ndvi_timeseries['date'] >= startdate) & (ndvi_timeseries['date'] <= enddate)]

        if len(ndvi_timeseries) > 0:

            peaks, peak_dates, peak_values, pos_date, pos_value, vos_date, vos_value = get_peaks(ndvi_timeseries)
            sos_date, sos_value, eos_date, eos_value = get_markers(ndvi_timeseries, peak_dates)

            inflection_points, acceleration_points = get_derivatives(ndvi_timeseries, sos_date, pos_date, eos_date)
            growth_rate = get_growth_rate(sos_value, pos_value)
            plateaus = get_plateau(ndvi_timeseries)

            ### ================================ LST ================================ ###

            lst_timeseries = aggregation(dir_lsti, aoi, gid)
            lst_timeseries = preprocess_df(lst_timeseries)

            if slicing == True:
                lst_timeseries = lst_timeseries[(lst_timeseries['date'] >= vos_date) & (lst_timeseries['date'] <= enddate)]

            gdd_timeseries = get_gdd_corridors(
                lst_timeseries,
                vos_date,
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

            ndvi_features = vegetation_stats(
                ndvi_timeseries,
                sos_date,
                pos_date,
                eos_date,
                inflection_points,
                acceleration_points
            )

            summary_features = summary_stats(
                gid,
                ndvi_timeseries,
                lst_timeseries,
                sos_date,
                eos_date,
            )

            ard_timeseries, ard_features = feature_engineering(
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
                acceleration_points,
            )

            startdate = datetime.strptime(startdate.split('.')[0], '%Y-%m-%dT%H:%M:%S')
            enddate = datetime.strptime(enddate.split('.')[0], '%Y-%m-%dT%H:%M:%S')

            ### ================================ Plotting & Visualization ================================ ###

            if plotting == True:

                plot_all(
                    ard_timeseries,
                    ndvi_timeseries,
                    gdd_timeseries,
                    plateaus,
                    inflection_points,
                    acceleration_points,
                    peaks, peak_dates, peak_values,
                    sos_date, pos_date, eos_date,
                    sos_value, eos_value,
                    growth_rate, pos_value,
                    startdate, enddate
                )

            ### ================================ Canopy ================================ ###

            """
            img, nearest_date = get_parcel_image(dir_clip, pos_date, gid)
            sorted_labels_map = clustering(img)
            merged_image, cropland = postprocess(sorted_labels_map, img)

            ncf_features = pd.DataFrame()
            ncf_features['id'] = [gid]
            ncf_features['cropland'] = [cropland]

            plot_canopy_map(img, nearest_date, merged_image, cropland)

            zf = pd.concat([ncf_features,zf])
            """

            ### ================================ Data Prep ================================ ###

            yf = pd.concat([summary_features, yf])
            xf = pd.concat([ard_features, xf])

    yf.to_csv(output_1, sep=';', index=False)
    xf.to_csv(output_2, sep=';', index=False)
    #zf.to_csv(output_3, sep=';', index=False)
