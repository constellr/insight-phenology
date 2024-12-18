# roadmap

![image](https://github.com/user-attachments/assets/28abe0cf-4442-4fb2-8f6a-1fd7266eeb77)

# insight-phenology

This repo provides the parcel-based derivation of vegetation statistics in analysis-ready format (tabular data/CSV).

- get NDVI-based crop growth stages (phenology metrics)
- get GDD-based crop growth stages (GDD corridors based on temperature optima)
- get LST and NDVI time series features
- get canopy metrics

![image](https://github.com/user-attachments/assets/9b47356c-3431-429b-86ba-1c248509e04c)
![image](https://github.com/user-attachments/assets/d808f185-9df5-46aa-a47c-c8a9f9343d6f)

## prerequisites
- local NDVI tiffs
- local parcel-clipped NDVI tiffs
- LST tiffs
- UTM geojson
- parcel (AOI) geojson

## main parameters (in main.py)
* "country": "USA",  # Country for analysis ("India", "USA", "Brazil", "Germany")
* "crop": "corn",  # Target crop ("sugarcane", "wheat", "corn", "rice")
* "variety": "Dent corn",  # Crop variety (specific strain or type)
* "startdate": "2023-04-01",  # Start date of the analysis (YYYY-MM-DD)
* "enddate": "2023-10-01",  # End date of the analysis (YYYY-MM-DD)
* "slicing": False,  # Enable/disable data slicing (Boolean)
* "plotting": True,  # Enable/disable plotting of results (Boolean),
* "strategy": "ALL", # Select output statistics: ("ALL", "phenology", "summary", "timeseries")
* "resampling": "None", # Select resampling for sequential features ("None", "monthly", "weekly")

## preprocessing
- zonal statistics (per parcel) and spatial aggregation
- making NDVI and LST time series dataframes
  
## phenology
- extraction of time series markers (from derivatives, gradients, etc.) as NDVI-based crop growth markers

## GDD
- extraction of temperature-based crop growth markers (corridors)
- CSV file using literature values for ecological optima (GDD corridors) for crop varieties and grwowht stages

## feature engineering
- prepration of CSV outputs

## plotting
- plotting and visualization functions

## canopy
- getting parcel image (clipped NDVI) at or close to Peak of Season
- clustering to derive net area (actual area under crops == canopy density, full crop development ratio)
