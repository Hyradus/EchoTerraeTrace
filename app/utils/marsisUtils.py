#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 11:25:46 2024

@author: hyradus - giacomo.nodjoumi@hyranet.info
"""

import numpy as np
import os
import pathlib
from numpy import frombuffer as fbuff
from .genUtils import get_paths
from .DFUtils import xDR_params, COH_params

def raw_reader(file, offBytes, FileRecord, Item, RecordBytes, precision):
    dtype = np.dtype(precision)
    is_string = 'S' in precision
    values = np.empty(FileRecord, dtype=object if is_string else dtype)
    
    for i in range(FileRecord):
        offset = Item + offBytes + (RecordBytes * i) if not is_string else offBytes + (RecordBytes * i)
        values[i] = np.frombuffer(file, dtype=dtype, count=1, offset=offset)[0]
        if is_string:
            values[i] = values[i].decode()
    
    return values.tolist()

def process_parameter(xDR_File, i, ParamDF, FileRecord, RecordBytes):
    offBytes = ParamDF['START_BYTES'][i]
    precision = ParamDF['DATA_TYPE'][i]
    Items = ParamDF['ITEMS'][i]
    ItemBytes = ParamDF['ITEM_BYTES'][i]
    
    with open(xDR_File, 'rb') as file:
        f = file.read()

        if Items > 1 and 'S' not in precision:
            values = []
            mean_values = []
            for l in range(Items):
                Item = l * ItemBytes
                val = np.array(raw_reader(f, offBytes, FileRecord, Item, RecordBytes, precision))
                values.append(val)
                mean_values.append(np.mean(val))
        else:
            Item = 0
            values = np.array(raw_reader(f, offBytes, FileRecord, Item, RecordBytes, precision))
            mean_values = values[0] if 'S' in precision else np.mean(values)

    return values, mean_values
