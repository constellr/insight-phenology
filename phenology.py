import os
import pandas as pd
import geopandas as gpd
import numpy as np

from shapely.geometry import shape
from scipy.ndimage import gaussian_filter1d
from rasterstats import zonal_stats
from scipy.signal import find_peaks, savgol_filter

def get_crs(aoi,utm):
    if aoi.crs != utm.crs:
        aoi.to_crs(utm.crs)

    intersection = gpd.overlay(aoi,utm, how='intersection')
    epsg = intersection['epsg'].unique()[0]
    aoi = aoi.to_crs(epsg)

    return aoi

def aggregation(dir,aoi,gid):
    rows = []
    directory = os.fsencode(dir)

    aoi = aoi.loc[aoi.id == gid]
    for i, feature in aoi.iterrows():
        geom = shape(feature['geometry'])

    for file in os.listdir(directory):
        filename = os.fsdecode(file)

        if (filename.endswith(".tif") == True or filename.endswith(".tiff") == True) and "CLOUDS" not in filename:
            raster = f"{dir}\\{filename}"

            try:
                date = filename.split("_")[2]
            except:
                date = filename[:8]

            statistics = zonal_stats(
                geom,
                raster,
                stats="mean min max",
                all_touched=True,
                nodata=0,
                categorical=False,
            )

            mean = statistics[0]['mean']
            min = statistics[0]['min']
            max = statistics[0]['max']
            id = int(feature['id'])

            rows.append([id, date, mean, min, max])

    return rows

def preprocess_df(rows):
    df = pd.DataFrame(
        rows,
        columns=[
            "id",
            "date",
            "mean",
            'min',
            'max'
        ]
    )

    df['date'] = pd.to_datetime(df['date'])
    df['doy'] = df['date'].dt.dayofyear
    df = df.sort_values(by='date')

    return df

def smoothing(df):
    df.set_index('date', inplace=True)
    df = df[~df.index.duplicated()]
    gf = df.resample('1D').asfreq()
    gf['interpol'] = gf['mean'].interpolate(method='linear')
    gf['gaussian'] = gaussian_filter1d(gf['interpol'].values, 15)
    gf = gf.reset_index()

    return gf

def get_markers(gf,peak_dates):

    if len(peak_dates) == 0:
        ndvi_dates = gf['date'].values
        ndvi_values = gf['gaussian'].values
        pos_index = np.argmax(ndvi_values)
        date_pos = ndvi_dates[pos_index]
        peak_dates.loc[0] = pd.to_datetime(date_pos)

    date_sos = None
    date_eos = None

    for p in range(0,len(peak_dates)):
        date_pos = peak_dates.values[p]

        sf = gf.loc[(gf['date'] <= date_pos)]
        if len(sf) > 2:
            ndvi_dates = sf['date'].values
            ndvi_values = sf['gaussian'].values
            gradient = np.gradient(ndvi_values)
            sos_index = np.argmax(gradient > 0.001)
            date_sos = ndvi_dates[sos_index]

        sf = gf.loc[(gf['date'] >= date_pos)]
        if len(sf) > 2:

            ndvi_dates = sf['date'].values
            ndvi_values = sf['gaussian'].values
            gradient = np.gradient(ndvi_values)
            eos_index = len(gradient) - np.argmax(gradient[::-1] < -0.001) - 1
            date_eos = ndvi_dates[eos_index]

        if date_sos and date_eos:
            return date_sos, date_pos, date_eos

def get_plateau(gf):
    threshold = 0.002
    ndvi_dates = gf['date'].values
    ndvi_values = gf['gaussian'].values

    differences = np.abs(np.diff(ndvi_values))
    plateau_mask = differences < threshold
    plateau_regions = np.where(plateau_mask)[0]

    plateaus = []
    current_plateau = []

    for i in plateau_regions:
        if not current_plateau or i == current_plateau[-1] + 1:
            current_plateau.append(i)
        else:
            if len(current_plateau) > 1:
                plateaus.append(current_plateau)
            current_plateau = [i]

    if len(current_plateau) > 1:
        plateaus.append(current_plateau)

    return plateaus

def get_peaks(gf):
    peaks, _ = find_peaks(gf['gaussian'].values, height=0)
    peak_dates = gf['date'].iloc[peaks]
    peak_dates = pd.to_datetime(peak_dates)
    max_ndvi = np.max(gf['gaussian'].values)

    return peaks, peak_dates, max_ndvi

def get_derivatives(gf,sos,pos,eos):
    sf = gf.loc[(gf['date'] > sos) & (gf['date'] < eos)]
    if len(sf) > 2:
        sf['dy'] = sf['gaussian'].diff()
        sf['ddy'] = sf['dy'].diff()
        sf['dddy'] = sf['ddy'].diff()

        sf['inflection'] = np.sign(sf['ddy']).diff().fillna(0).abs() > 0
        inflection_points = sf[sf['inflection']][['date', 'gaussian']]

        xf = sf.loc[(sf['date'] < pos)]
        xf['acceleration'] = np.sign(xf['dddy']).diff().fillna(0).abs() > 0
        acceleration_1 = xf[xf['acceleration']][['date', 'gaussian']]

        acceleration_3 = xf[xf['acceleration'] == True]
        acceleration_3 = acceleration_3.head(1)

        yf = sf.loc[(sf['date'] > pos)]
        yf['acceleration'] = np.sign(yf['dddy']).diff().fillna(0).abs() > 0
        acceleration_2 = yf[yf['acceleration']][['date', 'gaussian']]

        acceleration_4 = yf[yf['acceleration'] == True]
        acceleration_4 = acceleration_4.tail(1)

        return inflection_points, acceleration_1, acceleration_2, acceleration_3, acceleration_4

def get_growth_rate(x,acceleration_1):
    try:
        tf = pd.DataFrame()
        tf['date'] = [x['date'].iloc[0], acceleration_1['date'].iloc[1]]
        tf['ndvi'] = [x['gaussian'].values[0], acceleration_1['gaussian'].iloc[1]]
        p1 = tf['ndvi'].values[0]
        p2 = tf['ndvi'].values[1]
        gradients = np.gradient([p1,p2])[0]

    except:
        gradients = 0

    return gradients

def get_gdd(lst_ts,sos,eos,Tbase,Tmax,Tmin):
    gdd = lst_ts.loc[(lst_ts['date'] >= sos) & (lst_ts['date'] <= eos)]
    if len(gdd) > 2:
        gdd['mean'] = gdd['mean'] - 270
        gdd['max'] = gdd['max'] - 270
        gdd['min'] = gdd['min'] - 270

        gdd['Tmax'] = gdd['max'].clip(upper=Tmax)
        #gdd['mean'] = (gdd['Tmax'] + Tmin) / 2
        gdd['mean'] = (gdd['Tmax'] + gdd['min']) / 2
        gdd['mean'] = (gdd['mean'] - Tbase).clip(lower=0)

        gdd_ts = smoothing(gdd)
        gdd_ts['GDD'] = gdd_ts['interpol'].cumsum()

        return gdd_ts


