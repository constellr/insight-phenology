import os
import geopandas as gpd
from rasterstats import zonal_stats
from shapely.geometry import shape

def get_crs(aoi,utm):
    if aoi.crs != utm.crs:
        aoi.to_crs(utm.crs)

    intersection = gpd.overlay(aoi,utm, how='intersection')
    epsg = intersection['epsg'].unique()[0]
    aoi = aoi.to_crs(epsg)

    return aoi

def aggregation(dir,aoi,gid):
    '''
    Apply zonal statistics / rasterstats based on a single AOI/parcel geometry and
    local raster files (NDVI, LST, etc.)
    '''

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
                stats="mean",
                all_touched=True,
                nodata=0,
                categorical=False,
            )

            mean = statistics[0]['mean']
            id = int(feature['id'])

            rows.append([id, date, mean])

    return rows

def preprocess_df(rows):
    '''
    Gets stats for a parcel
    '''

    df = pd.DataFrame(
        rows,
        columns=[
            "id",
            "date",
            "mean",
        ]
    )

    df['date'] = pd.to_datetime(df['date'])
    #df['doy'] = df['date'].dt.dayofyear
    df = df.sort_values(by='date')

    return df
