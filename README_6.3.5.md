## Figure 6.3.5 — Plan to Reproduce

Reproduce the per‑station total days ≥ 95°F (35°C) in 6‑year periods for the contiguous U.S. (US48) using `processed_data/preprocessed_us_TMAX_data.nc` and plot as bars. 

### Data and assumptions
- **Input**: `processed_data/preprocessed_us_TMAX_data.nc`
  - Variable: `temperature` (°C), absolute temps
  - Coords: `time` (daily), `latitude`, `longitude`, and `land_mask`
  - Region: US48 (24–50°N, −125 to −66°E/W), ocean masked
- **Threshold**: 95°F = 35.0°C
- **Aggregation window**: non-overlapping 6‑year blocks. Start at first full year available (likely 1931); periods will be 1931–36, 1937–42, …
- **“Per station”**: treat each land grid cell as a station; for each period, compute mean exceedance count across all valid land grid cells in the given area (US48 or region). This matches the caption’s “Per Station Total”.

### How to run

Prerequisite: run preprocessing (see `Final/README.md` Step 1) to create `processed_data/preprocessed_us_TMAX_data.nc` (and optionally `processed_data/preprocessed_nh_TMAX_data.nc`). Run from the project root:

```bash
# US (CONUS) multipanel (default thresholds: 95 97.5 100 102.5 105 °F)
python Final/reproduce_6_3_5.py

# Northern Hemisphere (24–50°N)
python Final/reproduce_6_3_5.py --region nh

# Custom thresholds (space-separated list in °F)
python Final/reproduce_6_3_5.py --thresholds-f 95 100 105

# Custom bin size and anchor end year
python Final/reproduce_6_3_5.py --bin-years 6 --end-year 2024

# Custom output path
python Final/reproduce_6_3_5.py --output Figure6.3.5/my_custom.png
```

Options:
- `--region {us,nh}`: region to analyze (default `us`).
- `--thresholds-f ...`: list of Fahrenheit thresholds for the multipanel (default `95 97.5 100 102.5 105`).
- `--bin-years N`: size of non-overlapping periods (default `6`).
- `--end-year YYYY`: last year of the final bin (default `2024`).
- `--output PATH`: output PNG path. If `--region nh` is used with the default output, the script auto-names to `Figure6.3.5/Figure6.3.5_nh_multi.png`.

### Validation checks
- Sanity: US48 bars should be O(60–150) per 6‑yr period depending on start year.
- Unit check: confirm 95°F = 35.0°C and dataset in °C.
- Grid cell weighting: simple unweighted cell average approximates “per station”. If desired, weight by `cos(latitude)` for area weighting; the original per‑station metric likely did not area‑weight.

### File outputs
- US (default): `Figure6.3.5/Figure6.3.5_us_multi.png`
- NH (with `--region nh`): `Figure6.3.5/Figure6.3.5_nh_multi.png`

