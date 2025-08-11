# USHCN Station Density Visualization

This document describes the `plot_ushcn_stations_conus.py` script, which creates visualizations of USHCN (U.S. Historical Climatology Network) station locations and density across the contiguous United States (CONUS).

## Overview

The script generates two types of plots:
1. **Station Locations Map**: A scatter plot showing individual USHCN station locations on a CONUS-focused map
2. **Station Density Map**: A heatmap showing the spatial distribution of station density across CONUS

## Requirements

### Python Dependencies
- `matplotlib` - For plotting and figure generation
- `cartopy` - For geographic projections and map features
- `numpy` - For numerical operations and density calculations
- `pandas` - For reading grid map CSV files (optional)
- `scipy` - For efficient nearest-neighbor calculations (optional, falls back to manual computation)

### Data Files
- **Required**: USHCN station list file (default: `ushcn_stn_list_250617.txt`); this can be downloaded from [here](https://www.nsstc.uah.edu/data/ushcn_jrc/)
- **Optional**: Grid map CSV file for density calculations (columns: `grid_lat`, `grid_lon`)

## Usage

### Basic Usage

```bash
# Generate both station locations and density plots with default settings
python plot_ushcn_stations_conus.py

# Specify custom input file
python plot_ushcn_stations_conus.py --input path/to/stations.txt

# Specify custom output paths
python plot_ushcn_stations_conus.py --output figures/my_stations.png --density-output figures/my_density.png
```

### Advanced Options

```bash
# Use custom grid map for density calculations
python plot_ushcn_stations_conus.py --grid-map gridded_station_map.csv

# Adjust density grid resolution (default: 4.0 degrees)
python plot_ushcn_stations_conus.py --regular-grid-deg 2.0

# Disable area normalization
python plot_ushcn_stations_conus.py --no-area-normalize

# Display plots interactively after saving
python plot_ushcn_stations_conus.py --show
```

### Command Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | `ushcn_stn_list_250617.txt` | Path to USHCN station list text file |
| `--output` | `figures/ushcn_stations_conus.png` | Path for station locations plot |
| `--density-output` | `figures/ushcn_station_density_conus.png` | Path for density plot |
| `--grid-map` | `None` | Optional CSV with grid centers for density calculations |
| `--regular-grid-deg` | `4.0` | Bin size in degrees for density grid |
| `--no-area-normalize` | `False` | Disable cosine(latitude) area normalization |
| `--show` | `False` | Display plots interactively after saving |

## Input File Format

The script expects a tab-delimited text file with the following columns:
```
COOP ID    Lat    Lon    St    Station Name
```

Example:
```
010013    32.45   -86.55 AL    Montgomery
010015    30.69   -88.04 AL    Mobile
...
```

## Output Files

1. **Station Locations Plot** (`ushcn_stations_conus.png`):
   - Red dots representing individual station locations
   - CONUS-focused map with state boundaries and coastlines
   - Lambert Conformal projection for optimal CONUS representation

2. **Station Density Plot** (`ushcn_station_density_conus.png`):
   - Heatmap showing station density per grid cell
   - Red color scale (darker = higher density)
   - Area-adjusted counts (cosine latitude correction)
   - White cells for areas with no stations

## Density Calculation Methods

### Regular Grid Method (Default)
- Divides CONUS into regular latitude/longitude bins
- Counts stations within each bin
- Optionally applies area normalization

### Grid Center Method (with `--grid-map`)
- Maps stations to nearest grid center from provided CSV
- Aggregates center counts into regular grid
- Useful for matching Berkeley Earth grid structure

## Examples

### Generate standard plots
```bash
python plot_ushcn_stations_conus.py
```

### Create high-resolution density map with custom grid
```bash
python plot_ushcn_stations_conus.py \
    --grid-map berkeley_earth_grid.csv \
    --regular-grid-deg 2.0 \
    --density-output figures/high_res_density.png
```

### Quick visualization with custom station data
```bash
python plot_ushcn_stations_conus.py \
    --input my_stations.txt \
    --output figures/custom_stations.png \
    --show
```

## Error Handling

- The script gracefully handles malformed input data
- If density calculation fails, the basic station plot is still generated
- Missing dependencies (like `scipy`) trigger fallback to manual calculations
- Non-existent output directories are automatically created
