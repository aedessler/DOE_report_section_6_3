## DOE Section 6.3 Reproduction: Final Runbook

This folder centralizes the Python code needed to reproduce the figures referenced in `Final/description.txt`:

- Figure 6.3.3: All‑time daily record Highs (warm season) and record Lows (cold season)
- Figure 6.3.5: Days ≥ 95°F (CONUS; bars by 6‑year periods)
- Figure 6.3.6: Heatwave days (≥6‑day runs of daily 90th‑percentile exceedances)
- Global context maps (Figures 3 & 4 equivalent): JJA averages and differences using Berkeley Earth

### Data needed (not moved)

- Berkeley Earth daily NetCDFs in `Berkeley data/`:
  - `Complete_TMAX_Daily_LatLong1_{1900..2020}.nc`
  - `Complete_TMIN_Daily_LatLong1_{1900..2020}.nc`
- For global maps: `global berkeley plots/Complete_TMAX_LatLong1.nc`

Berkeley Earth data can be found [here](https://berkeleyearth.org/data/)

- USHCN inputs for station‑based/gridded comparisons:
  - `DOE reproduction/ushcn_jrc_tmax_250617.0.txt`
  - `DOE reproduction/ushcn_jrc_tmin_250617.0.txt`
  - `DOE reproduction/ushcn_stn_list_250617.txt`

USHCN data available [here](https://www.nsstc.uah.edu/data/ushcn_jrc).

### Outputs used by figures

Preprocessing creates NetCDFs in `processed_data/`:

- `preprocessed_us_TMAX_data.nc` and `preprocessed_us_TMIN_data.nc`
- `preprocessed_nh_TMAX_data.nc` (optional for NH mid‑latitudes analyses)


---

## Step 1 — Preprocess Berkeley Earth daily data (run once)

Converts anomalies to absolute °C, subsets regions, applies land mask, and writes compressed NetCDFs used by all analyses.

Run from the project root:

```bash
python Final/preprocess_data.py --region us --variable TMAX
python Final/preprocess_data.py --region us --variable TMIN

# Optional (for NH mid‑latitudes analyses)
python Final/preprocess_data.py --region nh --variable TMAX
```

This populates `processed_data/` with the files listed above. See `Final/README_processed_data.md` for details.

---

## Step 2 — Figure 6.3.3 (records; US and optional NH)

Inputs: preprocessed files from Step 1. The notebook allows choosing US `TMAX`/`TMIN` or NH `TMAX` data.

```bash
jupyter notebook Final/reproduce_6.3.3.ipynb
```

Follow the notebook prompts; figures are saved to `Figure6.3.3/` (e.g., `Figure6.3.3_us.png`, `Figure6.3.3_nh.png`).

Additional context is in `Final/README_6.3.3.md`.

---

## Step 3 — Figure 6.3.5 (days ≥ 95°F; CONUS)

Uses `processed_data/preprocessed_us_TMAX_data.nc`.

```bash
python Final/reproduce_6_3_5.py
```

Output: `Figure6.3.5/Figure6.3.5_us.png`. See `Final/README_6.3.5.md` for details.

---

## Step 4 — Figure 6.3.6 (heatwave days; US and NH)

Uses `processed_data/preprocessed_us_TMAX_data.nc` (US) or `processed_data/preprocessed_nh_TMAX_data.nc` (NH).

```bash
# US (default)
python Final/reproduce_6_3_6.py

# NH mid‑latitudes
python Final/reproduce_6_3_6.py --region nh

# Adjust minimum run length (default 6)
python Final/reproduce_6_3_6.py --min-run 4
```

Outputs: `Figure6.3.6/Figure6.3.6_us.png`, `Figure6.3.6/Figure6.3.6_nh.png`. See `Final/README_6.3.6.md`.

---

## Step 5 — Global context maps (Figures 3 & 4 equivalents)

These use the separate global file in `global berkeley plots/Complete_TMAX_LatLong1.nc`.

```bash
cd "global berkeley plots"
python berkeley_earth_plot.py
cd -
```

Outputs: `global berkeley plots/berkeley_earth_two_periods.png`, `global berkeley plots/berkeley_earth_difference.png`.

For dependency details, see `Final/README_global_berkeley_plots.md`.

---

## File index (copied into `Final/`)

- `preprocess_data.py` — Berkeley Earth daily → preprocessed region files
- `reproduce_6.3.3.ipynb` — DOE 6.3.3 (records)
- `analyze_station_coverage.py` — Station coverage utilities
- `reproduce_6_3_5.py` — DOE 6.3.5 (≥95°F days; CONUS)
- `reproduce_6_3_6.py` — DOE 6.3.6 (heatwave days; US/NH)
- `berkeley_earth_plot.py` — Global JJA maps and differences (Figures 3 & 4 equivalents)
- `README_6.3.3.md`, `README_6.3.5.md`, `README_6.3.6.md` — Methodology and notes
- `README_processed_data.md` — Processed data documentation
- `requirements_global_berkeley.txt` — optional dependency list for global maps


