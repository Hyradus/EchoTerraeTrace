#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions for profiling DEM data and radargram power profiles.

@author: giacomo.nodjoumi@hyranet.info 
"""

import numpy as np
import numpy.ma as ma
import rasterio as rio
from shapely.geometry import LineString
from rasterio.windows import from_bounds
from sklearn.preprocessing import MinMaxScaler, StandardScaler


def dem_profiler_sampling(dem_savename: str, line: LineString, n_samples: int) -> np.ndarray:
    """
    Generate a profile of DEM values along a line by sampling `n_samples` points.

    Args:
        dem_savename: Path to the DEM file.
        line: Shapely LineString object representing the line to profile.
        n_samples: Number of points to sample along the line.

    Returns:
        A numpy array of DEM values along the line, with NaNs handled.
    """
    # Calculate the bounding box of the line
    minx, miny, maxx, maxy = line.bounds

    # Open the DEM with rasterio
    with rio.open(dem_savename) as src:
        # Define a window based on the bounding box of the line
        window = from_bounds(minx, miny, maxx, maxy, transform=src.transform)

        # Read data within the window
        xarr = src.read(1, window=window, masked=True)
        transform = src.window_transform(window)

    # Interpolate points along the line
    points = [line.interpolate(i / (n_samples - 1), normalized=True) for i in range(n_samples)]

    # Convert points to pixel coordinates and extract values
    profile = []
    for point in points:
        # Transform geographic coordinates to pixel coordinates
        col, row = ~transform * (point.x, point.y)
        row, col = int(row), int(col)

        # Access the nearest pixel value, handling out-of-bounds cases
        if 0 <= row < xarr.shape[0] and 0 <= col < xarr.shape[1]:
            value = xarr[row, col]
        else:
            value = np.nan

        profile.append(value)

    # Replace NaNs with the mean of non-NaN values
    profile = np.where(np.isnan(profile), np.nanmean(profile), profile)

    return np.array(profile)


def power_profiler(radargram: np.ndarray, scaler: float = 0.137, normalize: str = None) -> np.ndarray:
    """
    Generate a power profile from a radargram.

    Args:
        radargram: A 2D numpy array representing the radargram.
        scaler: A scaling factor applied to the power profile.
        normalize: Normalization method, either 'minmax' or 'zscore'. Default is None.

    Returns:
        A numpy array representing the power profile.
    """
    pow_prof = []

    # Handle radargram dimensions
    try:
        rdrg_width = radargram.shape[1]
    except IndexError:
        rdrg_width = radargram.size[0]
        radargram = np.array(radargram)

    # Extract max power for each column
    for i in range(rdrg_width):
        pow_prof.append(radargram[:, i].max())

    # Apply scaling
    pow_prof = np.array(pow_prof) * scaler

    # Apply normalization if specified
    if normalize:
        if normalize == 'minmax':
            pow_prof = MinMaxScaler().fit_transform(pow_prof.reshape(-1, 1)).flatten()
        elif normalize == 'zscore':
            pow_prof = StandardScaler().fit_transform(pow_prof.reshape(-1, 1)).flatten()

    return pow_prof


def dem_profiler_xarray(line_geom: LineString, dem) -> np.ndarray:
    """
    Extract DEM values along a line geometry.

    Args:
        line_geom: A Shapely LineString object.
        dem: xarray DataArray containing the DEM data.

    Returns:
        A numpy array of elevation values along the line.
    """
    elevations = []
    line_coords = np.array(line_geom.coords)

    # Loop through each coordinate pair and extract corresponding elevation
    for coord in line_coords:
        lon, lat = coord
        elevation = dem.sel(x=lon, y=lat, method="nearest").values.flatten()[0]
        elevations.append(elevation)

    return np.array(elevations)

def dem_profiler_api(geom, target='Mars'):
    
        
    # Define the API URL (adjust the URL if your Docker container runs on a different host)
    api_url = "https://api.hyranet.info/profile/"
    
    # Convert shapely geometry to a GeoJSON serializable format
    geom_geojson = mapping(geom)
    
    
    # Prepare the payload (including the serialized geometry)
    payload = {
        "geometry": geom_geojson,
        "target": target
    }
    
    # Send a POST request to the API with the payload
    response = requests.post(api_url, json=payload)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        profile_data = response.json()
    
        # Extract distances and elevations from the response
        
        elevations = profile_data.get("elevations_m")        
        # Print the topographic profile data        
        #print("Elevations (m):", elevations)
    
        
    else:
        # If the request failed, print the error message
        print(f"Request failed with status code {response.status_code}: {response.text}")
    return np.array(elevations)
    
    
    
