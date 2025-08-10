import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd

# Load the USHCN temperature dataset
ds = xr.open_dataset('USHCN/ushcn_temperature_dataset.nc')

# Extract TMAX data
tmax = ds['TMAX']

# Get number of stations
n_stations = len(ds.station_id)

# Group by year
yearly_data = tmax.groupby('date.year')

# Initialize arrays for results
years = sorted(list(yearly_data.groups.keys()))
fractions = []

# For each year, calculate fraction of stations with 300+ valid measurements
for year in years:
    year_data = yearly_data[year]
    # Count valid measurements per station
    valid_counts = (~np.isnan(year_data)).sum(dim='date')
    # Calculate fraction of stations with 300+ measurements
    fraction = (valid_counts >= 300).sum().item() / n_stations
    fractions.append(fraction)

# Create the figure
plt.figure(figsize=(12, 6))
plt.plot(years, fractions, '-o', markersize=3)
plt.grid(True, alpha=0.3)
plt.xlabel('Year')
plt.ylabel('Fraction of Stations with 300+ Valid Measurements')
plt.title('USHCN TMAX Data Coverage Over Time')

# Add horizontal line at 1.0 for reference
plt.axhline(y=1.0, color='r', linestyle='--', alpha=0.3)

# Adjust y-axis to show full range from 0 to 1
plt.ylim(-0.05, 1.05)

# Save the figure
#plt.savefig('station_coverage_analysis.png', dpi=300, bbox_inches='tight')
#plt.close()
plt.show()

# Print some summary statistics
print(f"Analysis complete. Results saved to 'station_coverage_analysis.png'")
print(f"Time period covered: {min(years)} to {max(years)}")
print(f"Average fraction of stations with 300+ measurements: {np.mean(fractions):.3f}")
print(f"Minimum fraction: {min(fractions):.3f} (Year: {years[np.argmin(fractions)]})")
print(f"Maximum fraction: {max(fractions):.3f} (Year: {years[np.argmax(fractions)]})")

# Calculate average fractions for specific periods using pandas
fraction_series = pd.Series(fractions, index=years)

# 1930-1939 period
avg_1930s = fraction_series.loc[1930:1939].mean()
print(f"Average fraction for 1930-1939: {avg_1930s:.3f}")

# 2015-2024 period
avg_2015_2024 = fraction_series.loc[2015:2024].mean()
print(f"Average fraction for 2015-2024: {avg_2015_2024:.3f}")
