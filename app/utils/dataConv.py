#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: giacomo.nodjoumi@hyranet.info - g.nodjoumi@jacobs-university.de
"""
from PIL import Image
import pds4_tools
import numpy as np
import os
import cv2 as cv
from multiprocessing import Pool
import pandas as pd
import math

def pds_converter(acquisition_folder, track, tp):   
    # see https://pds-geosciences.wustl.edu/mro/urn-nasa-pds-mro_sharad_simulations/document/userguide.pdf
    if tp == 'ssim':
        data = pds4_tools.read(f"{acquisition_folder}{track}_sim.xml")
        combo = data["Combined_Clutter_Simulation"].data
    else:
        import pdr

        data = pdr.read(f"{acquisition_folder}{track}_rgram.lbl")
        combo = data['IMAGE']
    
    # Log scale image
    comboScale = np.log10(combo + 1e-30)

    # Get valid (actually simulated) values
    comboValid = comboScale[combo != 0]

    # Make linear mapping from image values to 0 -255
    p10 = np.percentile(comboValid, 10)
    m = 255 / (comboValid.max() - p10)
    b = -p10 * m

    # Apply map, clip values below minimum
    comboMap = (m * comboScale) + b
    comboMap[comboMap < 0] = 0
    comboMap = comboMap.astype(np.uint8)

    # Save browse image
    comboImg = Image.fromarray(comboMap)
    comboImg.save(f"{acquisition_folder}{track}_{tp}.png")
    
    return comboMap, combo, comboScale


c = 299792458  # speed of light in vacuum (m/s)

# Conversion functions
def twt2height(twt, eps, c=c):    
    return (c * twt * 1e-6) / (2 * np.sqrt(eps))  # twt is in microseconds so we need to convert it to seconds 1 s == 10^6 microseconds

def height2twt(h, eps, c=c):    
    return (2 * h * np.sqrt(eps) / c) * 1e6  # twt is in microseconds so we need to convert it to seconds 1 s == 10^6 microseconds

def epsit(twt, h, c=c):
    return ((c * twt * 1e-6) / (2 * h)) ** 2

def real_permittivity(delta_t, h, c=c):
    # Calculate the real permittivity
    return ((c * delta_t * 1e-6) / (2 * h)) ** 2

def calculate_thickness(delta_t, epsilon_prime, c=c):
    # Calculate the thickness
    return (c * delta_t * 1e-6) / (2 * math.sqrt(epsilon_prime))
