"""
Data Preprocessing Script for EPA Figure 11 Analysis

This script handles Step 1 of the two-step approach:
1. Read in all NetCDF data files for 1931-present
2. Cut out the specified region (US or Northern Hemisphere in US latitude range)
3. Reduce data by factor of 4 (every 2nd lat/lon point)
4. Add climatology to convert anomalies to absolute temperatures
5. Write out concatenated dataset to new NetCDF file in /processed_data/ directory

Usage:
    python preprocess_data.py --region us --variable TMAX   # Process US region TMAX data (default)
    python preprocess_data.py --region nh --variable TMIN   # Process Northern Hemisphere TMIN data
    python preprocess_data.py --region us --variable TMIN   # Process US region TMIN data
"""

import numpy as np
import xarray as xr
from pathlib import Path
import warnings
import os
import dask
import argparse
warnings.filterwarnings('ignore')

def preprocess_time_coords(ds):
    """Preprocess function to fix time coordinates for each file"""
    # Create proper time coordinate from year/month/day
    dates = []
    for i in range(len(ds.year)):
        year = int(ds.year[i])
        month = int(ds.month[i])
        day = int(ds.day[i])
        dates.append(f"{year:04d}-{month:02d}-{day:02d}")
    
    # Assign proper time coordinate
    ds = ds.assign_coords(time=('time', dates))
    ds['time'] = ds.time.astype('datetime64[ns]')
    
    return ds

def process_single_file(file_path, output_dir, region='us', variable='TMAX'):
    """Process a single NetCDF file: load, subset region, reduce by factor 9, add climatology"""
    print(f"Processing: {Path(file_path).name}")
    
    # Load the file
    ds = xr.open_dataset(file_path, chunks={'time': 365, 'latitude': 50, 'longitude': 50})
    ds_processed = preprocess_time_coords(ds)
    
    # Subset to specified region
    if region == 'us':
        regional_data = subset_us_region(ds_processed)
    elif region == 'nh':
        regional_data = subset_nh_region(ds_processed)
    else:
        raise ValueError(f"Unknown region: {region}. Use 'us' or 'nh'")
    
    # Convert temperature anomalies to absolute temperatures
    regional_data = convert_to_absolute_temperatures(regional_data, variable)
    
    # Create output filename
    input_name = Path(file_path).stem
    output_file = output_dir / f"processed_{region}_{variable}_{input_name}.nc"
    
    # Write processed file with compression
    print(f"Writing: {output_file.name}")
    encoding = {
        'temperature': {'zlib': True, 'complevel': 6},
        'land_mask': {'zlib': True, 'complevel': 6}
    }
    
    regional_data.to_netcdf(output_file, encoding=encoding)
    print(f"Saved: {output_file}")
    
    return output_file

def process_all_files_sequentially(data_dir, output_dir, region='us', variable='TMAX'):
    """Process all files sequentially, creating individual processed files"""
    # All required files for analysis
    data_files = [f'{data_dir}/Complete_{variable}_Daily_LatLong1_{decade}.nc' 
                  for decade in [1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]]
    
    # Filter to existing files
    valid_files = [f for f in data_files if Path(f).exists()]
    
    if not valid_files:
        raise FileNotFoundError(f"No {variable} data files found")
    
    print(f"Processing {len(valid_files)} {variable} files sequentially for {region.upper()} region...")
    
    processed_files = []
    for file_path in valid_files:
        processed_file = process_single_file(file_path, output_dir, region, variable)
        processed_files.append(processed_file)
    
    return processed_files

def concatenate_processed_files(processed_files, output_file, region='us', variable='TMAX'):
    """Concatenate all processed files using dask and write final dataset"""
    print(f"Concatenating {len(processed_files)} processed {variable} files using dask...")
    
    # Open all processed files with dask
    datasets = []
    for file_path in processed_files:
        print(f"Opening: {Path(file_path).name}")
        ds = xr.open_dataset(file_path, chunks={'time': 365, 'latitude': 'auto', 'longitude': 'auto'})
        datasets.append(ds)
    
    print("Concatenating datasets...")
    combined = xr.concat(datasets, dim='time')
    
    print("Sorting time coordinates...")
    analysis_data = combined.sortby('time')
    
    # Set region-specific attributes
    if region == 'us':
        title = f'Preprocessed US {variable} Temperature Data for EPA Figure 11 Analysis'
        description = f'Berkeley Earth daily {variable.lower()} temperature data, US subset, reduced by factor of 9, absolute temperatures'
        geographic_subset = 'US region (24-50°N, -125 to -66°W)'
    elif region == 'nh':
        title = f'Preprocessed Northern Hemisphere {variable} Temperature Data for EPA Figure 11 Analysis'
        description = f'Berkeley Earth daily {variable.lower()} temperature data, NH subset (US latitude range), reduced by factor of 9, absolute temperatures'
        geographic_subset = 'Northern Hemisphere region (24-50°N, all longitudes)'
    
    # Add global attributes for documentation
    analysis_data.attrs.update({
        'title': title,
        'description': description,
        'geographic_subset': geographic_subset,
        'data_reduction': 'Every 2nd latitude and longitude point',
        'temperature_conversion': 'Anomalies converted to absolute temperatures using climatology',
        'created_by': 'preprocess_data.py',
        'region': region.upper(),
        'variable': variable
    })
    
    # Write final concatenated file with compression
    print(f"Writing final concatenated file: {output_file}")
    encoding = {
        'temperature': {'zlib': True, 'complevel': 6},
        'land_mask': {'zlib': True, 'complevel': 6}
    }
    
    analysis_data.to_netcdf(output_file, encoding=encoding)
    print(f"Final dataset shape: {analysis_data.temperature.shape}")
    
    return analysis_data

def subset_us_region(data):
    """Extract U.S. region from global grid with data reduction"""
    # Approximate U.S. bounding box
    lat_min, lat_max = 24, 50
    lon_min, lon_max = -125, -66
    
    # Data uses -180 to 180 longitude system
    us_data = data.sel(
        latitude=slice(lat_min, lat_max),
        longitude=slice(lon_min, lon_max)
    )
    
    # Apply data reduction: take every 3rd latitude and longitude for faster processing
    print("Applying data reduction (every 3rd lat/lon)...")
    us_data = us_data.isel(
        latitude=slice(None, None, 2),
        longitude=slice(None, None, 2)
    )
    
    # Apply land mask to focus on land points only
    land_mask = us_data.land_mask > 0
    us_data = us_data.where(land_mask)
    
    print(f"U.S. subset (reduced): {us_data.latitude.size} lat × {us_data.longitude.size} lon grid points")
    print(f"Land points: {land_mask.sum().values} grid cells")
    return us_data

def subset_nh_region(data):
    """Extract Northern Hemisphere region in US latitude range from global grid with data reduction"""
    # Use same latitude range as US but include all longitudes
    lat_min, lat_max = 24, 50
    
    # Include all longitudes for Northern Hemisphere
    nh_data = data.sel(
        latitude=slice(lat_min, lat_max)
    )
    
    # Apply data reduction: take every 2nd latitude and longitude for faster processing
    print("Applying data reduction (every 2nd lat/lon)...")
    nh_data = nh_data.isel(
        latitude=slice(None, None, 2),
        longitude=slice(None, None, 2)
    )
    
    # Apply land mask to focus on land points only
    land_mask = nh_data.land_mask > 0
    nh_data = nh_data.where(land_mask)
    
    print(f"NH subset (reduced): {nh_data.latitude.size} lat × {nh_data.longitude.size} lon grid points")
    print(f"Land points: {land_mask.sum().values} grid cells")
    return nh_data

def convert_to_absolute_temperatures(data, variable='TMAX'):
    """Convert temperature anomalies to absolute temperatures using climatology"""
    import pandas as pd
    
    print("Adding climatology to convert anomalies to absolute temperatures...")
    
    # Get temperature anomalies and climatology
    temp_anomalies = data['temperature']
    climatology = data['climatology']
    
    # Create day-of-year coordinate for temperature data
    time_coords = pd.to_datetime(temp_anomalies.time.values)
    day_of_year = time_coords.dayofyear - 1  # Convert to 0-364 to match day_number
    
    # Handle leap years - map Feb 29 (day 60) to Feb 28 (day 59)
    day_of_year = np.where(day_of_year > 59, 
                          np.minimum(day_of_year - 1, 364), 
                          day_of_year)
    
    # Select climatology values for each day more efficiently
    daily_climatology = climatology.isel(day_number=day_of_year)
    
    # Add climatology to anomalies to get absolute temperatures
    # Use numpy broadcasting for efficiency
    absolute_temp_values = temp_anomalies.values + daily_climatology.values
    
    # Create new temperature DataArray with absolute values
    absolute_temps = xr.DataArray(
        absolute_temp_values,
        coords=temp_anomalies.coords,
        dims=temp_anomalies.dims,
        attrs={
            'long_name': f'Absolute Daily {variable} Temperature',
            'units': 'degree C'
        }
    )
    
    # Create new dataset with absolute temperatures
    data_absolute = data.copy(deep=True)
    data_absolute = data_absolute.drop_vars(['climatology'])  # Remove to save memory
    data_absolute['temperature'] = absolute_temps
    
    # Print some validation statistics
    sample_temps = absolute_temps.isel(time=slice(0, 100)).values
    valid_temps = sample_temps[~np.isnan(sample_temps)]
    if len(valid_temps) > 0:
        print(f"Sample absolute temperature range: {valid_temps.min():.1f}°C to {valid_temps.max():.1f}°C")
        print(f"Sample absolute temperature mean: {valid_temps.mean():.1f}°C")
    
    return data_absolute

def main():
    """Main preprocessing workflow"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Preprocess temperature data for EPA Figure 11 analysis')
    parser.add_argument('--region', choices=['us', 'nh'], default='us',
                       help='Region to process: "us" for United States, "nh" for Northern Hemisphere (same latitude range as US)')
    parser.add_argument('--variable', choices=['TMAX', 'TMIN'], default='TMAX',
                       help='Temperature variable to process: "TMAX" for maximum temperature, "TMIN" for minimum temperature')
    
    args = parser.parse_args()
    region = args.region
    variable = args.variable
    
    print(f"Starting data preprocessing for EPA Figure 11 analysis ({region.upper()} region, {variable} variable)...")
    
    # Create output directory
    output_dir = Path('processed_data')
    output_dir.mkdir(exist_ok=True)
    print(f"Created output directory: {output_dir}")
    
    data_dir = 'Berkeley data'
    
    # Step 1: Process each file individually
    print(f"\n=== STEP 1: Processing individual {variable} files for {region.upper()} region ===")
    processed_files = process_all_files_sequentially(data_dir, output_dir, region, variable)
    
    # Step 2: Concatenate all processed files using dask
    print(f"\n=== STEP 2: Concatenating {len(processed_files)} processed {variable} files ===")
    final_output_file = output_dir / f'preprocessed_{region}_{variable}_data.nc'
    final_data = concatenate_processed_files(processed_files, final_output_file, region, variable)
    
    # Print summary statistics
    print(f"\n=== PREPROCESSING SUMMARY ===")
    print(f"Region: {region.upper()}")
    print(f"Variable: {variable}")
    print(f"Input data period: 1931-present")
    print(f"Final dataset shape: {final_data.temperature.shape}")
    print(f"Geographic grid: {final_data.latitude.size} lat × {final_data.longitude.size} lon")
    print(f"Land grid points: {(final_data.land_mask > 0).sum().values}")
    print(f"Individual processed files: {len(processed_files)}")
    print(f"Final concatenated file: {final_output_file}")
    print(f"Final file size: {final_output_file.stat().st_size / (1024**2):.1f} MB")
    print("Preprocessing complete!")

if __name__ == "__main__":
    main()