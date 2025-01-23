#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: giacomo.nodjoumi@hyranet.info - g.nodjoumi@jacobs-university.de
"""

import geopandas as gdf
import numpy as np
import os
from PIL import Image
from pyproj import CRS, Transformer
from utils.geomUtils import get_geom
from utils.profilers import dem_profiler_sampling, power_profiler
from utils.dataConv import pds_converter
from utils.dataPlots import Formatters
import rioxarray as riox
from sklearn.preprocessing import normalize, MinMaxScaler
from utils.filters import FFTfilter, FFTfilter_vertical, BLURfilter, IDWTfilter, log_gabor_filter
from skimage.filters import unsharp_mask
import cv2
import concurrent.futures
from shapely import LineString
from utils.CRS import MARS2000, DST_CRS

class DataPrepSHARAD:
    def __init__(self, acquisition_folder, track, wcs_url, dem_layerid, bmap_layerid, boundingbox, plot_size, roll=1800):
        self.acquisition_folder = acquisition_folder
        self.track = f"s_{track}"
        self.wcs_url = wcs_url
        self.dem_layerid = dem_layerid
        self.bmap_layerid = bmap_layerid
        self.boundingbox = boundingbox
        self.plot_size = plot_size
        self.roll = roll
        self.src_crs = MARS2000
        self.dst_crs = MARS2000

    def prepare_data(self):
        acquisition = f'{self.acquisition_folder}{self.track}_tiff.tif'
        print('ssim')
        scs_img_scaled, scs_img_src, scs_scaled = pds_converter(self.acquisition_folder, self.track, 'ssim')
        print('rgram')
        acq_img_scaled, acq_img_src, acq_scaled = pds_converter(self.acquisition_folder, self.track, 'rgram')
        print('done')
        print('Acquiring Geometry')
        try:
            geom, geom_gdf = get_geom(self.boundingbox, self.track, self.acquisition_folder)
        except Exception as e:
            print(e)
        print(geom, geom_gdf)
        
        max_width, max_height = acq_img_src.shape[1], acq_img_src.shape[0]
        geom_rep = geom_gdf.to_crs(DST_CRS).iloc[0]['geometry']
        geom_length = geom_rep.length // 1000
        print(geom_length)
        
        xFormatter, yFormatter, _ = Formatters(geom_length, max_width)
        try:
            print('Acquiring basemaps')
            # Acquiring basemaps
            # bmap_savename, dem_savename = get_basemaps(geom, self.acquisition_folder, self.bmap_layerid, self.dem_layerid, self.wcs_url)
        except Exception as e:
            print(e)
        
        acq_img_scalednorm = MinMaxScaler().fit_transform(normalize(acq_img_src))
        try:
            print('Computing power profiles')
            scs_pow_profile = power_profiler(scs_img_scaled)
            acq_pow_profile = power_profiler(acq_img_scaled)
        except Exception as e:
            print(e)
        try:
            print("roll", self.roll)
            rolled_acq = np.roll(np.array(acq_img_scaled), self.roll, axis=0)
            rolled_scs = np.roll(np.array(scs_img_scaled), self.roll, axis=0)
            rolled_acq_scaled = np.roll(acq_img_scalednorm, self.roll, axis=0)
            rolled_scs_db = rolled_scs * 0.137
            rolled_acq_db = rolled_acq * 0.137
            print(rolled_acq.shape)
            print(rolled_scs.shape)
        except Exception as e:
            print(e)
        
        try:
            print('Acquiring DEM profile')
            shape = acq_img_scaled.shape[1]
            dem_basepath = os.path.join(self.acquisition_folder, 'Basemaps')
            dem_name = f'{self.dem_layerid}.tiff'
            dem_source = os.path.join(dem_basepath, dem_name)
            print('EDIT:', dem_source)
            try:
                dem = riox.open_rasterio(dem_source, masked=True)
                dem_profile = dem_profiler_sampling(dem_source, geom, shape)
                print(dem_profile.shape)
            except Exception as e:
                print(e)
        except Exception as e:
            dem_profile = np.empty(shape)
            print(e)
        
        return (geom, geom_rep, geom_length, rolled_scs, rolled_acq, rolled_acq_scaled, rolled_acq_db, rolled_scs_db, max_width, max_height, xFormatter, yFormatter, dem_profile, dem, acq_pow_profile, scs_pow_profile)

    @staticmethod
    def coord_transformer(src_crs, dst_crs, x, y):
        transformer = Transformer.from_crs(src_crs, dst_crs)
        return transformer.transform(x, y)

    @staticmethod
    def enhancer(rolled_acq, rolled_acq_scaled):
        def apply_blur(image):
            return BLURfilter(image, blur=2)

        def apply_unsharp_mask(image):
            return unsharp_mask(image, radius=10, amount=2)

        def apply_fft(image):
            return FFTfilter(image)

        def apply_idwt(image, scaled_image):
            idwt_result = IDWTfilter(image, scaled_image, 95)
            return idwt_result[:, 0:image.shape[1]]

        def apply_minmax_scaler_normalize(image):
            return MinMaxScaler().fit_transform(normalize(image))

        def apply_log_gabor(image, log_gabor_resized):
            result = np.fft.ifft2(np.fft.fft2(image) * log_gabor_resized).real
            result = np.uint8(255 * (result - np.min(result)) / np.ptp(result))
            return result

        sigma = 50.0
        theta = 0.0
        frequency = 5
        bandwidth = 1.5
        log_gabor = log_gabor_filter(rolled_acq.shape, sigma, theta, frequency, bandwidth)
        log_gabor_resized = cv2.resize(log_gabor, (rolled_acq.shape[1], rolled_acq.shape[0]))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            blur_future = executor.submit(apply_blur, rolled_acq)
            scaled_blur_future = executor.submit(apply_blur, rolled_acq_scaled)
            
            usm_future = executor.submit(apply_unsharp_mask, rolled_acq)
            scaled_usm_future = executor.submit(apply_unsharp_mask, rolled_acq_scaled)
            
            fft_future = executor.submit(apply_fft, rolled_acq)
            scaled_fft_future = executor.submit(apply_fft, rolled_acq_scaled)
            
            idwt_future = executor.submit(apply_idwt, rolled_acq, rolled_acq_scaled)
            scaled_idwt_future = executor.submit(apply_idwt, rolled_acq_scaled, rolled_acq_scaled)

            gabor_future = executor.submit(apply_log_gabor, rolled_acq, log_gabor_resized)

            rolled_acq_blur = blur_future.result()
            rolled_acq_scaled_gausblur = scaled_blur_future.result()

            rolled_acq_usm = usm_future.result()
            rolled_acq_scaled_usm = scaled_usm_future.result()

            rolled_acq_fft = fft_future.result()
            rolled_acq_scaled_fft = scaled_fft_future.result()

            rolled_acq_usm_fft = apply_fft(rolled_acq_usm)
            rolled_acq_scaled_usm_fft = apply_fft(rolled_acq_scaled_usm)

            rolled_acq_idwt = idwt_future.result()
            rolled_acq_scaled_idwt = scaled_idwt_future.result()

            rolled_acq_idwt_scalednorm = apply_minmax_scaler_normalize(rolled_acq_idwt)
            rolled_acq_scaled_idwt_scalednorm = apply_minmax_scaler_normalize(rolled_acq_scaled_idwt)

            rolled_acq_idwt_scalednorm_blur = apply_blur(rolled_acq_idwt_scalednorm)
            rolled_acq_scaled_idwt_scalednorm_blur = apply_blur(rolled_acq_scaled_idwt_scalednorm)

            rolled_acq_gabor = gabor_future.result()
            rolled_acq_gabor_scaled = apply_minmax_scaler_normalize(rolled_acq_gabor)

        stack = np.stack((rolled_acq_blur,
                          rolled_acq_scaled_gausblur,
                          rolled_acq_usm,
                          rolled_acq_scaled_usm,
                          rolled_acq_fft,
                          rolled_acq_scaled_fft,
                          rolled_acq_usm_fft,
                          rolled_acq_scaled_usm_fft,
                          rolled_acq_idwt,
                          rolled_acq_scaled_idwt,
                          rolled_acq_idwt_scalednorm,
                          rolled_acq_scaled_idwt_scalednorm,
                          rolled_acq_idwt_scalednorm_blur,
                          rolled_acq_scaled_idwt_scalednorm_blur,
                          rolled_acq_gabor,
                          rolled_acq_gabor_scaled))

        stack_titles = ['Gaussian Blur', 'Scaled Gaussian Blur',
                        'Unsharp Mask', 'Scaled Unsharp Mask',
                        'FFT', 'Scaled FFT',
                        'Unsharp Mask + FFT', 'Scaled Unsharp Mask + FFT',
                        'IDWT', 'Scaled IDWT',
                        'IDWT + MinMaxScaler-normalizer', 'Scaled IDWT + MinMaxScaler-normalizer',
                        'IDWT + MinMaxScaler-normalizer + Gaussian Blur', 'Scaled IDWT + MinMaxScaler-normalizer + Gaussian Blur',
                        'Log-Gabor', 'Log-Gabor + MinMaxScaler-normalizer']

        return stack, stack_titles

