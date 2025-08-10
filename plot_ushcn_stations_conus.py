#!/usr/bin/env python3
"""
Plot USHCN station locations on a Cartopy map focused on CONUS.

Defaults:
- Input: ushcn_stn_list_250617.txt (expects columns: COOP ID, Lat, Lon, St, Station Name)
- Output: figures/ushcn_stations_conus.png

Requires:
- matplotlib
- cartopy
Optionally uses numpy for density computation
"""

from __future__ import annotations

import argparse
import csv
import os
from typing import List, Tuple, Optional

import numpy as np

import matplotlib.pyplot as plt
import matplotlib as mpl
import cartopy.crs as ccrs
import cartopy.feature as cfeature


def read_station_lat_lons(station_list_path: str) -> List[Tuple[float, float]]:
    """Read station latitude/longitude pairs from the USHCN station list.

    The file is expected to be a tab-delimited text file with a header row:
    COOP ID\tLat\tLon\tSt\tStation Name
    """
    station_coords: List[Tuple[float, float]] = []
    with open(station_list_path, "r", newline="") as f:
        # Use csv with delimiter set to tab for robust parsing (station names contain spaces)
        reader = csv.reader(f, delimiter="\t")
        header_seen = False
        for row in reader:
            if not row:
                continue
            # Detect and skip header
            if not header_seen:
                header_seen = True
                # If the first column is not numeric, it's the header
                try:
                    float(row[1])  # attempt to parse Lat
                except Exception:
                    continue
            try:
                # Expected columns: [COOP ID, Lat, Lon, St, Station Name]
                lat = float(row[1])
                lon = float(row[2])
                station_coords.append((lat, lon))
            except Exception:
                # Skip malformed rows silently
                continue
    return station_coords


def filter_conus(coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Return only coordinates within a simple CONUS bounding box."""
    min_lon, max_lon = -125.0, -66.0
    min_lat, max_lat = 24.0, 50.0
    return [
        (lat, lon)
        for lat, lon in coords
        if (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon)
    ]


def plot_conus_stations(
    station_coords: List[Tuple[float, float]],
    output_path: str,
    show: bool = False,
) -> None:
    """Plot station points on a CONUS-focused map and save the figure."""
    # Projection well-suited for CONUS
    proj = ccrs.LambertConformal(
        central_longitude=-96.0,
        central_latitude=39.0,
        standard_parallels=(33, 45),
    )

    fig = plt.figure(figsize=(11, 7))
    ax = plt.axes(projection=proj)

    # Geographic extent for CONUS in PlateCarree
    ax.set_extent([-125, -66, 24, 50], crs=ccrs.PlateCarree())

    # Map features
    ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor="#f0f0f0")
    ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor="#ffffff")
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6, edgecolor="#444444")
    ax.add_feature(cfeature.BORDERS.with_scale("50m"), linewidth=0.5, edgecolor="#666666")
    ax.add_feature(cfeature.STATES.with_scale("50m"), linewidth=0.3, edgecolor="#999999")

    if station_coords:
        lats = [lat for lat, _ in station_coords]
        lons = [lon for _, lon in station_coords]
        ax.scatter(
            lons,
            lats,
            s=10,
            c="#cc0000",
            alpha=0.75,
            transform=ccrs.PlateCarree(),
            zorder=10,
            linewidths=0,
        )

    ax.set_title("USHCN Stations (CONUS)")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close(fig)


def _setup_conus_axes(fig_size: Tuple[float, float] = (11, 7), *, fill_background: bool = True):
    proj = ccrs.LambertConformal(
        central_longitude=-96.0,
        central_latitude=39.0,
        standard_parallels=(33, 45),
    )
    fig = plt.figure(figsize=fig_size)
    ax = plt.axes(projection=proj)
    ax.set_extent([-125, -66, 24, 50], crs=ccrs.PlateCarree())
    if fill_background:
        ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor="#f0f0f0", zorder=0)
        ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor="#ffffff", zorder=0)
    # Draw line features above raster layers (will be above the pcolormesh with higher zorder)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6, edgecolor="#444444", zorder=12)
    ax.add_feature(cfeature.BORDERS.with_scale("50m"), linewidth=0.5, edgecolor="#666666", zorder=11)
    ax.add_feature(cfeature.STATES.with_scale("50m"), linewidth=0.3, edgecolor="#999999", zorder=10)
    return fig, ax


def _compute_density_regular_grid(
    coords: List[Tuple[float, float]], bin_deg: float, area_normalize: bool
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    lats = np.array([lat for lat, _ in coords], dtype=float)
    lons = np.array([lon for _, lon in coords], dtype=float)
    # Define bin edges covering CONUS bbox
    lat_edges = np.arange(24.0, 50.0 + 1e-6, bin_deg)
    lon_edges = np.arange(-125.0, -66.0 + 1e-6, bin_deg)
    H, yedges, xedges = np.histogram2d(lats, lons, bins=[lat_edges, lon_edges])
    # Area-normalize by cos(latitude) per row (approximate equal-area adjustment)
    if area_normalize:
        lat_centers = 0.5 * (yedges[:-1] + yedges[1:])
        coslat = np.cos(np.deg2rad(lat_centers))
        coslat[coslat == 0] = np.nan  # avoid divide-by-zero (not in CONUS)
        H = H / coslat[:, None]
    # Create grid for pcolormesh (x: lon, y: lat)
    X, Y = np.meshgrid(xedges, yedges)
    return H, X, Y


def _compute_density_nearest_grid(
    coords: List[Tuple[float, float]],
    grid_map_path: str,
    bin_deg: float,
    area_normalize: bool,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Expect columns grid_lat, grid_lon
    import pandas as pd

    df = pd.read_csv(grid_map_path)
    if not {"grid_lat", "grid_lon"}.issubset(df.columns):
        raise KeyError("grid_map CSV must contain 'grid_lat' and 'grid_lon' columns")

    grid_lats = df["grid_lat"].to_numpy(dtype=float)
    grid_lons = df["grid_lon"].to_numpy(dtype=float)

    # Map each station to nearest grid center (in lat/lon space) to get per-center counts
    try:
        from scipy.spatial import cKDTree  # type: ignore
        use_tree = True
    except Exception:
        use_tree = False

    stations = np.array(coords, dtype=float)
    if stations.size == 0:
        # Build an empty grid
        lon_edges = np.unique(np.round(grid_lons, 3))
        lat_edges = np.unique(np.round(grid_lats, 3))
        X, Y = np.meshgrid(lon_edges, lat_edges)
        return np.zeros_like(X[:-1, :-1]), X, Y

    if use_tree:
        tree = cKDTree(np.c_[grid_lats, grid_lons])
        d, idx = tree.query(stations, k=1)
        counts = np.zeros(grid_lats.shape[0], dtype=int)
        for j in idx:
            counts[int(j)] += 1
    else:
        counts = np.zeros(grid_lats.shape[0], dtype=int)
        for slat, slon in stations:
            d2 = (grid_lats - slat) ** 2 + (grid_lons - slon) ** 2
            j = int(np.argmin(d2))
            counts[j] += 1

    # Aggregate center counts into a regular lat/lon grid of bin_deg
    lat_edges = np.arange(24.0, 50.0 + 1e-6, bin_deg)
    lon_edges = np.arange(-125.0, -66.0 + 1e-6, bin_deg)
    H, yedges, xedges = np.histogram2d(grid_lats, grid_lons, bins=[lat_edges, lon_edges], weights=counts)
    if area_normalize:
        lat_centers = 0.5 * (yedges[:-1] + yedges[1:])
        coslat = np.cos(np.deg2rad(lat_centers))
        coslat[coslat == 0] = np.nan
        H = H / coslat[:, None]
    X, Y = np.meshgrid(xedges, yedges)
    return H, X, Y


def plot_station_density(
    station_coords: List[Tuple[float, float]],
    output_path: str,
    grid_map_path: Optional[str] = None,
    regular_bin_deg: float = 4.0,
    area_normalize: bool = True,
    show: bool = False,
) -> None:
    # Compute density either by nearest BE grid centers (if provided) or via regular lat/lon bins
    if grid_map_path and os.path.exists(grid_map_path):
        H, X, Y = _compute_density_nearest_grid(station_coords, grid_map_path, regular_bin_deg, area_normalize)
    else:
        H, X, Y = _compute_density_regular_grid(station_coords, regular_bin_deg, area_normalize)

    # For NaN cells to appear white, avoid filling land/ocean behind the mesh
    fig, ax = _setup_conus_axes(fill_background=False)
    # Set zero-count cells to NaN so they use the colormap's 'bad' color (white)
    H_plot = H.copy()
    H_plot[H_plot == 0] = np.nan
    cmap = mpl.colormaps["Reds"].copy()
    cmap.set_bad(color="white")
    # pcolormesh expects X, Y as bin edges; H shape must be (len(y)-1, len(x)-1)
    # Use a perceptually uniform colormap; set minimum to 0
    pcm = ax.pcolormesh(
        X,
        Y,
        H_plot,
        cmap=cmap,
        shading="auto",
        transform=ccrs.PlateCarree(),
        zorder=1, vmin=0, vmax=40
    )
    cbar = fig.colorbar(pcm, ax=ax, orientation="vertical", pad=0.02, shrink=0.85)
    cbar.set_label("Area-adjusted station count per cell")
    ax.set_title("USHCN Station Density (CONUS)")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot USHCN station locations on a CONUS Cartopy map."
    )
    parser.add_argument(
        "--input",
        default="ushcn_stn_list_250617.txt",
        help="Path to USHCN station list text file",
    )
    parser.add_argument(
        "--output",
        default=os.path.join("figures", "ushcn_stations_conus.png"),
        help="Path to output PNG file",
    )
    parser.add_argument(
        "--density-output",
        default=os.path.join("figures", "ushcn_station_density_conus.png"),
        help="Path to output PNG file for the station density plot",
    )
    parser.add_argument(
        "--grid-map",
        default=None,
        help=(
            "Optional path to a CSV with grid centers (e.g., gridded_station_map.csv). "
            "If provided, will compute density by assigning each station to the nearest grid center "
            "(expects columns grid_lat, grid_lon)."
        ),
    )
    parser.add_argument(
        "--regular-grid-deg",
        type=float,
        default=4.0,
        help=(
            "Bin size in degrees for the density grid (also used to aggregate grid centers when --grid-map is provided)."
        ),
    )
    parser.add_argument(
        "--no-area-normalize",
        action="store_true",
        help=(
            "Disable cosine(latitude) area normalization. By default, counts are divided by cos(lat)."
        ),
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the plot interactively after saving",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    coords = read_station_lat_lons(args.input)
    coords_conus = filter_conus(coords)
    plot_conus_stations(coords_conus, args.output, show=args.show)
    # Also compute and plot station density
    try:
        plot_station_density(
            coords_conus,
            args.density_output,
            grid_map_path=args.grid_map,
            regular_bin_deg=args.regular_grid_deg,
            area_normalize=(not args.no_area_normalize),
            show=args.show,
        )
    except Exception as e:
        # Keep the basic scatter plot even if density fails
        print(f"Warning: failed to compute density map: {e}")


if __name__ == "__main__":
    main()


