## Figure 6.3.6 — Heatwave Days

This analysis reproduces the figure showing the 15‑year trailing average of the number of heatwave days per year per station. It supports both the U.S. (CONUS) and Northern Hemisphere (24–50°N) domains and allows customization of the minimum run length for heatwaves.

### Data
- US input: `processed_data/preprocessed_us_TMAX_data.nc`
- NH input: `processed_data/preprocessed_nh_TMAX_data.nc`
- Variables/coords: `temperature` (°C, absolute), `land_mask`, `time` (daily), `latitude`, `longitude`
- Temporal coverage: 1900–present (based on current processed files)

### Methodology
- **Season**: May–September.
- **Thresholds**: For each calendar day, compute the 90th percentile at each grid cell using the full available record in the file.
- **Heatwave day definition**: A day is a heatwave day if it exceeds its daily 90th‑percentile threshold and belongs to a run of at least `min_run` consecutive exceedance days. The metric counts days, not events; e.g., a 12‑day run contributes 12 heatwave days.
- **Regions**:
  - `US` mode: `West` (lon < −105°), `Central‑East` (lon ≥ −105°), and `US48` (all land cells in U.S. domain).
  - `NH` mode: `NH` (all land cells in 24–50°N, all longitudes).
- **Aggregation**: For each calendar year, count heatwave days per grid cell and then average across all land grid cells in the region (unweighted) to produce a per‑station average.
- **Smoothing**: Compute a 15‑year trailing (right‑aligned) average of the annual per‑station series.

### Command‑line Usage
Run from the project root.

Basic (US, default parameters):
```
python Figure6.3.6/reproduce_6_3_6.py
```

Options:
- `--region {us,nh}`: choose domain (default `us`).
- `--min-run N`: minimum consecutive‑day run length for a heatwave (default `6`).
- `--data PATH`: override the auto‑selected input NetCDF.
- `--quick`: enable fast test mode.
- `--quick-years YYYY-YYYY`: year range used in quick mode (default `1990-1999`).
- `--quick-step S`: spatial subsampling step in quick mode (default `6`).

Examples:
```
# Full US with default 6‑day runs
python Figure6.3.6/reproduce_6_3_6.py

# Full US with 4‑day runs
python Figure6.3.6/reproduce_6_3_6.py --min-run 4

# Full NH (24–50°N) with 6‑day runs
python Figure6.3.6/reproduce_6_3_6.py --region nh

# Quick US test (subset in time/space)
python Figure6.3.6/reproduce_6_3_6.py --quick --quick-years 1990-1999 --quick-step 8
```

### Outputs
- US: `Figure6.3.6/Figure6.3.6_us.png`
- NH: `Figure6.3.6/Figure6.3.6_nh.png`

### Assumptions
- Percentiles are computed over the full span available in the file (currently 1900–present).
- Per‑station averaging is unweighted; latitude area‑weighting can be added later if needed.

## Figure 6.3.6 — Heatwave Days

**Objective**: Reproduce the figure showing the 15‑year trailing average of the number of heatwave days per year per station for three series: `US48` (black), `West` (red), and `Central‑East` (green), using `processed_data/preprocessed_us_TMAX_data.nc`.  There is also the ability to analyze a NH mid-latitude data set in the same way.

### Data
- Input: `processed_data/preprocessed_us_TMAX_data.nc`
  - Variable: `temperature` (°C), absolute temps
  - Coords: `time` (daily), `latitude`, `longitude`
  - Ancillary: `land_mask` (>0 means land). Ocean is NaN after masking.
  - Time coverage: expected 1931–present (per preprocessing notes)

### Methodology
- **Season**: May–September inclusive.
- **Thresholds**: For each calendar day, compute the 90th percentile at each grid cell using the full record in the file (1900–present).
- **Heatwave day definition**: A day is a heatwave day if it (a) exceeds its daily 90th‑percentile threshold and (b) belongs to a run of at least `min_run` consecutive exceedance days. The metric counts days, not events; a 12‑day run contributes 12 heatwave days.
- **Regions**:
  - `US` mode: `West` (lon < −105°), `Central‑East` (lon ≥ −105°), and `US48` (all land cells)
  - `NH` mode: `NH` (all land cells in 24–50°N, all longitudes)
- **Aggregation**: For each calendar year, count heatwave days per grid cell and average across land cells in the region (unweighted) → “per‑station” average.
- **Smoothing**: Compute a 15‑year trailing (right‑aligned) average of the annual per‑station series.

### Performance Notes
- Uses `xarray`/`pandas` with dask-friendly chunking.
- Thresholds via `.groupby('time.dayofyear')` are computed per cell over all years.
- Consecutive‑run detection implemented with vectorized rolling + shifts; time dimension is rechunked to avoid dask’s rolling window limits.
- A quick‑test mode reduces years and spatial resolution for fast iteration.

### Notes and Assumptions
- Reference period for percentiles is the full span in the input file (currently 1900–present).
- “Per‑station” means an unweighted average across land grid cells; latitude area‑weighting can be added later if desired.
- Outputs are figures only; no CSVs are written.


