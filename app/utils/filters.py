#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: giacomo.nodjoumi@hyranet.info - g.nodjoumi@jacobs-university.de
"""

import pywt
import numpy as np
from scipy import ndimage, fftpack

def FFTfilter(img, keep_fraction=0.25):
    im_fft = fftpack.fft2(img)
    im_fft2 = im_fft.copy()

    r, c = im_fft2.shape
    im_fft2[int(r*keep_fraction):int(r*(1-keep_fraction))] = 0
    im_fft2[:, int(c*keep_fraction):int(c*(1-keep_fraction))] = 0

    return fftpack.ifft2(im_fft2).real


def FFTfilter_vertical(img, keep_fraction=0.25):
    im_fft = fftpack.fft2(img)
    im_fft2 = im_fft.copy()

    r, c = im_fft2.shape
    im_fft2[:, int(c*keep_fraction):int(c*(1-keep_fraction))] = 0

    return fftpack.ifft2(im_fft2).real


def BLURfilter(img, blur=1):
    return ndimage.gaussian_filter(img, blur)

def IDWTfilter(img, img_scaled, percentile):
    if img.dtype != 'uint8':
        img = (img * 255).astype('uint8')

    coeffs = pywt.dwt2(img, 'haar')
    noise_sigma = np.median(np.abs(coeffs[-1])) / 0.6745
    threshold = noise_sigma * np.sqrt(2 * np.log(img.size))
    percent = np.percentile(img_scaled * 255, percentile)
    coeffs = tuple(pywt.threshold(c, percent + threshold, mode='soft') for c in coeffs)

    return pywt.idwt2(coeffs, 'haar')

def log_gabor_filter(size, sigma, theta, frequency, bandwidth):
    cols, rows = size
    center_row, center_col = (rows - 1) / 2.0, (cols - 1) / 2.0

    u = np.arange(-center_col, center_col + 1)
    v = np.arange(-center_row, center_row + 1)
    u, v = np.meshgrid(u, v)

    radius = np.sqrt(u ** 2 + v ** 2)
    omega = np.log(frequency) / np.log(bandwidth)
    filter = np.exp(-0.5 * ((np.log(radius) / omega - np.log(sigma)) ** 2))
    filter *= np.exp(-0.5 * ((theta - np.angle(u + 1j * v)) ** 2) / (np.pi / 8) ** 2)

    return filter


