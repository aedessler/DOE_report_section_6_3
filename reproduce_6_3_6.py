"""
Reproduce Figure 6.3.6: 15-year trailing average of heatwave days per year

Method (per README):
- Season: May–September
- Thresholds: For each calendar day, compute 90th percentile over the full record
- Heatwave day: Exceedance day that lies within a run of ≥6 consecutive exceedance days
- Regions: West (< −105°), Central‑East (≥ −105°), US48 (all land)
- Output: Figure saved to Figure6.3.6/Figure6.3.6_us.png

Performance:
- Uses xarray/dask for parallel computation where available
- Vectorized consecutive‑run detection using rolling windows and shifts (no Python loops over grid)
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Dict, Tuple
import argparse

import numpy as np
import pandas as pd
import xarray as xr

# Optional dask configuration for parallel execution
try:
    import dask  # type: ignore

    # Prefer multi-threaded scheduler for array ops
    dask.config.set(scheduler="threads")
except Exception:  # pragma: no cover - dask not strictly required to run
    dask = None  # type: ignore

import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")


# ----------------------------- Data Loading ---------------------------------

def load_temperature_data(netcdf_path: Path) -> xr.DataArray:
    """Load preprocessed TMAX dataset and return land-only temperatures.

    Parameters
    ----------
    netcdf_path: Path
        Path to `processed_data/preprocessed_us_TMAX_data.nc`.

    Returns
    -------
    xr.DataArray
        DataArray of absolute temperatures (°C) over land with dims
        (time, latitude, longitude).
    """
    print(f"Loading dataset: {netcdf_path}")
    # Chunk for parallelism and memory efficiency
    ds = xr.open_dataset(
        netcdf_path,
        chunks={"time": 365, "latitude": "auto", "longitude": "auto"},
    )

    if "temperature" not in ds:
        raise KeyError("Dataset missing variable 'temperature'")
    if "land_mask" not in ds:
        raise KeyError("Dataset missing variable 'land_mask'")

    land_mask = (ds["land_mask"] > 0).isel(time=0)
    temp_land = ds["temperature"].where(land_mask)

    tmin = pd.to_datetime(temp_land.time.values).min()
    tmax = pd.to_datetime(temp_land.time.values).max()
    n_land = int(land_mask.sum().compute() if temp_land.chunks else land_mask.sum())
    print(f"Data time span: {tmin.date()} → {tmax.date()} | Land grid cells: {n_land}")

    return temp_land


# ----------------------------- Region Masks ---------------------------------

def build_region_masks(temp_data: xr.DataArray, region: str) -> Dict[str, xr.DataArray]:
    """Create boolean masks for regions.

    - For `us`: returns `West`, `Central-East`, and `US48` using −105° split.
    - For `nh`: returns a single `NH` mask covering all land points in the file.
    """
    valid_land = xr.where(~np.isnan(temp_data.isel(time=0)), True, False)

    if region == "us":
        lon = temp_data["longitude"]
        west_mask = xr.where(lon < -105.0, True, False)
        central_east_mask = xr.where(lon >= -105.0, True, False)
        us48_mask = xr.ones_like(west_mask, dtype=bool)

        # Broadcast to (latitude, longitude)
        base = temp_data.isel(time=0, drop=True) * 0 + 1
        west_mask2d = xr.broadcast(base, west_mask)[1].astype(bool)
        central_east_mask2d = xr.broadcast(base, central_east_mask)[1].astype(bool)
        us48_mask2d = xr.broadcast(base, us48_mask)[1].astype(bool)

        west_mask2d = west_mask2d & valid_land
        central_east_mask2d = central_east_mask2d & valid_land
        us48_mask2d = us48_mask2d & valid_land

        print(
            "Region cells:",
            f"West={int(west_mask2d.sum())}",
            f"Central‑East={int(central_east_mask2d.sum())}",
            f"US48={int(us48_mask2d.sum())}",
        )

        return {"West": west_mask2d, "Central-East": central_east_mask2d, "US48": us48_mask2d}

    elif region == "nh":
        nh_mask = valid_land
        print("Region cells: NH=", int(nh_mask.sum()))
        return {"NH": nh_mask}

    else:
        raise ValueError("Unknown region. Use 'us' or 'nh'.")


# --------------------------- Seasonal Selection -----------------------------

def select_may_to_september(temp_data: xr.DataArray) -> xr.DataArray:
    """Select May–September (months 5–9) temperatures."""
    month = temp_data["time"].dt.month
    may_sep = temp_data.sel(time=((month >= 5) & (month <= 9)))
    print(
        f"Seasonal subset May–Sep: {may_sep.sizes['time']} days | "
        f"{pd.to_datetime(may_sep.time.values).min().date()} → {pd.to_datetime(may_sep.time.values).max().date()}"
    )
    return may_sep


def quick_subset(
    temp_data: xr.DataArray,
    start_year: int = 1990,
    end_year: int = 1999,
    spatial_step: int = 6,
) -> xr.DataArray:
    """Return a reduced subset for fast iteration/testing.

    - Limits years to [start_year, end_year]
    - Subsamples latitude/longitude by the given step
    """
    print(
        f"Applying quick subset: years {start_year}-{end_year}, spatial step={spatial_step}"
    )
    years = temp_data["time"].dt.year
    sub = temp_data.sel(time=(years >= start_year) & (years <= end_year))
    sub = sub.isel(latitude=slice(None, None, spatial_step), longitude=slice(None, None, spatial_step))
    n_land = int((~np.isnan(sub.isel(time=0))).sum())
    print(
        f"Quick subset sizes — time: {sub.sizes['time']}, lat: {sub.sizes['latitude']}, lon: {sub.sizes['longitude']} | cells: {n_land}"
    )
    return sub


# ----------------------- Thresholds and Exceedances -------------------------

def compute_daily_90th_thresholds(may_sep: xr.DataArray) -> xr.DataArray:
    """Compute 90th percentile by day‑of‑year for May–Sep using the full record.

    Returns a DataArray with dims (dayofyear, latitude, longitude).
    """
    print("Computing daily 90th percentile thresholds (full record)...")
    # dayofyear ∈ [1, 365/366]; May–Sep does not include Feb 29, so leap handling is moot here
    thresholds = (
        may_sep.groupby("time.dayofyear").quantile(0.9, dim="time", skipna=True)
    )
    # Rename the groupby dimension for clarity
    if "dayofyear" not in thresholds.dims:
        thresholds = thresholds.rename({"dayofyear": "dayofyear"})
    print(f"Thresholds computed for {thresholds.sizes['dayofyear']} day‑of‑year values")
    return thresholds


def identify_heatwave_days(
    may_sep: xr.DataArray, thresholds: xr.DataArray, min_run_length: int = 6
) -> xr.DataArray:
    """Identify heatwave days (≥6‑day consecutive exceedances of daily 90th percentiles).

    Vectorized approach:
    1) Exceedances by aligning May–Sep data with thresholds via groupby('time.dayofyear').
    2) Rolling window of size 6 on time to flag ends of consecutive runs.
    3) Shift‑OR combine the run ends to mark all members of qualifying runs.
    """
    print("Identifying exceedance days...")
    exceed = may_sep.groupby("time.dayofyear") > thresholds

    # Ensure rolling window fits within chunk sizes along time
    n_time = int(exceed.sizes["time"])  # number of May–Sep days in the selection
    try:
        exceed = exceed.chunk({"time": n_time})  # put all time in one chunk to avoid dask window limits
    except Exception:
        pass

    print("Marking days that belong to ≥6‑day consecutive runs...")
    # True at time t when the window [t-5, t] is all True
    window = int(min_run_length)
    end_of_runs = exceed.rolling(time=window, min_periods=window).sum() == window

    # Mark membership for all days within each qualifying 6‑day window by shifting
    heatwave = xr.zeros_like(exceed, dtype=bool)
    for shift in range(window):
        heatwave = heatwave | end_of_runs.shift(time=-shift).fillna(False)

    print("Heatwave day identification complete.")
    return heatwave


# ------------------------- Annual Aggregation -------------------------------

def aggregate_annual_per_region(
    heatwave_days: xr.DataArray, region_masks: Dict[str, xr.DataArray]
) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    """Aggregate heatwave days to annual per‑station averages for each region."""
    print("Aggregating annual counts per region (per‑station averages)...")
    annual_counts_cell = heatwave_days.groupby("time.year").sum(dim="time")

    years = annual_counts_cell["year"].values
    regional: Dict[str, np.ndarray] = {}

    for region, mask2d in region_masks.items():
        masked = annual_counts_cell.where(mask2d)
        # Mean across valid land cells in the region
        per_station = masked.mean(dim=("latitude", "longitude"), skipna=True)
        regional[region] = per_station.values
        print(
            f"  {region}: {int(mask2d.sum())} cells, "
            f"avg={np.nanmean(regional[region]):.2f} days/station/year"
        )

    return years, regional


# --------------------------- Trailing Average -------------------------------

def trailing_average(values: np.ndarray, window: int = 15) -> np.ndarray:
    series = pd.Series(values)
    # Allow partial windows at the start; plotting will clip to >=1914
    return series.rolling(window=window, min_periods=1).mean().values


# ------------------------------ Plotting ------------------------------------

def plot_figure(years: np.ndarray, regional_series: Dict[str, np.ndarray], region: str) -> None:
    print("Creating figure...")
    # Compute 15‑year trailing averages
    smooth = {k: trailing_average(v, window=15) for k, v in regional_series.items()}

    # Clip to first full-window year (1914) before plotting
    mask = years >= 1914
    years_plot = years[mask]
    smooth = {k: v[mask] for k, v in smooth.items()}

    fig, ax = plt.subplots(figsize=(12, 8))
    order = list(regional_series.keys())
    colors = {"West": "red", "Central-East": "green", "US48": "black", "NH": "black"}
    widths = {"West": 2.0, "Central-East": 2.0, "US48": 3.0, "NH": 3.0}

    for key in order:
        c = colors.get(key, "black")
        w = widths.get(key, 2.0)
        ax.plot(years_plot, smooth[key], color=c, linewidth=w, label=key)

    ax.set_xlim(int(years_plot.min()), int(years_plot.max()))
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Average Number of Heatwave Days per Year", fontsize=12)
    ax.grid(True, alpha=0.3, linestyle="-", linewidth=0.5)
    ax.legend(loc="upper left", fontsize=11)
    if region == "us":
        title = (
            "Figure 6.3.6 15-year trailing average of number of heatwave days per year per station in the\n"
            "CONUS (black line) and two regions: West (red), Central‑east (green)."
        )
    else:
        title = (
            "Figure 6.3.6 15-year trailing average of number of heatwave days per year per station in the\n"
            "Northern Hemisphere 24–50°N (black)."
        )
    ax.set_title(title, fontsize=11, pad=20)
    plt.tight_layout()

    out_path = Path("Figure6.3.6") / (
        "Figure6.3.6_us.png" if region == "us" else "Figure6.3.6_nh.png"
    )
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Saved figure: {out_path}")
    plt.close(fig)


# ------------------------------- Orchestration ------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce Figure 6.3.6 heatwave days")
    parser.add_argument("--quick", action="store_true", help="Run on a small subset for fast testing")
    parser.add_argument("--quick-years", default="1990-1999", help="Year range for quick mode, e.g., 1990-1999")
    parser.add_argument("--quick-step", type=int, default=6, help="Spatial subsampling step for quick mode")
    parser.add_argument(
        "--min-run",
        type=int,
        default=6,
        help="Minimum consecutive-day run length to qualify as a heatwave (default: 6)",
    )
    parser.add_argument("--region", choices=["us", "nh"], default="us", help="Geo region: 'us' (CONUS) or 'nh' (Northern Hemisphere 24–50°N)")
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Override path to input NetCDF (defaults based on --region)",
    )
    args = parser.parse_args()

    print("=== Reproducing Figure 6.3.6 (Heatwave Days) ===")
    repo_root = Path(__file__).resolve().parents[1]
    default_path = (
        repo_root / "processed_data" / ("preprocessed_us_TMAX_data.nc" if args.region == "us" else "preprocessed_nh_TMAX_data.nc")
    )
    data_file = Path(args.data) if args.data is not None else default_path

    # 1) Load
    temp_land = load_temperature_data(data_file)

    # Optional quick subset prior to other steps
    if args.quick:
        try:
            y0, y1 = [int(x) for x in args.quick_years.split("-")]
        except Exception:
            y0, y1 = 1990, 1999
        temp_land = quick_subset(temp_land, start_year=y0, end_year=y1, spatial_step=args.quick_step)

    # 2) Regions
    region_masks = build_region_masks(temp_land, args.region)

    # 3) Season
    may_sep = select_may_to_september(temp_land)

    # 4) Thresholds
    thresholds = compute_daily_90th_thresholds(may_sep)

    # 5) Heatwave days
    print(f"Using minimum run length: {args.min_run} days")
    heatwave = identify_heatwave_days(may_sep, thresholds, min_run_length=args.min_run)

    # 6) Annual per‑region
    years, regional = aggregate_annual_per_region(heatwave, region_masks)

    # 7) Plot
    plot_figure(years, regional, args.region)

    print("=== Done ===")


if __name__ == "__main__":
    main()


