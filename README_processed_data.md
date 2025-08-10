# Processed Data Directory

This directory contains preprocessed temperature datasets used for DOE extreme heat analysis and figure reproduction. All datasets are derived from Berkeley Earth daily temperature data and USHCN (United States Historical Climatology Network) station observations.

## Files Overview

### Berkeley Earth Preprocessed Data

#### `preprocessed_us_TMAX_data.nc` (727 MB)
- **Description**: Preprocessed daily maximum temperature data for the Continental United States (CONUS)
- **Source Data**: Berkeley Earth Complete_TMAX_Daily_LatLong1_*.nc files (1900-2020)
- **Geographic Coverage**: US region (24-50°N, -125 to -66°W)
- **Spatial Resolution**: Reduced by factor of 2 (every 2nd latitude/longitude point)
- **Data Type**: Absolute temperatures (°C) converted from anomalies using climatology
- **Time Period**: 1931-present
- **Created By**: `preprocess_data.py --region us --variable TMAX`

#### `preprocessed_us_TMIN_data.nc` (731 MB)  
- **Description**: Preprocessed daily minimum temperature data for the Continental United States (CONUS)
- **Source Data**: Berkeley Earth Complete_TMIN_Daily_LatLong1_*.nc files (1900-2020)
- **Geographic Coverage**: US region (24-50°N, -125 to -66°W)
- **Spatial Resolution**: Reduced by factor of 2 (every 2nd latitude/longitude point)
- **Data Type**: Absolute temperatures (°C) converted from anomalies using climatology
- **Time Period**: 1931-present
- **Created By**: `preprocess_data.py --region us --variable TMIN`

#### `preprocessed_nh_TMAX_data.nc` (4.1 GB)
- **Description**: Preprocessed daily maximum temperature data for Northern Hemisphere (US latitude range)
- **Source Data**: Berkeley Earth Complete_TMAX_Daily_LatLong1_*.nc files (1900-2020)
- **Geographic Coverage**: Northern Hemisphere region (24-50°N, all longitudes)
- **Spatial Resolution**: Reduced by factor of 2 (every 2nd latitude/longitude point)
- **Data Type**: Absolute temperatures (°C) converted from anomalies using climatology
- **Time Period**: 1931-present
- **Created By**: `preprocess_data.py --region nh --variable TMAX`

#### `preprocessed_nh_TMIN_data.nc` (4.2 GB)
- **Description**: Preprocessed daily minimum temperature data for Northern Hemisphere (US latitude range)
- **Source Data**: Berkeley Earth Complete_TMIN_Daily_LatLong1_*.nc files (1900-2020)
- **Geographic Coverage**: Northern Hemisphere region (24-50°N, all longitudes)
- **Spatial Resolution**: Reduced by factor of 2 (every 2nd latitude/longitude point)
- **Data Type**: Absolute temperatures (°C) converted from anomalies using climatology
- **Time Period**: 1931-present
- **Created By**: `preprocess_data.py --region nh --variable TMIN`

### USHCN Station-Replaced Data

#### `ushcn_replaced_TMAX_data.nc` (702 MB)
- **Description**: US gridded temperature data with Berkeley Earth values replaced by nearest USHCN station observations
- **Source Data**: 
  - `preprocessed_us_TMAX_data.nc` (grid structure)
  - `../USHCN/ushcn_temperature_dataset.nc` (station observations)
- **Processing**: Each grid point replaced with data from nearest USHCN station (filtered to stations ending in 2024+)
- **Station Coverage**: ~257 unique USHCN stations covering 390 grid points
- **Geographic Coverage**: US region (24-50°N, -125 to -66°W)
- **Data Type**: Absolute temperatures (°C) from quality-controlled station observations
- **Created By**: `Figure6.3.3/create_gridded_ushcn.py`

#### `ushcn_replaced_TMIN_data.nc` (704 MB)
- **Description**: US gridded temperature data with Berkeley Earth values replaced by nearest USHCN station observations
- **Source Data**: 
  - `preprocessed_us_TMIN_data.nc` (grid structure)
  - `../USHCN/ushcn_temperature_dataset.nc` (station observations)
- **Processing**: Each grid point replaced with data from nearest USHCN station (filtered to stations ending in 2024+)
- **Station Coverage**: ~257 unique USHCN stations covering 390 grid points
- **Geographic Coverage**: US region (24-50°N, -125 to -66°W)
- **Data Type**: Absolute temperatures (°C) from quality-controlled station observations
- **Created By**: `Figure6.3.3/create_gridded_ushcn.py`

## Data Processing Workflow

### Step 1: Berkeley Earth Preprocessing (`preprocess_data.py`)

1. **Input Processing**: Reads Berkeley Earth NetCDF files from `Berkeley data/` directory
2. **Time Coordinate Fixing**: Converts year/month/day to proper datetime64 coordinates
3. **Regional Subsetting**: 
   - US region: 24-50°N, -125 to -66°W
   - NH region: 24-50°N, all longitudes
4. **Spatial Reduction**: Takes every 2nd latitude/longitude point for computational efficiency
5. **Land Masking**: Applies land mask to focus on terrestrial areas only
6. **Temperature Conversion**: Converts anomalies to absolute temperatures using daily climatology
7. **Compression**: Saves with zlib compression (complevel=6) for storage efficiency

### Step 2: USHCN Station Replacement (`Figure6.3.3/create_gridded_ushcn.py`)

1. **Station Filtering**: Filters 1,218 USHCN stations to ~785 stations with data extending to 2024+
2. **Nearest Neighbor Mapping**: For each grid point, finds nearest USHCN station using Euclidean distance
3. **Data Replacement**: Replaces Berkeley Earth gridded values with station observations
4. **Time Interpolation**: Handles temporal alignment between gridded and station data
5. **Metadata Preservation**: Maintains original grid structure and coordinates
6. **Quality Control**: Uses only quality-controlled USHCN observations

## Usage Notes

1. **Coordinate System**: All files use standard latitude/longitude coordinates
2. **Time Dimension**: Daily time series with datetime64[ns] encoding
3. **Missing Data**: Represented as NaN values
4. **Memory Optimization**: Files use chunking and compression for efficient access
5. **Land Focus**: Ocean points are masked out (NaN) in all datasets

## File Dependencies

```
Berkeley data/Complete_T{MAX,MIN}_Daily_LatLong1_*.nc
    ↓ (preprocess_data.py)
preprocessed_{us,nh}_T{MAX,MIN}_data.nc
    ↓ (create_gridded_ushcn.py)
ushcn_replaced_T{MAX,MIN}_data.nc
```
