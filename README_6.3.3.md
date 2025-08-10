# DOE Figure 6.3.3 Reproduction

This folder contains scripts to reproduce DOE Figure 6.3.3, which shows the number of daily record high and low temperatures for warm and cold seasons in the Continental United States (CONUS).

## Files in This Directory

### Scripts

#### `reproduce_6.3.3.ipynb`
**Purpose**: Interactive notebook for analyzing temperature records and creating the DOE figure.

**What it does**:
- Loads preprocessed temperature data from Berkeley Earth
- Processes warm season (May-Sep) maximum temperatures
- Processes cold season (Nov-Apr) minimum temperatures
- Creates combined visualization matching DOE Figure 6.3.3
- Provides detailed statistics about temperature records

#### `create_gridded_ushcn.py`
**Purpose**: Replace gridded temperature data with nearest USHCN station data.

**What it does**:
- Loads preprocessed gridded TMAX and TMIN data from Berkeley Earth
- Loads USHCN station temperature dataset
- Filters USHCN stations to only include those with data extending to 2024 or later
- For each grid point, finds the nearest USHCN station
- Replaces grid point time series with data from the nearest USHCN station
- Outputs new datasets with USHCN station data mapped to the original grid

#### `analyze_station_coverage.py`
**Purpose**: Analyze and visualize the coverage of temperature stations.

**What it does**:
- Processes station data to assess coverage over time
- Creates visualizations of station density and distribution
- Outputs analysis in `station_coverage_analysis.png`

### Input Data

Required data files in parent directories:
- `../processed_data/preprocessed_us_TMAX_data.nc` (Berkeley Earth TMAX data for CONUS)
- `../processed_data/preprocessed_us_TMIN_data.nc` (Berkeley Earth TMIN data for CONUS)
- `../processed_data/preprocessed_nh_TMAX_data.nc` (Berkeley Earth TMAX data for all longitudes + CONUS latitudes)
- `../processed_data/ushcn_replaced_TMAX_data.nc`  (Berkeley Earth grid, but TMAX data replaced with nearest USHCN station)
- `../processed_data/ushcn_replaced_TMIN_data.nc`  (ditto, for TMIN)

There are flags in the notebook that allow you to pick which input file you want

### Output Files

#### Figures
- `Figure6.3.3_us.png` (US region figure)
- `Figure6.3.3_nh.png` (Northern Hemisphere region figure)
- `station_coverage_analysis.png` (Analysis of station coverage over time)

## How to Run

### Prerequisites

Required Python packages:
```bash
pip install numpy xarray matplotlib pandas scipy jupyter
```

### Create the ushcn data files

```bash
python create_gridded_ushcn.py
```

## Technical Details

### Season Definitions
- **Warm Season**: May 1 - September 30 (153 days)
- **Cold Season**: November 1 - April 30 (181-182 days)

### Record Processing
- Records are calculated per day of year
- For ties (multiple occurrences of max/min temperature), the earliest year is used
- Grid points require valid data for processing
- Results are normalized by number of valid stations

### Data Coverage
- US region (CONUS): 24.5°N-48.5°N, 124.5°W-66.5°W
- Grid resolution: 2° latitude × 2° longitude
- Total grid points: 390 (13 latitude × 30 longitude)
- Valid grid points: ~281 (land points with data)
- For the Berkeley data, there is essentially no missing data for the continental US after 1900
- But there are a lot of missing data points for the 'nh' data, with the number dropping significantly after WW2

### Statistical Output
The analysis provides:
- Total records by season
- Records per station
- Top 5 years for high/low temperature records
- 15-year running averages

## Results

### Top Record Years
**High Temperature Records (Warm Season)**:
1. 2023: 5.75 records per station
2. 1936: 5.68 records per station
3. 1934: 4.05 records per station
4. 2020: 3.56 records per station
5. 1931: 3.29 records per station

**Low Temperature Records (Cold Season)**:
1. 1936: 3.27 records per station
2. 1989: 3.19 records per station
3. 1932: 3.12 records per station
4. 1917: 2.97 records per station
5. 1983: 2.63 records per station

## Troubleshooting

### Common Issues
- **Memory errors**: Datasets are large (~730 MB each)
- **Missing data files**: Check paths in parent directories
- **Invalid seasons**: Verify date ranges in masks
- **NaN values**: Check valid data requirements

### Best Practices
- Run cells in order in notebook
- Monitor memory usage
- Verify season definitions
- Check data quality before processing

## Dependencies

- **numpy**: Array operations
- **xarray**: NetCDF handling
- **matplotlib**: Plotting
- **pandas**: Time series processing
- **jupyter**: Notebook interface
- **scipy**: (Optional) For USHCN processing

## Data Sources

- **Berkeley Earth**: Primary temperature data
- **USHCN**: Optional comparison data
- **DOE**: Reference methodology