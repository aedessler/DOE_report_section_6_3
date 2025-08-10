import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.util import add_cyclic_point
import argparse

def load_berkeley_data(filename):
    """Load Berkeley Earth temperature data from NetCDF file using xarray."""
    # Open the dataset with xarray
    ds = xr.open_dataset(filename)
    ds['time'] = pd.date_range(start='1850-01-01', periods=len(ds['time']), freq='ME')

    # Extract the temperature variable
    temp_da = ds['temperature']
    
    print("Time coordinate info:")
    print(f"Time coordinate values (first 5): {temp_da.time.values[:5]}")
    print(f"Time coordinate values (last 5): {temp_da.time.values[-5:]}")
    print("Note: Time is now in proper datetime format")
    
    return temp_da

def get_time_period_data(temp_da, start_year, end_year):
    """Extract summer (JJA) data for a specific time period using xarray."""
    # First select data for the time period
    if start_year == end_year:
        # If same year, select that year's data
        period_data = temp_da.sel(time=slice(f"{start_year}-01-01", f"{start_year}-12-31"))
    else:
        # For a range of years, select the period
        period_data = temp_da.sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
    
    # Filter for summer months (June, July, August) using datetime accessor
    summer_data = period_data.where(period_data.time.dt.month.isin([6, 7, 8]), drop=True)
    
    # Calculate mean over time dimension (this will average all summer months)
    if start_year != end_year or len(summer_data.time) > 1:
        summer_data = summer_data.mean(dim='time')
    
    print(f"Summer data shape: {summer_data.shape}")
    print(f"Time range: {start_year}-{end_year}, filtered for JJA months")

    return summer_data

def plot_berkeley_earth_maps(start_year=2015, end_year=2024):
    """Create the Berkeley Earth temperature anomaly plots using xarray."""
    
    # Load data
    print("Loading Berkeley Earth data...")
    temp_da = load_berkeley_data('Complete_TMAX_LatLong1.nc')
    
    # Extract data for the two periods
    print("Processing historical period data...")
    data_historical = get_time_period_data(temp_da, 1930, 1939)
    print(f"Processing {start_year}-{end_year} data...")
    data_recent = get_time_period_data(temp_da, start_year, end_year)
    
    # Calculate the difference
    print("Calculating difference...")
    data_difference = data_recent - data_historical
    
    # Create two separate figures
    # Figure 1: Two periods in a column
    fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 14), 
                                    subplot_kw={'projection': ccrs.Mollweide()})
    
    # Figure 2: Difference plot
    fig2, ax3 = plt.subplots(1, 1, figsize=(12, 8), 
                             subplot_kw={'projection': ccrs.Mollweide()})
    
    # Use RdBu_r colormap
    cmap = 'RdBu_r'
    
    # Set colorbar limits
    vmin, vmax = -2.0, 2.0
    levels = np.linspace(vmin, vmax, 9)
    
    # Add cyclic point to longitude for proper plotting
    # Extract numpy arrays from xarray DataArrays for plotting
    lons = data_historical.longitude.values
    lats = data_historical.latitude.values
    
    data_historical_cyclic, lons_cyclic = add_cyclic_point(data_historical.values, coord=lons)
    data_recent_cyclic, _ = add_cyclic_point(data_recent.values, coord=lons)
    data_difference_cyclic, _ = add_cyclic_point(data_difference.values, coord=lons)
    
    # Plot historical period data
    print("Plotting historical period map...")
    im1 = ax1.pcolormesh(lons_cyclic, lats, data_historical_cyclic, 
                         cmap=cmap, vmin=vmin, vmax=vmax,
                         transform=ccrs.PlateCarree())
    
    # Add coastlines only
    ax1.add_feature(cfeature.COASTLINE, linewidth=0.5, color='black')
    ax1.set_title('Berkeley Earth Summer (JJA) Average Daily High Temperatures\nHistorical Period (1930-1939)', 
                  fontsize=16, fontweight='bold', pad=20)
    
    # Plot recent period data
    print(f"Plotting {start_year}-{end_year} map...")
    im2 = ax2.pcolormesh(lons_cyclic, lats, data_recent_cyclic, 
                         cmap=cmap, vmin=vmin, vmax=vmax,
                         transform=ccrs.PlateCarree())
    
    # Add coastlines only
    ax2.add_feature(cfeature.COASTLINE, linewidth=0.5, color='black')
    ax2.set_title(f'Berkeley Earth Summer (JJA) Average Daily High Temperatures\nRecent Period ({start_year}-{end_year})', 
                  fontsize=16, fontweight='bold', pad=20)
    
    # Plot difference data
    print("Plotting difference map...")
    im3 = ax3.pcolormesh(lons_cyclic, lats, data_difference_cyclic, 
                         cmap=cmap, vmin=vmin, vmax=vmax,
                         transform=ccrs.PlateCarree())
    
    # Add coastlines only
    ax3.add_feature(cfeature.COASTLINE, linewidth=0.5, color='black')
    ax3.set_title(f'Difference in Summer (JJA) Average Daily High Temperatures\nbetween {start_year}-{end_year} and Historical Period (1930-1939)', 
                  fontsize=16, fontweight='bold', pad=20)
    
    # Add colorbar for first figure (two periods)
    cbar_ax1 = fig1.add_axes([0.92, 0.15, 0.02, 0.7])
    cbar1 = fig1.colorbar(im2, cax=cbar_ax1, orientation='vertical')
    cbar1.set_label('Temperature Anomaly (°C) relative to 1951-1980', 
                    fontsize=14, fontweight='bold')
    cbar1.set_ticks(levels)
    cbar1.set_ticklabels([f'{level:.1f}' for level in levels])
    cbar1.ax.tick_params(labelsize=12)
    
    # Adjust layout for first figure - reduce spacing between panels
    fig1.tight_layout()
    fig1.subplots_adjust(right=0.88, hspace=0.02, top=0.95, bottom=0.05)
    
    # Add colorbar for second figure (difference) - underneath
    cbar_ax2 = fig2.add_axes([0.15, 0.08, 0.7, 0.03])
    cbar2 = fig2.colorbar(im3, cax=cbar_ax2, orientation='horizontal')
    cbar2.set_label('Temperature Difference (°C)', 
                    fontsize=14, fontweight='bold')
    cbar2.set_ticks(levels)
    cbar2.set_ticklabels([f'{level:.1f}' for level in levels])
    cbar2.ax.tick_params(labelsize=12)
    
    # Adjust layout for second figure - reduce spacing
    fig2.tight_layout()
    fig2.subplots_adjust(bottom=0.12)
    
    # Save the plots
    fig1.savefig('berkeley_earth_two_periods.png', 
                 dpi=300, bbox_inches='tight')
    fig2.savefig('berkeley_earth_difference.png', 
                 dpi=300, bbox_inches='tight')
    print("Plots saved as 'berkeley_earth_two_periods.png' and 'berkeley_earth_difference.png'")
    
    # Show the plots
    plt.show()

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Create Berkeley Earth temperature anomaly plots')
    parser.add_argument('--start-year', type=int, default=2015, 
                       help='Start year for the recent period (default: 2015)')
    parser.add_argument('--end-year', type=int, default=2024, 
                       help='End year for the recent period (default: 2024)')
    
    args = parser.parse_args()
    
    # Validate year range
    if args.start_year >= args.end_year:
        print("Error: Start year must be less than end year")
        exit(1)
    
    if args.start_year < 1850 or args.end_year > 2024:
        print("Error: Year range must be between 1850 and 2024")
        exit(1)
    
    # Create the plots
    plot_berkeley_earth_maps(args.start_year, args.end_year) 