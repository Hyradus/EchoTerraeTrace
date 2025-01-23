#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: giacomo.nodjoumi@hyranet.info
"""

from pyproj import CRS

MARS2000 = CRS.from_wkt('GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]')
DST_CRS = CRS.from_wkt('PROJCS["Mars_Equidistant_Cylindrical",GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Equidistant_Cylindrical"],PARAMETER["False_Easting",0],PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",0],PARAMETER["Standard_Parallel_1",0],UNIT["Meter",1]]')
MARS0360 = CRS.from_wkt('GEOGCRS["GCS_Mars",    DATUM["D_Mars",        ELLIPSOID["Mars_2000_IAU_IAG", 3396190, 169.8944472236118, LENGTHUNIT["metre", 1]]],    PRIMEM["Reference_Meridian", 0, ANGLEUNIT["degree", 1]],    CS[ellipsoidal, 2],        AXIS["longitude", east, ORDER[1], ANGLEUNIT["degree", 1, ID["EPSG", 9122]]],        AXIS["latitude", north, ORDER[2], ANGLEUNIT["degree", 1, ID["EPSG", 9122]]],    ID["EPSG", 49900]]')
