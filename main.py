import pandas as pd
import geopandas as gpd
from datetime import datetime
import pyproj
from shapely.ops import transform

from preprocessing import *
from phenology import *
from feature_engineering import *
from canopy import *
from plotting import *
from gdd import *
from meteo import *

pd.set_option('mode.chained_assignment', None)

def load_config():
    """
    Load and return the configuration parameters.
    """
    return {
        # Directories
        "dir_ndvi": r"C:\Users\DimoDimov\Documents\DATA\LST_Syngenta\LANDSAT\NDVI",
        "dir_clip": r"C:\Users\DimoDimov\Documents\DATA\LST_Syngenta\Landsat\NDVI-CLIP",
        "dir_lsti": r"C:\Users\DimoDimov\Documents\DATA\LST_Syngenta\LST",

        # Input files
        "aoi": r"C:\Users\DimoDimov\Documents\DATA\LST_Syngenta\syngenta_parcels.geojson",
        "utm": r"C:\Users\DimoDimov\Documents\DATA\utm_zones.geojson",

        # Output files
        "output_summary_stats": "summary_stats.csv",
        "output_phenology_stats": "phenology_stats.csv",
        "output_ncf_stats": "ncf_stats.csv",
        "output_timeseries_stats": "timeseries.csv",

        "country": "USA",  # Country for analysis ("India", "USA", "Brazil", "Germany")
        "crop": "corn",  # Target crop ("sugarcane", "wheat", "corn", "rice")
        "variety": "Dent corn",  # Crop variety (specific strain or type)
        "start_date": "2023-04-01",  # Start date of the analysis (YYYY-MM-DD)
        "end_date": "2023-10-01",  # End date of the analysis (YYYY-MM-DD)
        "slicing": False,  # Enable/disable data slicing (Boolean)
        "plotting": True,  # Enable/disable plotting of results (Boolean),
        "strategy": "ALL", # Select output statistics: ("ALL", "phenology", "summary", "timeseries")
        "resampling": "None", # Select resampling for sequential features ("None", "monthly", "weekly")
    }

def parse_dates(row: pd.Series, default_start: str, default_end: str) -> tuple[datetime, datetime]:
    """
    Parse sowing and harvesting dates for a row or return defaults.
    """
    try:
        start = datetime.strptime(row['Sowing_3'], '%d-%b-%Y')
        end = datetime.strptime(row['Harvesting_4'], '%d-%b-%Y')
    except KeyError:
        start = datetime.strptime(default_start, '%Y-%m-%d')
        end = datetime.strptime(default_end, '%Y-%m-%d')
    return start, end

def process_parcel(
        row, aoi, crs, config: dict,
        wf: pd.DataFrame, xf: pd.DataFrame, yf: pd.DataFrame, zf: pd.DataFrame
    ):
    """
    Process a single parcel row to extract features and generate stats.
    """
    gid = row['id']
    print(f"Processing parcel ID: {gid}")

    def transform_to_epsg4326(geometry, source_crs):
        transformer = pyproj.Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)
        return transform(transformer.transform, geometry)
    transformed_geometry = transform_to_epsg4326(row.geometry, crs)
    centroid = transformed_geometry.centroid
    lat, lon = centroid.y, centroid.x

    start_date, end_date = parse_dates(row, config['start_date'], config['end_date'])
    start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%S')
    end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%S')

    veg = aggregation(config['dir_ndvi'], aoi, gid)
    ndvi_data = preprocess_df(veg)
    ndvi_data = smoothing(ndvi_data)

    if config['slicing']:
        ndvi_data = ndvi_data[(ndvi_data['date'] >= start_date_str) & (ndvi_data['date'] <= end_date_str)]

    if len(ndvi_data) > 0:
        peaks, peak_dates, peak_values, pos_date, pos_value, vos_date, vos_value = get_peaks(ndvi_data)
        sos_date, sos_value, eos_date, eos_value = get_markers(ndvi_data, peak_dates)
        inflection_points, acceleration_points = get_derivatives(ndvi_data, sos_date, pos_date, eos_date)
        growth_rate = get_growth_rate(sos_value, pos_value)
        plateaus = get_plateau(ndvi_data)

        lst_data = aggregation(config['dir_lsti'], aoi, gid)
        lst_data = preprocess_df(lst_data)

        if config['slicing']:
            lst_data = lst_data[(lst_data['date'] >= start_date_str) & (lst_data['date'] <= end_date_str)]

        meteo_data = get_era5_daily_gee(lat, lon, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

        gdd_corridors = get_gdd_corridors(
            lst_data, meteo_data, start_date, end_date,
            config['country'], config['crop'], config['variety']
        )

        lst_phenology = get_lst_stages(
            lst_data, sos_date, pos_date, eos_date,
            inflection_points, acceleration_points,
            config['country'], config['crop'], config['variety']
        )

        ndvi_phenology = get_ndvi_stages(
            ndvi_data, sos_date, pos_date, eos_date,
            inflection_points, acceleration_points
        )

        summary_features = summary_stats(gid, ndvi_data, lst_data, sos_date, eos_date)

        ard_timeseries, phenology_features = feature_engineering(
            gid, gdd_corridors, lst_phenology, ndvi_phenology, ndvi_data, growth_rate,
            sos_date, sos_value, pos_date, pos_value, eos_date, eos_value, inflection_points, acceleration_points
        )

        timeseries_features = get_timeseries_stats(
            gid,
            lst_data,
            ndvi_data,
        )

        img, nearest_date = get_parcel_image(config['dir_clip'], pos_date, gid)
        sorted_labels_map = clustering(img)
        merged_image, cropland = postprocess(sorted_labels_map, img)

        ncf_features = pd.DataFrame()
        ncf_features['id'] = [gid]
        ncf_features['cropland'] = [cropland]

        if config['plotting']:
            plot_all(
                ard_timeseries, ndvi_data, gdd_corridors, plateaus, inflection_points, acceleration_points,
                peaks, peak_dates, peak_values, sos_date, pos_date, eos_date, sos_value, eos_value, growth_rate, pos_value,
                start_date, end_date
            )

            plot_canopy_map(img, nearest_date, merged_image, cropland)

        # Append results to dataframes
        wf = pd.concat([summary_features, wf])
        xf = pd.concat([phenology_features, xf])
        yf = pd.concat([ncf_features, yf])
        zf = pd.concat([timeseries_features, zf])

    return wf, xf, yf, zf

def main():
    config = load_config()
    global aoi
    aoi = gpd.read_file(config['aoi'])
    utm = gpd.read_file(config['utm'])

    # Ensure CRS consistency
    aoi = get_crs(aoi, utm)
    crs = aoi.crs

    wf, xf, yf, zf = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    for _, row in aoi.iterrows():
        #try:
        xf, yf, yf, zf = process_parcel(row, aoi, crs, config, wf, xf, yf, zf)
        #except Exception as e:
         #   print(f"Error processing parcel ID {row['id']}: {e}")

    # Save results
    wf.to_csv(config['output_summary_stats'], sep=';', index=False)
    xf.to_csv(config['output_phenology_stats'], sep=';', index=False)
    yf.to_csv(config['output_ncf_stats'], sep=';', index=False)

    zf_seq = get_sequential_features(zf, config['resampling'])
    zf_seq.to_csv(config['output_timeseries_stats'], sep=';', index=False)

if __name__ == "__main__":
    main()
