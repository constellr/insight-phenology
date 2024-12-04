# roadmap

![image](https://github.com/user-attachments/assets/440085ae-3df4-43fa-84da-a8f7f5767679)

# insight-phenology

This repo targets the parcel-based assessment of vegetation index AND LST time series to:
- get NDVI-based crop growth stages (phenology metrics)
- get GDD-based crop growth stages (GDD corridors based on temperature optima)

![image](https://github.com/user-attachments/assets/d21332b8-6c1d-4df0-adfd-822e3984c9f3)

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
