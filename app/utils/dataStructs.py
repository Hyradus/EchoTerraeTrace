#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: giacomo.nodjoumi@hyranet.info
"""
import math
import numpy as np
from shapely import Point

def track_dict_builder(track, geom, geom_length, xdr_array, xdr_array_db, xcors, ycors, xs_arrays, ys_arrays, dem, frequencies_array, sampling=0.0375):
    track_dict = {
        "track_id": track,
        "layers": None,
    }
    track_layers = []

    for i, (x_arr, y_arr) in enumerate(zip(xs_arrays, ys_arrays)):
        layer_dict = {
            "track_num": f"{track}",
            "layer_id": str(i),
            "pt_distances": (np.array(x_arr) * math.ceil(geom_length / xdr_array.shape[1])).astype('float64'),
            "pt_twts": abs(np.array(y_arr) * -sampling).astype('float64'),
            "pt_lines": np.ceil(y_arr).astype(np.int64),
            "pt_cols": np.ceil(x_arr).astype(np.int64),
            "pt_lats": [],
            "pt_lons": [],
            "surf_elevs": [],
            "surf_twts": [],
            "pt_db": [],
            "pt_snr_db": [],
            "signal_std_db": [],
            "signal_median_db": [],
            "signal_snr_db": [],
            "frequencies_1": [] if sampling != 0.0375 else None,
            "frequencies_2": [] if sampling != 0.0375 else None
        }

        for xx, yy in zip(x_arr, y_arr):
            xxI = math.floor(xx)
            yyI = math.floor(yy)
            layer_dict["pt_lons"].append(xcors[xxI])
            layer_dict["pt_lats"].append(ycors[xxI])
            elevation = dem.sel(x=xcors[xxI], y=ycors[xxI], method="nearest").values.flatten()[0]
            layer_dict["surf_elevs"].append(elevation)

            sliced_db = xdr_array_db[:, xxI]
            signal_std_db = np.std(sliced_db)
            signal_median_db = np.median(sliced_db)
            signal_snr_std_db = signal_median_db - signal_std_db
            pt_db = xdr_array_db[yyI][xxI]
            pt_snr_db = signal_median_db - pt_db
            surf_db = np.max(sliced_db)

            layer_dict["signal_std_db"].append(signal_std_db)
            layer_dict["signal_median_db"].append(signal_median_db)
            layer_dict["signal_snr_db"].append(signal_snr_std_db)
            layer_dict["pt_db"].append(pt_db)
            layer_dict["pt_snr_db"].append(pt_snr_db)
            layer_dict["surf_twts"].append(np.where(sliced_db == surf_db)[0][0] * sampling)

            if sampling != 0.0375:
                layer_dict["frequencies_1"].append(frequencies_array[0][xxI])
                layer_dict["frequencies_2"].append(frequencies_array[1][xxI])
            
        adjusted_points = [geom.interpolate(geom.project(Point(xy))) for xy in zip(layer_dict["pt_lons"], layer_dict["pt_lats"])]
        layer_dict["pt_lats"] = [pt.y for pt in adjusted_points]
        layer_dict["pt_lons"] = [pt.x for pt in adjusted_points]

        track_layers.append(layer_dict)

    track_dict['layers']=track_layers
    return track_dict
