"""
Reproduce Figure 6.3.5 (version 1):
- Compute per-station total days ≥ 95°F in non-overlapping 6-year periods for CONUS (US48)
- Treat each land grid cell as a station and average across land cells
- Input data: processed_data/preprocessed_us_TMAX_data.nc (absolute temps, °C)

Usage (from project root):
    # Multipanel (default thresholds: 95, 97.5, 100, 102.5, 105 F)
    # US (CONUS):
    python Figure6.3.5/reproduce_6_3_5.py \
        --region us \
        --output Figure6.3.5/Figure6.3.5_us_multi.png \
        

    # Northern Hemisphere (24–50°N, all longitudes):
    python Figure6.3.5/reproduce_6_3_5.py \
        --region nh \
        --output Figure6.3.5/Figure6.3.5_nh_multi.png \
        

Notes:
- Regional (nine-region) time series are deferred to a future version.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Tuple, Dict, List

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt


def fahrenheit_to_celsius(temp_f: float) -> float:
    return (temp_f - 32.0) * (5.0 / 9.0)


def load_dataset(file_path: str) -> xr.Dataset:
    print(f"Loading dataset: {file_path}")
    ds = xr.open_dataset(
        file_path,
        chunks={"time": 365, "latitude": "auto", "longitude": "auto"},
    )
    # Expect variables: temperature (°C), land_mask; coords: time, latitude, longitude
    return ds


def compute_us48_series(
    ds: xr.Dataset,
    threshold_c: float = 35.0,
    bin_years: int = 6,
    anchor_end_year: int = 2024,
) -> xr.DataArray:
    """Compute US48 per-station totals of days exceeding threshold for each 6-year bin.

    Returns an xr.DataArray indexed by bin_start (the first year of each period).
    """
    print(f"Computing exceedance mask for threshold {threshold_c:.1f}°C …")
    is_hot = (ds["temperature"] >= threshold_c)

    years = is_hot.time.dt.year
    # Align bins so that the LAST bin ends at anchor_end_year (e.g., 2024)
    anchor_start_year = anchor_end_year - (bin_years - 1)
    print(
        f"Anchoring 6-yr bins to end at {anchor_end_year} (starts at {anchor_start_year} for final bin)"
    )

    # Compute first-year label for each 6-year bin using the anchored start
    # Example: with anchor_end_year=2024 and bin_years=6 → anchor_start_year=2019,
    # bins start at ..., 2007, 2013, 2019 so the last ends at 2024.
    bin_start = ((years - anchor_start_year) // bin_years) * bin_years + anchor_start_year
    # Ensure the grouping key is named so the resulting dimension is 'bin_start'
    bin_start = bin_start.rename("bin_start")
    print("Grouping by 6-year periods and counting exceedance days per grid cell …")
    counts_cell = is_hot.groupby(bin_start).sum(dim="time")

    print("Averaging across land grid cells to obtain per-station totals …")
    us48_series = counts_cell.mean(dim=("latitude", "longitude"), skipna=True)
    us48_series.name = "US48_days_ge_95F_per_6yr"
    return us48_series


def format_period_labels(bin_starts: np.ndarray) -> Tuple[np.ndarray, list[str]]:
    labels = []
    for start in bin_starts:
        start_int = int(start)
        end = start_int + 5
        labels.append(f"{start_int}\u2013{str(end)[-2:]}")  # e.g., 1931–36
    return bin_starts, labels


def plot_us48_bars(us48_series: xr.DataArray, output_file: Path) -> None:
    print(f"Creating plot: {output_file}")
    # Materialize values for plotting
    series_computed = us48_series.compute()

    # Determine the grouping dimension name (expected 'bin_start')
    dim_name = list(series_computed.dims)[0]
    starts = series_computed.coords[dim_name].values
    values = series_computed.values
    starts, labels = format_period_labels(starts)

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.bar(starts, values, width=5.5, color="salmon", edgecolor="brown", label="US48")

    ax.set_xticks(starts)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_xlim(starts.min() - 3, starts.max() + 8)
    ax.set_xlabel("Six-year periods")
    ax.set_ylabel("Per station total days ≥95°F per 6-yr period")
    ax.legend(fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=200)
    plt.close(fig)
    print(f"Saved figure: {output_file}")


# CSV output removed per request


def compute_multi_series(
    ds: xr.Dataset, thresholds_f: List[float], bin_years: int, anchor_end_year: int = 2024
) -> Dict[float, xr.DataArray]:
    """Compute US48 per-station series for multiple Fahrenheit thresholds."""
    results: Dict[float, xr.DataArray] = {}
    for thr_f in thresholds_f:
        thr_c = fahrenheit_to_celsius(thr_f)
        print(f"\n--- Threshold {thr_f:.1f}°F ({thr_c:.1f}°C) ---")
        series = compute_us48_series(
            ds, threshold_c=thr_c, bin_years=bin_years, anchor_end_year=anchor_end_year
        )
        results[thr_f] = series
    return results


def plot_multipanel(
    series_by_threshold: Dict[float, xr.DataArray], output_file: Path, region_label: str
) -> None:
    print(f"Creating multipanel plot: {output_file}")
    thresholds = sorted(series_by_threshold.keys())
    n = len(thresholds)
    # Use the first series to define x-axis labels
    first_series = series_by_threshold[thresholds[0]].compute()
    dim_name = list(first_series.dims)[0]
    starts = first_series.coords[dim_name].values
    starts, labels = format_period_labels(starts)

    fig, axes = plt.subplots(n, 1, figsize=(12, 2.6 * n), sharex=True)
    if n == 1:
        axes = [axes]

    for ax, thr_f in zip(axes, thresholds):
        ser = series_by_threshold[thr_f].compute()
        values = ser.values
        ax.bar(starts, values, width=5.5, color="salmon", edgecolor="brown")
        ax.set_ylabel("days/6yr")
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        ax.set_title(f"≥{thr_f:g}°F", loc="left", fontsize=11, pad=6)

    axes[-1].set_xticks(starts)
    axes[-1].set_xticklabels(labels, rotation=45, ha="right")
    axes[-1].set_xlabel("Six-year periods")

    fig.suptitle(f"Per-station total days above thresholds (6-yr periods) — {region_label}", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=200)
    plt.close(fig)
    print(f"Saved figure: {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce Figure 6.3.5 (US or NH)")
    parser.add_argument(
        "--region",
        choices=["us", "nh"],
        default="us",
        help="Region indicator: 'us' (CONUS) or 'nh' (Northern Hemisphere 24–50°N)",
    )
    parser.add_argument(
        "--thresholds-f",
        nargs="+",
        type=float,
        default=[95.0, 97.5, 100.0, 102.5, 105.0],
        help="List of thresholds in Fahrenheit for multipanel plot (default: 95 97.5 100 102.5 105)",
    )
    parser.add_argument(
        "--bin-years", type=int, default=6, help="Bin size in years (default: 6)"
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2024,
        help="Anchor end year for the last 6-year bin (default: 2024)",
    )
    parser.add_argument(
        "--output",
        default="Figure6.3.5/Figure6.3.5_us_multi.png",
        help="Output multipanel figure path",
    )

    args = parser.parse_args()

    # Choose input path from region
    input_path = (
        "processed_data/preprocessed_us_TMAX_data.nc"
        if args.region == "us"
        else "processed_data/preprocessed_nh_TMAX_data.nc"
    )

    output_path = Path(args.output)
    # If outputs are default US names but region is NH, swap filenames for clarity
    if args.region == "nh" and str(output_path) == "Figure6.3.5/Figure6.3.5_us_multi.png":
        output_path = Path("Figure6.3.5/Figure6.3.5_nh_multi.png")

    # No CSV outputs

    ds = load_dataset(input_path)
    series_by_thr = compute_multi_series(
        ds, args.thresholds_f, args.bin_years, anchor_end_year=args.end_year
    )
    region_label = "US48" if args.region == "us" else "Northern Hemisphere (24–50°N)"
    plot_multipanel(series_by_thr, output_path, region_label)

    print("Done.")


if __name__ == "__main__":
    main()


