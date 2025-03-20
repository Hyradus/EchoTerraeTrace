#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title: 
@author: @author: Giacomo Nodjoumi g.nodjoumi@jacobs-unversity.de



Created on Wed Oct  7 20:39:25 2020
@author: @author: Giacomo Nodjoumi g.nodjoumi@jacobs-unversity.de
"""
import pandas as pd


def xDR_params():
    # param_col=['NAME', 'DATA_TYPE', 'START_BYTES', 'BYTES', 'ITEMS', 'ITEM_BYTES', 'RECORD_BYTES']
    RECORD_BYTES=24823
    PARAMETER = ['CENTRAL_FREQUENCY',
                 'SLOPE',
                 'SCET_FRAME_WHOLE',
                 'SCET_FRAME_FRAC',
                 'H_SCET_PAR',  
                 'VT_SCET_PAR', 
                 'VR_SCET_PAR', 
                 'DELTA_SCET_PAR',
                 'NA_SCET_PAR',
                 'ECHO_MODULUS_MINUS_F1_DIP',
                 'ECHO_PHASE_MINUS_F1_DIP',
                 'ECHO_MODULUS_ZERO_F1_DIP',
                 'ECHO_PHASE_ZERO_F1_DIP',
                 'ECHO_MODULUS_PLUS1_F1_DIP',
                 'ECHO_PHASE_PLUS1_F1_DIP',
                 'ECHO_MODULUS_MINUS_F2_DIP',
                 'ECHO_PHASE_MINUS_F2_DIP',
                 'ECHO_MODULUS_ZERO_F2_DIP',
                 'ECHO_PHASE_ZERO_F2_DIP',
                 'ECHO_MODULUS_PLUS1_F2_DIP',
                 'ECHO_PHASE_PLUS1_F2_DIP',
                 'GEOMETRY_EPHEMERIS_TIME',
                 'GEOMETRY_EPOCH',
                 'MARS_SOLAR_LONGITUDE',
                 'MARS_SUN_DISTANCE',
                 'ORBIT_NUMBER',
                 'TARGET_NAME',
                 'TARGET_SC_POSITION_VECTOR',
                 'SPACECRAFT_ALTITUDE',
                 'SUB_SC_LONGITUDE', 
                 'SUB_SC_LATITUDE',
                 'TARGET_SC_VELOCITY_VECTOR',
                 'TARGET_SC_RADIAL_VELOCITY',
                 'TARGET_SC_TANG_VELOCITY',
                 'LOCAL_TRUE_SOLAR_TIME',
                 'SOLAR_ZENITH_ANGLE',
                 'DIPOLE_UNIT_VECTOR',
                 'MONOPOLE_UNIT_VECTOR'] 
    
    START_BYTES = [1,9,13,17,19,23,27,31,35,
                   39,2087,4135,6183,8231,10279,
                   12327,14375,16423,18471,20519,22567,
                   24615,24623,24646,24654,24662,24666,24672,
                   24696,24704,24712,24720,24744,24752,24760,24768,24776,24800]
    START_BYTES = [x-1 for x in START_BYTES]
    BYTES = [8,4,4,2,4,4,4,4,4,
             2048,2048,2048,2048,2048,2048,
             2048,2048,2048,2048,2048,2048,
             8,23,8,8,4,6,24,8,8,8,24,8,8,8,8,24,24]
    ITEM_BYTES = [4,4,4,2,4,4,4,4,2,
                  4,4,4,4,4,4,
                  4,4,4,4,4,4,
                  8,1,8,8,4,1,8,8,8,8,8,8,8,8,8,8,8]
    # ITEMS = []
    # for i in range(len(BYTES)):
    #     item = BYTES[i]/ITEM_BYTES[i]
    #     ITEMS.append(item)
        
    # ITEMS = list(map(int, ITEMS))
    
    DATA_TYPE = ['float32','float32','uint32','uint16','float32','float32',
                 'float32','float32','uint16','float32','float32','float32',
                 'float32','float32','float32','float32','float32','float32',
                 'float32','float32','float32','float64','S23','float64','float64',
                 'uint32','S6','float64','float64','float64','float64','float64',
                 'float64','float64','float64','float64','float64','float64']
    # params = {
    #    param_col[0]: PARAMETER,
    #    param_col[1]: DATA_TYPE,
    #    param_col[2]: START_BYTES,
    #    param_col[3]: BYTES,
    #    param_col[4]: ITEMS,
    #    param_col[5]: ITEM_BYTES,
    #    param_col[6]: RECORD_BYTES
    # }
    # ParamDF = pd.DataFrame(columns=param_col)
    
    # ParamDF= pd.DataFrame.from_dict(params)
    
    ITEMS = [BYTES[i] // ITEM_BYTES[i] for i in range(len(BYTES))]

    # Packing everything into the dictionary for DataFrame
    params = {
        'NAME': PARAMETER,
        'DATA_TYPE': DATA_TYPE,
        'START_BYTES': START_BYTES,
        'BYTES': BYTES,
        'ITEMS': ITEMS,
        'ITEM_BYTES': ITEM_BYTES,
        'RECORD_BYTES': [RECORD_BYTES] * len(PARAMETER) 
        }
        
    # Creating the DataFrame directly from the dictionary
    ParamDF = pd.DataFrame(params)
    return(ParamDF)



def RAW_params():
    
    # param_col=['NAME', 'DATA_TYPE', 'START_BYTES', 'BYTES', 'ITEMS', 'ITEM_BYTES', 'RECORD_BYTES']
    RECORD_BYTES=15927
    PARAMETER = ['CENTRAL_FREQUENCY',
                 'SLOPE',
                 'SCET_FRAME_WHOLE',
                 'SCET_FRAME_FRAC',
                 'H_SCET_PAR',  
                 'VT_SCET_PAR', 
                 'VR_SCET_PAR', 
                 'DELTA_SCET_PAR',
                 'NA_SCET_PAR',
                 'ECHO_MODULUS_B1',
                 'ECHO_PHASE_B1',
                 'ECHO_MODULUS_B2',
                 'ECHO_PHASE_B2', 
                 'GEOMETRY_EPHEMERIS_TIME',
                 'GEOMETRY_EPOCH',
                 'MARS_SOLAR_LONGITUDE',
                 'MARS_SUN_DISTANCE',
                 'ORBIT_NUMBER',
                 'TARGET_NAME',
                 'TARGET_SC_POSITION_VECTOR',
                 'SPACECRAFT_ALTITUDE',
                 'SUB_SC_LONGITUDE', 
                 'SUB_SC_LATITUDE',
                 'TARGET_SC_VELOCITY_VECTOR',
                 'TARGET_SC_RADIAL_VELOCITY',
                 'TARGET_SC_TANG_VELOCITY',
                 'LOCAL_TRUE_SOLAR_TIME',
                 'SOLAR_ZENITH_ANGLE',
                 'DIPOLE_UNIT_VECTOR',
                 'MONOPOLE_UNIT_VECTOR'] 
    
    START_BYTES = [0,8,12,16,18,22,26,30,34,38,3958,7878,11798,15718,
                   15726,15749,15757,15765,15769,15775,15799,15807,15815,15823,
                   15847,15855,15863,15871,15879,15903]
    # START_BYTES = [x-1 for x in START_BYTES]
    ITEMS = [2,1,1,1,1,1,1,1,2,980,980,980,980,1,23,1,1,1,6,3,1,1,1,3,1,1,1,1,3,3]
    ITEM_BYTES =[4,4,4,2,4,4,4,4,2,4,4,4,4,8,1,8,8,4,1,8,8,8,8,8,8,8,8,8,8,8]
    BYTES = [8,4,4,2,4,4,4,4,4,3920,3920,3920,3920,8,23,8,8,4,6,24,8,8,8,24,8,8,8,8,24,24]
 
    # ITEMS = []
    # for i in range(len(BYTES)):
    #     item = BYTES[i]/ITEM_BYTES[i]
    #     ITEMS.append(item)
        
    # ITEMS = list(map(int, ITEMS))
    
    DATA_TYPE = ['float32','float32','uint32','uint16','float32','float32',
                 'float32','float32','uint16','float32','float32','float32',
                 'float32','float32','S23','float64','float64',
                 'uint32','S6','float64','float64','float64','float64','float64',
                 'float64','float64','float64','float64','float64','float64']
    # params = {
    #    param_col[0]: PARAMETER,
    #    param_col[1]: DATA_TYPE,
    #    param_col[2]: START_BYTES,
    #    param_col[3]: BYTES,
    #    param_col[4]: ITEMS,
    #    param_col[5]: ITEM_BYTES,
    #    param_col[6]: RECORD_BYTES
    # }
    # ParamDF = pd.DataFrame(columns=param_col)
    
    # ParamDF= pd.DataFrame.from_dict(params)
    ITEMS = [BYTES[i] // ITEM_BYTES[i] for i in range(len(BYTES))]

    # Packing everything into the dictionary for DataFrame
    params = {
        'NAME': PARAMETER,
        'DATA_TYPE': DATA_TYPE,
        'START_BYTES': START_BYTES,
        'BYTES': BYTES,
        'ITEMS': ITEMS,
        'ITEM_BYTES': ITEM_BYTES,
        'RECORD_BYTES': [RECORD_BYTES] * len(PARAMETER) 
        }
        
    # Creating the DataFrame directly from the dictionary
    ParamDF = pd.DataFrame(params)
    return(ParamDF)

def FM_params():
    # param_col=['NAME', 'DATA_TYPE', 'START_BYTES', 'BYTES', 'ITEMS', 'ITEM_BYTES','RECORD_BYTES']
    # param_col=['RecordBytes', 'Parameter', 'OffsetBytes', 'OffsetBits', 'Items', 'Precision', 'OutputPrecision', 'MachineFormat', 'ItemBytes', 'ItemBits']
    RECORD_BYTES=215
    PARAMETER = ['SCET_FRAME_WHOLE',
    'SCET_FRAME_FRAC',
    'GEOMETRY_EPHEMERIS_TIME',
    'GEOMETRY_EPOCH',
    'MARS_SOLAR_LONGITUDE',
    'MARS_SUN_DISTANCE',
    'ORBIT_NUMBER',
    'TARGET_NAME',
    'TARGET_SC_POSITION_VECTOR',
    'SPACECRAFT_ALTITUDE',
    'SUB_SC_LONGITUDE',
    'SUB_SC_LATITUDE',
    'TARGET_SC_VELOCITY_VECTOR',
    'TARGET_SC_RADIAL_VELOCITY',
    'TARGET_SC_TANG_VELOCITY',
    'LOCAL_TRUE_SOLAR_TIME',
    'SOLAR_ZENITH_ANGLE',
    'DIPOLE_UNIT_VECTOR',
    'MONOPOLE_UNIT_VECTOR']
    
    START_BYTES = [0,4,6,14,37,45,53,57,63,87,95,103,111,135,143,151,159,167,191]
    
    ITEMS = [1,1,1,23,1,1,1,6,3,1,1,1,3,1,1,1,1,3,3]
    DATA_TYPE = ['uint32','uint16','float64','S23','float64','float64','uint32','S6','float64','float64','float64','float64','float64','float64','float64','float64','float64','float64','float64']
    
    ITEM_BYTES= [4,2,8,1,8,8,4,1,8,8,8,8,8,8,8,8,8,8,8]
    
    BYTES=[]
    
    for i in range(len(ITEMS)):
        item = ITEMS[i]*ITEM_BYTES[i]
        BYTES.append(item)
   
    # params = {
    #    param_col[0]: PARAMETER,
    #    param_col[1]: DATA_TYPE,
    #    param_col[2]: START_BYTES,
    #    param_col[3]: BYTES,
    #    param_col[4]: ITEMS,
    #    param_col[5]: ITEM_BYTES,
    #    param_col[6]: RecordBytes
    # }
    # ParamDF = pd.DataFrame(columns=param_col)
    
    # ParamDF= pd.DataFrame.from_dict(params)
    ITEMS = [BYTES[i] // ITEM_BYTES[i] for i in range(len(BYTES))]

    # Packing everything into the dictionary for DataFrame
    params = {
        'NAME': PARAMETER,
        'DATA_TYPE': DATA_TYPE,
        'START_BYTES': START_BYTES,
        'BYTES': BYTES,
        'ITEMS': ITEMS,
        'ITEM_BYTES': ITEM_BYTES,
        'RECORD_BYTES': [RECORD_BYTES] * len(PARAMETER) 
        }
        
    # Creating the DataFrame directly from the dictionary
    ParamDF = pd.DataFrame(params)
    return(ParamDF)



def COH_params():
    # param_col=['NAME', 'DATA_TYPE', 'START_BYTES', 'BYTES', 'ITEMS', 'ITEM_BYTES', 'RECORD_BYTES']
    RECORD_BYTES=49312
    PARAMETER =['ostline',
                'f0',
                'theta_s',
                'frameid',
                'scetfw',
                'scetff',
                'Vt',
                'Vr',
                'NA',
                'x0',
                'y0',
                'z0',
                'alt0',
                'Vx0',
                'Vy0',
                'Vz0',
                'lon_0',
                'lat_0',
                'esm1f1r',
                'esm1f1i',
                'es00f1r',
                'es00f1i',
                'esp1f1r',
                'esp1f1i',
                'esm1f2r',
                'esm1f2i',
                'es00f2r',
                'es00f2i',
                'esp1f2r',
                'esp1f2i'] 
    
    START_BYTES = [0,
                   8,24,32,40,48,56,64,72,88,96,104,112,
                   120,128,136,144,152,160,4256,8352,12448,
                   16544,20640,24736,28832,32928,37024,41120,45216]
    
    # START_BYTES = [x-1 for x in START_BYTES]
    # BYTES = [8,4,4,2,4,4,4,4,4,
    #          2048,2048,2048,2048,2048,2048,
    #          2048,2048,2048,2048,2048,2048,
    #          8,23,8,8,4,6,24,8,8,8,24,8,8,8,8,24,24]
    
    ITEMS = [1,2,1,1,1,1,1,1,2,1,1,1,1,1,1,1,1,1,
                  512,512,512,512,512,512,512,512,512,512,512,512]
    ITEM_BYTES = 8
    BYTES = [item*ITEM_BYTES for item in ITEMS]
    # BYTES = [el[0]*el[1] for el in list(zip(ITEMS, ITEM_BYTES))]
    # ITEMS = []
    # for i in range(len(BYTES)):
    #     item = BYTES[i]/ITEM_BYTES[i]
    #     ITEMS.append(item)
        
    # ITEMS = list(map(int, ITEMS))
    
    # DATA_TYPE = ['float32','float32','uint32','uint16','float32','float32',
    #              'float32','float32','uint16','float32','float32','float32',
    #              'float32','float32','float32','float32','float32','float32',
    #              'float32','float32','float32','float64','S23','float64','float64',
    #              'uint32','S6','float64','float64','float64','float64','float64',
    #              'float64','float64','float64','float64','float64','float64']
    DATA_TYPE = ['double' for el in ITEMS]
    
    
    
    # params = {
    #    param_col[0]: PARAMETER,
    #    param_col[1]: DATA_TYPE,
    #    param_col[2]: START_BYTES,
    #    param_col[3]: BYTES,
    #    param_col[4]: ITEMS,
    #    param_col[5]: ITEM_BYTES,
    #    param_col[6]: RECORD_BYTES
    # }
    # ParamDF = pd.DataFrame(columns=param_col)
    
    # ParamDF= pd.DataFrame.from_dict(params)
    
    # ITEMS = [BYTES[i] // ITEM_BYTES for i in range(len(ITEM_BYTES))]

    # Packing everything into the dictionary for DataFrame
    params = {
        'NAME': PARAMETER,
        'DATA_TYPE': DATA_TYPE,
        'START_BYTES': START_BYTES,
        'BYTES': BYTES,
        'ITEMS': ITEMS,
        'ITEM_BYTES': ITEM_BYTES,
        'RECORD_BYTES': [RECORD_BYTES] * len(PARAMETER) 
        }
        
    # Creating the DataFrame directly from the dictionary
    ParamDF = pd.DataFrame(params)
    return(ParamDF)


import pandas as pd

def NCSIM_params():
        # Define the data
    RecordBytes = 4343

    Parameter = [
        'CENTRAL_FREQUENCY', 'SLOPE', 'SCET_FRAME_WHOLE', 'SCET_FRAME_FRAC', 'H_SCET_PAR',
        'VT_SCET_PAR', 'VR_SCET_PAR', 'DELTA_S_SCET_PAR', 'NA_SCET_PAR', 'SIMULATED_ECHO_B1',
        'SIMULATED_ECHO_B2', 'GEOMETRY_EPHEMERIS_TIME', 'GEOMETRY_EPOCH', 'MARS_SOLAR_LONGITUDE',
        'MARS_SUN_DISTANCE', 'ORBIT_NUMBER', 'TARGET_NAME', 'TARGET_SC_POSITION_VECTOR',
        'SPACECRAFT_ALTITUDE', 'SUB_SC_LONGITUDE', 'SUB_SC_LATITUDE', 'TARGET_SC_VELOCITY_VECTOR',
        'TARGET_SC_RADIAL_VELOCITY', 'TARGET_SC_TANG_VELOCITY', 'LOCAL_TRUE_SOLAR_TIME',
        'SOLAR_ZENITH_ANGLE', 'DIPOLE_UNIT_VECTOR', 'MONOPOLE_UNIT_VECTOR'
    ]

    OffsetBytes = [
        0, 8, 12, 16, 18, 22, 26, 30, 34, 38, 2086, 4134, 4142, 4165, 4173, 4181, 4185, 4191,
        4215, 4223, 4231, 4239, 4263, 4271, 4279, 4287, 4295, 4319
    ]

    OffsetBits = [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ]

    Items = [
        2, 1, 1, 1, 1, 1, 1, 1, 2, 512, 512, 1, 23, 1, 1, 1, 6, 3, 1, 1, 1, 3, 1, 1, 1, 1, 3, 3
    ]

    Precision = [
        'float32', 'float32', 'uint32', 'uint16', 'float32', 'float32', 'float32', 'float32',
        'uint16', 'float32', 'float32', 'float64', 'S23', 'float64', 'float64', 'uint32', 'S6',
        'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64',
        'float64', 'float64', 'float64'
    ]

    OutputPrecision = [
        'float32', 'float32', 'uint32', 'uint16', 'float32', 'float32', 'float32', 'float32',
        'uint16', 'float32', 'float32', 'float64', 'str', 'float64', 'float64', 'uint32', 'str',
        'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64', 'float64',
        'float64', 'float64', 'float64'
    ]

    MachineFormat = [
        'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le',
        'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le',
        'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le',
        'ieee-le', 'ieee-le', 'ieee-le', 'ieee-le'
    ]

    ItemBytes = [
        4, 4, 4, 2, 4, 4, 4, 4, 2, 4, 4, 8, 1, 8, 8, 4, 1, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8
    ]

    ItemBits = [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ]

    # Calculate BYTES from ItemBytes and Items
    BYTES = [ItemBytes[i] * Items[i] for i in range(len(Items))]

    # Packing everything into the dictionary for DataFrame
    params = {
        'NAME': Parameter,
        'DATA_TYPE': Precision,
        'START_BYTES': OffsetBytes,
        'START_BITS': OffsetBits,
        'BYTES': BYTES,
        'ITEMS': Items,
        'ITEM_BYTES': ItemBytes,
        'ITEM_BITS': ItemBits,
        'RECORD_BYTES': [RecordBytes] * len(Parameter)
    }
        
    # Creating the DataFrame directly from the dictionary
    ParamDF = pd.DataFrame(params)
    return ParamDF


def xDR_DF(ParamDF):
    #columns = ['Type','Orbit','OpMode','InsState','DataForm','Target'] + ParamDF['NAME'].tolist()
    columns = ['name','proj4'] + ParamDF['NAME'].tolist()
    xDR_df = pd.DataFrame(columns=columns)
    return(xDR_df)

def gdf_split(geodf, latitude):
    
    if latitude >= 0:
        geodf = geodf.drop(geodf[geodf['SUB_SC_LATITUDE'] <= latitude].index).reset_index(drop=True)
    else:
        geodf = geodf.drop(geodf[geodf['SUB_SC_LATITUDE'] >= latitude].index).reset_index(drop=True)
    
    return(geodf)
  
def geoDF2file(geodf, areatype, crs, path, drvr):
    if geodf.shape[0] == 0:
        print('skip')
    else:
        tgt = geodf['TARGET_NAME'][0].strip()
        n_orbits = str(geodf.shape[0])
        layername = tgt +'' + areatype + ' tracks'
        if drvr in['GPKG', 'gpkg']:
            driver = 'GPKG'
            ext = '.gpkg'
        else: 
            driver = 'ESRI Shapefile'
            ext = '.shp'
        name = tgt +'_'+n_orbits + '_orbits_'+ areatype + ext
        savename = path+'/'+name
        #geodf = geodf.to_crs(crs)
        geodf.crs = crs[0]
        if areatype == 'Complete':
            pass
        else:
            geodf.crs = crs[0]
            geodf.to_crs(crs[1])
        
        geodf.to_file(savename, layer=layername, driver=driver)

# def DF_DROP(df, drtype):
#     if drtype in ['FM', 'fm']:
#         df.drop(['TARGET_SC_POSITION_VECTOR',
#         'TARGET_SC_VELOCITY_VECTOR',
#         'DIPOLE_UNIT_VECTOR',
#         'MONOPOLE_UNIT_VECTOR'],
#          axis=1, inplace=True)
#     else:
#         df.drop(['TARGET_SC_POSITION_VECTOR',
#         'TARGET_SC_VELOCITY_VECTOR',
#         'DIPOLE_UNIT_VECTOR',
#         'MONOPOLE_UNIT_VECTOR',
#         'ECHO_MODULUS_MINUS_F1_DIP',
#         'ECHO_PHASE_MINUS_F1_DIP',
#         'ECHO_MODULUS_ZERO_F1_DIP',
#         'ECHO_PHASE_ZERO_F1_DIP',
#         'ECHO_MODULUS_PLUS1_F1_DIP',
#         'ECHO_PHASE_PLUS1_F1_DIP',
#         'ECHO_MODULUS_MINUS_F2_DIP',
#         'ECHO_PHASE_MINUS_F2_DIP',
#         'ECHO_MODULUS_ZERO_F2_DIP',
#         'ECHO_PHASE_ZERO_F2_DIP',
#         'ECHO_MODULUS_PLUS1_F2_DIP',
#         'ECHO_PHASE_PLUS1_F2_DIP',
#         'GEOMETRY_EPHEMERIS_TIME',
#         'CENTRAL_FREQUENCY',
#         'NA_SCET_PAR'],
#         axis=1, inplace=True)
        
#     return(df)


def DF_drop(df, drtype):
    if drtype in ['FM', 'fm']:
        df.drop(['TARGET_SC_POSITION_VECTOR',
        'TARGET_SC_VELOCITY_VECTOR',
        'DIPOLE_UNIT_VECTOR',
        'MONOPOLE_UNIT_VECTOR'],
         axis=1, inplace=True)
    elif drtype in ['EDR', 'edr','RDR', 'rdr']:
        df.drop(['TARGET_SC_POSITION_VECTOR',
        'TARGET_SC_VELOCITY_VECTOR',
        'DIPOLE_UNIT_VECTOR',
        'MONOPOLE_UNIT_VECTOR',
        'ECHO_MODULUS_MINUS_F1_DIP',
        'ECHO_PHASE_MINUS_F1_DIP',
        'ECHO_MODULUS_ZERO_F1_DIP',
        'ECHO_PHASE_ZERO_F1_DIP',
        'ECHO_MODULUS_PLUS1_F1_DIP',
        'ECHO_PHASE_PLUS1_F1_DIP',
        'ECHO_MODULUS_MINUS_F2_DIP',
        'ECHO_PHASE_MINUS_F2_DIP',
        'ECHO_MODULUS_ZERO_F2_DIP',
        'ECHO_PHASE_ZERO_F2_DIP',
        'ECHO_MODULUS_PLUS1_F2_DIP',
        'ECHO_PHASE_PLUS1_F2_DIP',
        'GEOMETRY_EPHEMERIS_TIME',
        'CENTRAL_FREQUENCY',
        'NA_SCET_PAR'],
        axis=1, inplace=True)
    elif drtype in ['RAW', 'raw']:
        df.drop(['TARGET_SC_POSITION_VECTOR',
        'TARGET_SC_VELOCITY_VECTOR',
        'DIPOLE_UNIT_VECTOR',
        'MONOPOLE_UNIT_VECTOR',
        'ECHO_MODULUS_B1',
        'ECHO_PHASE_B1',
        'ECHO_MODULUS_B2',
        'ECHO_PHASE_B2',
        'GEOMETRY_EPHEMERIS_TIME',
        'CENTRAL_FREQUENCY',
        'NA_SCET_PAR'],
        axis=1, inplace=True)
        
    return(df)

def geom_df():
    param_col=['RecordBytes', 'Parameter', 'OffsetBytes', 'OffsetBits', 'Items', 'Precision', 'OutputPrecision', 'MachineFormat', 'ItemBytes', 'ItemBits', 'RecordBytes']
    RecordBytes=215
    Parameter = ['SCET_FRAME_WHOLE',
    'SCET_FRAME_FRAC',
    'GEOMETRY_EPHEMERIS_TIME',
    'GEOMETRY_EPOCH',
    'MARS_SOLAR_LONGITUDE',
    'MARS_SUN_DISTANCE',
    'ORBIT_NUMBER',
    'TARGET_NAME',
    'TARGET_SC_POSITION_VECTOR',
    'SPACECRAFT_ALTITUDE',
    'SUB_SC_LONGITUDE',
    'SUB_SC_LATITUDE',
    'TARGET_SC_VELOCITY_VECTOR',
    'TARGET_SC_RADIAL_VELOCITY',
    'TARGET_SC_TANG_VELOCITY',
    'LOCAL_TRUE_SOLAR_TIME',
    'SOLAR_ZENITH_ANGLE',
    'DIPOLE_UNIT_VECTOR',
    'MONOPOLE_UNIT_VECTOR']
    
    OffsetBytes = [0,4,6,14,37,45,53,57,63,87,95,103,111,135,143,151,159,167,191]
    OffsetBits = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    Items = [1,1,1,23,1,1,1,6,3,1,1,1,3,1,1,1,1,3,3]
    Precision = ['uint32','uint16','float64','S23','float64','float64','uint32','S6','float64','float64','float64','float64','float64','float64','float64','float64','float64','float64','float64']
    OutputPrecision = ['uint32','uint16','float64','S23','float64','float64','uint32','S6','float64','float64','float64','float64','float64','float64','float64','float64','float64','float64','float64']
    MachineFormat= ['ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be','ieee-be']
    ItemBytes= [4,2,8,1,8,8,4,1,8,8,8,8,8,8,8,8,8,8,8]
    ItemBits = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    
    params = {
       param_col[0]: RecordBytes,
       param_col[1]: Parameter,
       param_col[2]: OffsetBytes,
       param_col[3]: OffsetBits,
       param_col[4]: Items,
       param_col[5]: Precision,
       param_col[6]: OutputPrecision,
       param_col[7]: MachineFormat,
       param_col[8]: ItemBytes,
       param_col[9]: ItemBits,
       param_col[10]: RecordBytes
    }
    GeomDf = pd.DataFrame(columns=param_col)
    
    GeomDf= pd.DataFrame.from_dict(params)

    return(GeomDf)