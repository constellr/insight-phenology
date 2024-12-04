import pandas as pd
import numpy as np

from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks, savgol_filter

def smoothing(df):
    '''
    Main function to
    - resample NDVI time series to daily/weekly/decadal/monthly intervals
    - interpolate and gap-fill resampled time series
    - apply smoothing filter like filter or savitzky-golay

    Prefered filter is gaussian-1D to reduce noise and to enable extraction of derivatives.
    Savitzky-Golay preserves time series shape, but yields too much noise still.
    '''

    sf = df.copy(deep=True)
    sf.set_index('date', inplace=True)
    sf = sf[~sf.index.duplicated()]
    gf = sf.resample('1D').asfreq()
    gf['interpol'] = gf['mean'].interpolate(method='linear')

    filter = "gaussian"

    if filter == "gaussian":
        gf['filter'] = gaussian_filter1d(gf['interpol'].values, 15)
    if filter == "savgol":
        gf['filter'] = savgol_filter(gf['interpol'].values, 9, 2)

    gf = gf.reset_index()

    return gf

def get_peaks(gf):
    '''
    1. get peaks from the timer series, there can be multiple peaks,
    especially for sugarcane, grass, alfalfa.

    2. then get absolute POS
    '''

    peaks, _ = find_peaks(gf['filter'].values, height=0)
    peak_dates = gf['date'].iloc[peaks]
    peak_dates = pd.to_datetime(peak_dates)
    peak_values = gf['filter'].iloc[peaks]

    max_index = gf['filter'].idxmax()
    pos_date = gf.loc[max_index, 'date']
    pos_value = gf.loc[max_index, 'filter']

    hf = gf.copy()
    hf = hf[hf['date'] < pos_date]
    min_index = hf['filter'].idxmin()
    vos_date = hf.loc[min_index, 'date']
    vos_value = hf.loc[min_index, 'filter']

    return peaks, peak_dates, peak_values, pos_date, pos_value, vos_date, vos_value

def get_markers(gf, pos_dates):
    '''
    get the Start of Season and End of Season
    based on the gradient changes of the time series.
    Default threshold is 0.001
    '''

    sos_date = None
    sos_value = None
    eos_date = None
    eos_value = None

    ndvi_threshold = 0.001

    for p in range(0,len(pos_dates)):
        pos_date = pos_dates.values[p]

        sf = gf.loc[(gf['date'] <= pos_date)]
        if len(sf) > 2:
            ndvi_dates = sf['date'].values
            ndvi_values = sf['filter'].values
            gradient = np.gradient(ndvi_values)
            sos_index = np.argmax(gradient > ndvi_threshold)
            sos_date = ndvi_dates[sos_index]
            sos_value = ndvi_values[sos_index]

        sf = gf.loc[(gf['date'] >= pos_date)]
        if len(sf) > 2:

            ndvi_dates = sf['date'].values
            ndvi_values = sf['filter'].values
            gradient = np.gradient(ndvi_values)
            eos_index = len(gradient) - np.argmax(gradient[::-1] < -ndvi_threshold) - 1
            eos_date = ndvi_dates[eos_index]
            eos_value = ndvi_values[eos_index]

        if sos_date and eos_date:
            return sos_date, sos_value, eos_date, eos_value

def get_plateau(gf):
    '''
    get the low and high NDVI plateaus which indicate stagnation:
    - high plateau = NDVI saturation and max canopy/biomass development
    - low plateau = low or no growth (after harvest, before sowing)
    '''
    threshold = 0.002
    ndvi_dates = gf['date'].values
    ndvi_values = gf['filter'].values

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

def get_derivatives(gf,sos,pos,eos):
    '''
    get inflection and acceleration points of the time series
    based on the 2nd and 3rd derivation
    '''

    sf = gf.loc[(gf['date'] > sos) & (gf['date'] < eos)]
    if len(sf) > 2:
        sf['dy'] = sf['filter'].diff()
        sf['ddy'] = sf['dy'].diff()
        sf['dddy'] = sf['ddy'].diff()

        sf['inflection'] = np.sign(sf['ddy']).diff().fillna(0).abs() > 0
        inflection_points = sf[sf['inflection']][['date', 'filter']]

        sf['acceleration'] = np.sign(sf['dddy']).diff().fillna(0).abs() > 0
        acceleration_points = sf[sf['acceleration']][['date', 'filter']]

        return inflection_points, acceleration_points

def get_growth_rate(sos_value, pos_value):
    '''
    get the gradient/slope between SOS and POS
    as a proxy of the plant growth rate
    '''

    gradients = np.gradient([sos_value,pos_value])[0]

    return gradients

