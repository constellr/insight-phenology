# insight-phenology

This repo targets the parcel-based assessment of vegetation index AND LST time series.
It uses local dirs and local GeoTIFFs (NDVI and LST).
For real integration it would be better to include connectr-functionality.

## preprocessing
- zonal statistics (per parcel) and spatial aggregation
- making NDVI and LST time series dataframes
  
## phenology
- extraction of time series markers (from derivatives, gradients, etc.) as NDVI-based crop growth markers

## GDD
- extraction of temperature-based crop growth markers (corridors)
- CSV file using literature values for ecological optima (GDD corridors) for crop varieties and grwowht stages

## plotting
- plotting and visualization functions

## canopy
- getting parcel image (clipped NDVI) at or close to Peak of Season
- clustering to derive net area (actual area under crops == canopy density, full crop development ratio)
