#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions for saving data and autpicked data.

@author: giacomo.nodjoumi@hyranet.info 
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from scipy.ndimage import maximum_filter
from utils.CRS import MARS2000
from utils.dataStructs import track_dict_builder
import math

def subsurface_saver(source, track, hdf_file, acquisition_array_list, geom, geom_length, dem, data_dir, frequencies_array, selected_frequency=None):
    
    if selected_frequency is None:
        acquisition_array = acquisition_array_list[0]
        acquisition_array_db = acquisition_array_list[1]
        
    elif selected_frequency == 'F1':        
        acquisition_array = acquisition_array_list[0]
        acquisition_array_db = acquisition_array_list[1]
        
    else:
        acquisition_array = acquisition_array_list[2]
        acquisition_array_db = acquisition_array_list[3]
    
    print(track)        
    ### **Collect all the drawings ang generate the ticks labels and plots**
    xs_arrays = [np.array(i) for i in source.data['x']]
    ys_arrays = [np.array(i) for i in source.data['y']]        
#    if len(xs_arrays)!=0:     
    xcors = (np.linspace(geom.xy[0][0], geom.xy[0][-1], num=acquisition_array.shape[1]))
    ycors = (np.linspace(geom.xy[1][0], geom.xy[1][-1], num=acquisition_array.shape[1]))
    print(xs_arrays)
    #track_dict = track_dict_builder(track, geom, geom_length, rolled_acq_db, xcors, ycors, xs_arrays, ys_arrays, dem_profile, layer_dict)
    if geom.geom_type == 'LineString':
        # If it's a LineString, we can directly use geom.xy
        x_start, x_end = geom.xy[0][0], geom.xy[0][-1]
        y_start, y_end = geom.xy[1][0], geom.xy[1][-1]
    
    elif geom.geom_type == 'MultiLineString':
        # If it's a MultiLineString, collect all x and y coordinates
        xs, ys = [], []
        for line in geom.geoms:
            xs.extend(line.xy[0])
            ys.extend(line.xy[1])
    
    #if frequencies_array is None or frequencies_array.size == None:
    #    frequencies_array = np.empty(acquisition_array.shape[1])
            
    track_dict = track_dict_builder(track, geom, geom_length, acquisition_array, acquisition_array_db, xcors, ycors, xs_arrays, ys_arrays, dem, frequencies_array, sampling=0.0375)
    print(track_dict)
    track_df = pd.DataFrame()#columns=track_dict['layers'][0].keys())
    
    for i, val in enumerate(track_dict['layers']):
        print(len(val))
        track_df = pd.concat([track_df, pd.DataFrame(val)])
    print('####################### TRACK DF BUILT')
    track_df.reset_index(inplace=True, drop=True)        
    try:
        #hdf_file = f"{data_dir}subsurface_layers.h5"
        df = pd.read_hdf(hdf_file)
        df = df[df.track_num.str.contains(f'{track}') == False]
        df.reset_index(inplace=True, drop=True)        
    except:
        df = pd.DataFrame(columns=track_dict['layers'].keys())    

    new_df = pd.concat([df, track_df])
    new_df = new_df.drop_duplicates()
    new_df.reset_index(inplace=True, drop=True)

    #hdf_file = f"{data_dir}/subsurface_layers.h5"
    geometries = [Point(lon, lat) for lon, lat in zip(new_df.pt_lons, new_df.pt_lats)]
    gdf = gpd.GeoDataFrame(new_df, geometry=geometries, crs=MARS2000)
    filename = f'{os.path.splitext(hdf_file)[0]}.gpkg'
    savename = os.path.join(data_dir, filename)
    gdf.to_file(savename, driver='GPKG')
    new_df.to_hdf(hdf_file, key='data', mode='w')

    print("Done", hdf_file)
    return new_df, xs_arrays, ys_arrays  

def compute_maxY(x_new, y_new, rolled_acq, kernel):
    maxY = []
    for i, val in enumerate(x_new):
        xc = val
        yc = y_new[i]
        vertical_window = abs(np.arange(yc - kernel, yc + kernel + 1, 1))
        weights = np.array([0, 1, 0])
        filtered = maximum_filter(rolled_acq[vertical_window, xc], footprint=weights)
        index = np.argmax(filtered)
        max_val = vertical_window[index]
        maxY.append(vertical_window[index])
    return maxY

def autopicker(track, dem, acquisition_array_list, geom, geom_length, data_dir, frequencies_array=None, selected_frequency=None):
    
    print('AUTOPICKING: ', track)

    if selected_frequency is None:
        hdf_file = f"{data_dir}subsurface_layers.h5"
        hdf_picked_file = f"{data_dir}/subsurface_layers_autopicked_F1.h5"
        acquisition_array = acquisition_array_list[0]
        acquisition_array_db = acquisition_array_list[1]
    elif selected_frequency == 'F1':
        hdf_file = f"{data_dir}/subsurface_layers_F1.h5"
        hdf_picked_file = f"{data_dir}/subsurface_layers_autopicked_F1.h5"
        acquisition_array = acquisition_array_list[0]
        acquisition_array_db = acquisition_array_list[1]
    else:  # F2
        hdf_file = f"{data_dir}/subsurface_layers_F2.h5"
        hdf_picked_file = f"{data_dir}/subsurface_layers_autopicked_F2.h5"
        acquisition_array = acquisition_array_list[2]
        acquisition_array_db = acquisition_array_list[3]
    
    
    subsurface_df = pd.read_hdf(hdf_file)
    #trackdf = df[df.track_num.str.contains(f'{track}') == True]
#    trackdf = trackdf[trackdf.layer_id.str.contains('surface') == False]
    #trackdf = df.loc[(df.track_num==track) & (df.layer_id!='surface')]
    track_df = subsurface_df.loc[subsurface_df.track_num.str.contains(track) == True]
    print('Picking', track_df)
    sub_ids = track_df.layer_id.unique()
    xs_arrays = []
    ys_arrays = []
    for sub_id in sub_ids:    
        #print(sub_id)
        subdf = track_df[track_df.layer_id == (f'{sub_id}')]
        xs = subdf.pt_cols.values.astype(int)
        ys = subdf.pt_lines.values.astype(int)

        points = np.array(list(zip(xs, ys)))
        # Convert the points to a numpy array for easier manipulation

        # Define the range to increase the x values
        x_start = xs.min()
        x_end = xs.max()
        # Define the step size for increasing x
        step = 1
        # Find the indices of the points within the range to increase
        indices = np.where((points[:, 0] >= x_start) & (points[:, 0] <= x_end))[0]
        # Increase the x values of the selected points by the desired step
        points[indices, 0] += step
        # Interpolate the y values between the original points
        x = points[:, 0]
        y = points[:, 1]
        x_new = np.arange(x_start, x_end + step, step).astype('int')
        #x_new = np.array([math.ceil(x) for x in x_new])
        y_new = np.interp(x_new, x, y).astype('int')
        y_new = np.array([math.floor(y) for y in y_new])
        #print(y_new.dtype)
        #print(x_new.dtype)
        kernel = 3
        print(len(x_new), len(xs))
        #if len(xs) < len(x_new):
        #maxY = []
        num_iterations = 1 # len(x_new)
        print('FINDING MAX: ', track)
        for _ in range(num_iterations):
            maxY = compute_maxY(x_new, y_new, acquisition_array, kernel)

        xs_arrays.append(x_new)
        ys_arrays.append(np.array(maxY))
    xcors = (np.linspace(geom.xy[0][0], geom.xy[0][-1], num=acquisition_array.shape[1]))
    ycors = (np.linspace(geom.xy[1][0], geom.xy[1][-1], num=acquisition_array.shape[1]))
    print(xs_arrays)
    #track_dict = track_dict_builder(track, geom, geom_length, rolled_acq_db, xcors, ycors, xs_arrays, ys_arrays, dem_profile, layer_dict)
    #if frequencies_array is None or frequencies_array.size == None:
    #    frequencies_array = np.empty(acquisition_array.shape[1])
    track_dict = track_dict_builder(track, geom, geom_length, acquisition_array, acquisition_array_db, xcors, ycors, xs_arrays, ys_arrays, dem, frequencies_array, sampling=0.0375)
    print(track_dict)
    
    track_df = pd.DataFrame()#columns=track_dict['layers'][0].keys())

    for i, val in enumerate(track_dict['layers']):
        track_df = pd.concat([track_df, pd.DataFrame(val)])
    print('####################### TRACK DF BUILT')
    track_df.reset_index(inplace=True, drop=True)        
    try:
        #hdf_picked_file = f"{data_dir}/subsurface_layers_autopicked.h5"
        picked_df = pd.read_hdf(hdf_picked_file)
        picked_df = picked_df[picked_df.track_num.str.contains(f'{track}') == False]
        picked_df = picked_df.loc[picked_df.track_num.str.contains(track) == False]
        picked_df.reset_index(inplace=True, drop=True)        
    except:
        picked_df = pd.DataFrame()#columns=track_dict['layers'][0].keys())    

    new_df = pd.concat([picked_df, track_df])
    new_df = new_df.drop_duplicates()
    new_df.reset_index(inplace=True, drop=True)

    geometries = [Point(lon, lat) for lon, lat in zip(new_df.pt_lons, new_df.pt_lats)]
    gdf = gpd.GeoDataFrame(new_df, geometry=geometries, crs=MARS2000)
    filename = f'{os.path.splitext(hdf_picked_file)[0]}.gpkg'
    savename = os.path.join(data_dir, filename)
    gdf.to_file(savename, driver='GPKG')
    new_df.to_hdf(hdf_picked_file, key='data', mode='w')

    print("Done", hdf_picked_file)
    return new_df, xs_arrays, ys_arrays    