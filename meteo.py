import xarray as xr
import pandas as pd
import numpy as np
from datetime import datetime
import ee

def get_era5_daily_cds(lat, lon, startdate, enddate, variable='2m_temperature'):
    """
    Extract daily mean, min, max temperatures from ERA5 for a given lat/lon and time period.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
        variable (str): ERA5 variable to extract (default is '2m_temperature').

    Returns:
        daily_data (dict): Dictionary containing 'mean', 'min', and 'max' daily values.
    """

    startdate = pd.to_datetime(startdate)
    enddate = pd.to_datetime(enddate)

    era5_url = (
        f"https://cds.climate.copernicus.eu/api/v2/resources/reanalysis"
        f"?product=reanalysis"
        f"&variable={variable}"
        f"&year={startdate.year},{enddate.year}"
        f"&month={startdate.month},{enddate.month}"
        f"&day={startdate.day},{enddate.day}"
        f"&time=12:00"
        f"&format=netcdf"
        f"&lon={lon}"
        f"&lat={lat}"
    )

    # Load ERA5 data from CDS API
    ds = xr.open_dataset(era5_url)

    # Extract relevant variables
    temp = ds[variable]

    # Extract daily statistics
    daily_mean = temp.resample(time='1D').mean(dim='time')
    daily_min = temp.resample(time='1D').min(dim='time')
    daily_max = temp.resample(time='1D').max(dim='time')

    # Convert to numpy arrays and flatten them
    daily_mean_values = daily_mean.values.flatten()
    daily_min_values = daily_min.values.flatten()
    daily_max_values = daily_max.values.flatten()

    # Combine into a dictionary
    daily_weather = {
        "mean": daily_mean_values.tolist(),
        "min": daily_min_values.tolist(),
        "max": daily_max_values.tolist(),
    }

    return daily_weather

def get_era5_daily_gee(lat: float, lon: float, startdate: str, enddate: str):
    """
    Extract daily mean, min, max temperatures from ERA5 using Google Earth Engine.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        startdate (str): Start date in 'YYYY-MM-DD' format.
        enddate (str): End date in 'YYYY-MM-DD' format.

    Returns:
        dict: Dictionary containing daily 'mean', 'min', and 'max' temperature lists.
    """

    ee.Authenticate()
    ee.Initialize()

    era5 = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR") \
        .filterDate(startdate, enddate) \
        .select(['temperature_2m', 'temperature_2m_min', 'temperature_2m_max'])

    point = ee.Geometry.Point([lon, lat])

    def extract_daily(image):
        stats = image.reduceRegion(reducer=ee.Reducer.first(), geometry=point, scale=11132)
        return ee.Feature(None, stats)

    daily_features = era5.map(extract_daily).getInfo()

    #dates = [feature['id'] for feature in daily_features['features']]
    timestamps = era5.aggregate_array("system:time_start").getInfo()
    dates = [datetime.utcfromtimestamp(ts / 1000).strftime('%Y-%m-%d') for ts in timestamps]

    daily_mean_values = [feature['properties']['temperature_2m'] for feature in daily_features['features']]
    daily_min_values = [feature['properties']['temperature_2m_min'] for feature in daily_features['features']]
    daily_max_values = [feature['properties']['temperature_2m_max'] for feature in daily_features['features']]

    # Create a DataFrame
    df = pd.DataFrame({
        'date': dates,
        'VWST_mean': daily_mean_values,
        'VWST_min': daily_min_values,
        'VWST_max': daily_max_values
    })

    return df
