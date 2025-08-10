## Figure 6.3.5 — Plan to Reproduce

Goal (v1): Reproduce the per‑station total days ≥ 95°F (35°C) in 6‑year periods for the contiguous U.S. (US48) using `processed_data/preprocessed_us_TMAX_data.nc` and plot as bars. Regional lines will be added in a subsequent iteration.

### Data and assumptions
- **Input**: `processed_data/preprocessed_us_TMAX_data.nc`
  - Variable: `temperature` (°C), absolute temps
  - Coords: `time` (daily), `latitude`, `longitude`, and `land_mask`
  - Region: US48 (24–50°N, −125 to −66°E/W), ocean masked
- **Threshold**: 95°F = 35.0°C
- **Aggregation window**: non-overlapping 6‑year blocks. Start at first full year available (likely 1931); periods will be 1931–36, 1937–42, …
- **“Per station”**: treat each land grid cell as a station; for each period, compute mean exceedance count across all valid land grid cells in the given area (US48 or region). This matches the caption’s “Per Station Total”.

### High-level steps (v1: CONUS only)
1) Load dataset with xarray/dask
- Use chunking on `time` and spatial dims for performance.

2) Build a boolean exceedance mask
- Convert the fixed threshold to °C (35.0).
- `is_hot = ds.temperature >= 35.0`

3) Define 6‑year bins
- Create a `bin_start_year` coordinate from `time.dt.year`:
  - `start = ds.time.dt.year.min().item()`
  - `bin_start = ((year - start) // 6) * 6 + start`
- Group by `bin_start`.

4) Count exceedance days per grid cell per 6‑year period
- `counts_cell = is_hot.groupby(bin_start).sum(dim='time')`

5) Compute “per‑station” totals for US48
- For each period: average over land grid cells: `us48_series = counts_cell.mean(dim=('latitude','longitude'), skipna=True)`
- This yields a 1D series indexed by `bin_start` for the bars.

6) Plot
- Bars: US48 per‑station totals (`us48_series`) for each 6‑year period.
- X‑axis ticks: label as `YYYY–YY` ranges using `bin_start` plus `+5` end year.
- Y‑axis: “Per Station Total of 95°F and greater days per 6‑yr period”.
- Save to `Figure6.3.5/Figure6.3.5_us.png`.

### Minimal Python outline (single-machine; adjust chunks to your RAM)
```python
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt

ds = xr.open_dataset('processed_data/preprocessed_us_TMAX_data.nc',
                     chunks={'time': 365, 'latitude': 'auto', 'longitude': 'auto'})

is_hot = (ds.temperature >= 35.0)
years = is_hot.time.dt.year
start_year = int(years.min())
bin_start = ((years - start_year) // 6) * 6 + start_year
counts_cell = is_hot.groupby(bin_start).sum(dim='time')

# US48 average (land already masked in preprocessing)
us48_series = counts_cell.mean(dim=('latitude','longitude'), skipna=True)

# Plot
fig, ax = plt.subplots(figsize=(11,6))

# Bars for US48
starts = us48_series.bin_start.values
ax.bar(starts, us48_series.values, width=5.5, color='salmon', edgecolor='brown', label='US48')

ax.set_xlabel('Six-year periods')
ax.set_ylabel('Per station total days ≥95°F per 6-yr period')
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig('Figure6.3.5/Figure6.3.5_us.png', dpi=200)
```

### Validation checks
- Sanity: US48 bars should be O(60–150) per 6‑yr period depending on start year.
- Unit check: confirm 95°F = 35.0°C and dataset in °C.
- Grid cell weighting: simple unweighted cell average approximates “per station”. If desired, weight by `cos(latitude)` for area weighting; the original per‑station metric likely did not area‑weight.

### File outputs
- Figure: `Figure6.3.5/Figure6.3.5_us.png`
- Optional CSV of series: `Figure6.3.5/Figure6.3.5_counts.csv` with columns `[bin_start, US48]`.

### Future work — Regions (v2)
- Add nine‑region time series (lines) using NOAA 9 climate regions:
  - PacNW: WA, OR, ID; PacSW: CA, NV; 4Crns: AZ, CO, NM, UT; NPIns: MT, ND, SD, WY, NE; SPIns: KS, OK, TX; UMidW: IA, MN, WI, MI; OhVly: IL, IN, KY, MO, OH, TN, WV; SoEst: AL, FL, GA, NC, SC, VA; NoEst: CT, DE, ME, MD, MA, NH, NJ, NY, PA, RI, VT, DC.
- Region masking approach: merge state polygons via `geopandas` and rasterize to the `(latitude, longitude)` grid with `rasterio.features.rasterize` (fallback: approximate lat/lon boxes).
- Compute per‑region “per‑station” totals as in steps 4–5, then plot as lines.

### Next steps
- Add a runnable script `Figure6.3.5/reproduce_6_3_5.py` implementing the v1 outline above,
- Then implement the region masking and plotting per the Future work section.


