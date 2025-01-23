#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: giacomo.nodjoumi@hyranet.info - g.nodjoumi@jacobs-university.de
"""
from bs4 import BeautifulSoup as BS
from gpt import log
from gpt.search import ode
import geopandas as gpd
from utils.CRS import MARS2000, DST_CRS
def get_geom(boundingbox, track, acquisition_folder):
    
    ### **Extraction of radargram footprint (geom) from SHARAD shapefile, basemap and dem images from WCS**
    try:
        print('Trying local coverage file')
        coverage = f'{acquisition_folder}Coverage/mars_mro_sharad_usrdrv2_c0l.shp'    
        gdf = gpd.read_file(coverage)
        geom_gdf= gdf.loc[gdf.ProductId.str.contains(track.upper())].reset_index(drop=True)
    except Exception as e:
        print(e)
        Body = 'Mars'          
        Orbiter = 'MRO'
        Instrument = 'SHARAD'
        SHARADsets = ode.available_datasets('mars')
        SHARADsets.loc[Orbiter].loc[Instrument]
        Data = 'USRDRv2' # EDR, USRDRv2, RDR
        print('Quering ODE')

    
        results = ode.search(boundingbox, dataset=f'{Body}/{Orbiter}/{Instrument}/{Data}', match='all')
        products = ode.parse_products(results, 
                                      data_selectors={'Type':['product','browse'], 'FileName': ['JPEG$','TIF$','IMG$','DAT$','JP2$']}, 
                                      data_select_how='all')
        gdf = ode.to_geodataframe(products, geometry_field='Footprint_C0_geometry')
        print(gdf.shape)
        print('zeroo',geom_gdf)
        geom_gdf= gdf.loc[gdf.pdsid.str.contains(track.lower())].reset_index(drop=True)
        print('a',geom_gdf)
        geom_gdf = geom_gdf.drop('notes', axis=1)
        print('b',geom_gdf)
        geom_gdf = geom_gdf.loc[geom_gdf.Description.str.contains('PRODUCT DATA FILE')]
        print('c',geom_gdf)
    
        print('gdf_shape', gdf.shape[0])
        
        
        print('aaaaaaaaaaaaaaaaaaa',geom_gdf)


    
    geom_gdf.set_geometry = 'geometry'
    print(geom_gdf.geometry)    
    geom_gdf.crs = MARS2000
    geom_gdf.to_file(f'{acquisition_folder}/{track}_footprint.gpkg', driver='GPKG')
    print('ccccccccccccccccccccccccc')
    #geom = geom_gdf.loc[geom_gdf.index[0]].geometry
    geom = geom_gdf.loc[0].geometry
    print(geom.coords.xy)
    #src_crs = MARS2000#sharad_gdf.crs
    return(geom, geom_gdf)