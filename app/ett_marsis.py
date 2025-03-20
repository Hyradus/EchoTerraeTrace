import numpy as np
import os
import pathlib
from pathlib import Path
import cv2 as cv
from numpy import frombuffer as fbuff
from multiprocessing import Pool
from sklearn.preprocessing import MinMaxScaler, StandardScaler, normalize
from skimage.filters import unsharp_mask
import matplotlib.pyplot as plt
from bokeh.io import curdoc
from bokeh.plotting import figure as fg
from bokeh.plotting import show
from bokeh.layouts import column, row
from bokeh.models import CustomJS, Span, RangeTool, Div, BoxAnnotation, PolyDrawTool, ColumnDataSource, PolyDrawTool, Callback, Select, BBoxTileSource, Range1d, CrosshairTool, Span, Slider, Dropdown, TextInput, HoverTool, CustomJSTickFormatter, ColumnDataSource, Button
from joblib import Parallel, delayed
from shapely.geometry import LineString, box, Point, MultiLineString
import pyproj
from pyproj import CRS, Transformer
import geopandas as gpd
import rioxarray
import rasterio
from rasterio.windows import from_bounds
from shapely.ops import transform
from scipy import fftpack
import cv2
import rioxarray as riox
import pandas as pd
from utils.dataPlots import Formatters
from utils.dataStructs import track_dict_builder
from utils.profilers import dem_profiler_xarray
from utils.marsisUtils import process_parameter
from utils.filters import FFTfilter, FFTfilter_vertical, BLURfilter, IDWTfilter, log_gabor_filter
from utils.genUtils import get_paths
from utils.DFUtils import xDR_params, COH_params, NCSIM_params
from scipy.ndimage import maximum_filter
import math
from skimage.restoration import denoise_tv_chambolle
from rasterio.coords import BoundingBox as BB
from concurrent.futures import ProcessPoolExecutor, as_completed
from utils.CRS import MARS2000, DST_CRS, MARS0360
from utils.saveUtils import subsurface_saver, autopicker

# Define constants
plot_size = 1500
hgt = 500
basemap_layerid = 'Mars_Viking_MDIM21_ClrMosaic_global_232m-cog'
wcs_url = 'https://explore.hyranet.info/geoserver/ows?service=WCS'
dem_layerid = 'Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2-cog'
min_Lon, min_Lat, max_Lon, max_Lat = -180, -90, 180, 90
bounding_box = [min_Lon, min_Lat, max_Lon, max_Lat]

# Data Directory Setup
home = '/app/'  # Replace with `Path.home()` if needed  # Replace with `Path.home()` if needed
print(f"Home Directory: {home}")

# Default data directory
data_dir = '/Data/MARSIS/'
data_dir = '/home/hyradus/SyncThing/SyncData/Zephyria_Planum/'

def process_images(indexes, full_parameters, ParamDF, datatype):
    
    amp_imgs, pha_imgs, titles, frequencies,sc_altitude, lon, lat = [], [], [], [], [], [], []
    
    for idx in indexes:

        if idx == 0:
            print('0',idx)
            frequencies.append(np.array(full_parameters[idx]))
        elif idx==28:
            print('28',idx)
            print(ParamDF.iloc[idx].NAME)
            sc_altitude.append(np.array(full_parameters[idx]))
        elif idx==29:
            lon.append(np.array(full_parameters[idx]))
        elif idx==30:
            lat.append(np.array(full_parameters[idx]))
        else:
            print(idx)
            img = np.array(full_parameters[idx])
            name = ParamDF.iloc[idx].NAME
            if datatype == 'ncsim' or (datatype == 'xdr' and idx % 2 != 0) or (datatype != 'ncsim' and datatype != 'xdr' and idx % 2 == 0):
                amp_imgs.append(img)
                titles.append(name)
            else:
                pha_imgs.append(img)
            
    return amp_imgs, pha_imgs, titles, frequencies, sc_altitude, lon, lat


def reader(File, ParamDF, indexes, datatype):
    # Pre-calculate FileSize and FileRecord
    FileSize = pathlib.Path(File).stat().st_size
    RecordBytes = ParamDF['RECORD_BYTES'][0]
    FileRecord = FileSize // RecordBytes
    
    # Prepare a placeholder for results
    results = [None] * len(ParamDF['START_BYTES'])
    
    with ProcessPoolExecutor() as executor:
        future_to_idx = {
            executor.submit(process_parameter, File, i, ParamDF, FileRecord, RecordBytes): i 
            for i in range(len(ParamDF['START_BYTES']))
        }
        
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as exc:
                print(f'Generated an exception: {exc}')
    
    full_parameters, short_parameters = zip(*results)
    
    # Process images based on datatype
    amp_imgs, pha_imgs, titles, frequencies, sc_altitude, lon, lat = process_images(indexes, full_parameters, ParamDF, datatype)
    
    return amp_imgs, pha_imgs, titles, frequencies, sc_altitude, lon, lat
    

    
def basemap(geom, data_dir, basemap_layerid, dem_layerid, wcs_url):    
    track = track_select.value    
    bounding_box= BB(min(geom.xy[0]), min(geom.xy[1]), max(geom.xy[0]), max(geom.xy[1]))
    # define basemap and dem filename
    bmap_savename = f"{data_dir}/Basemaps/{basemap_layerid}-crop_track-{track}.tiff"
    dem_savename = f"{data_dir}/Basemaps/{dem_layerid}-crop_track-{track}.tiff"
    # check if already downloaded and download if missing
    map_error = None
    if not os.path.isfile(bmap_savename):        
        try:           
            wcs_get(wcs_url, basemap_layerid, bounding_box, bmap_savename, resx=0.025, resy=0.025)
        except Exception as e:
            map_error = e
            bmap_savename = None
            print(e)
            pass
    dem_error = None
    if not os.path.isfile(dem_savename):

        try:           
            wcs_get(wcs_url, dem_layerid, bounding_box, dem_savename, resx=0.025, resy=0.025)
        except Exception as e:
            dem_error = e
            print(e)
            dem_savename = None
            pass
    return(bmap_savename, dem_savename)

def basemap(geom, data_dir, basemap_layerid, dem_layerid, wcs_url):    
    track = track_select.value    
    bounding_box = BB(min(geom.xy[0]), min(geom.xy[1]), max(geom.xy[0]), max(geom.xy[1]))

    # Define basemap and dem filenames
    bmap_savename = f"{data_dir}/{basemap_layerid}-crop_track-{track}.tiff"
    dem_savename = f"{data_dir}/{dem_layerid}-crop_track-{track}.tiff"

    basemap_dir = os.path.join(data_dir,'Basemaps')
    # Define paths to check existing files in basemap_dir
    basemap_layerid_file = f'{basemap_layerid}.tiff'
    bmap_existing = os.path.join(basemap_dir, bmap_savename)
    print(bmap_existing)
    dem_layerid_file = f'{dem_layerid}.tiff'
    dem_existing = os.path.join(basemap_dir, dem_savename)
    print('AAAAAAAAAAAAAAAAAAAAAAA',dem_existing, dem_layerid_file)
    
    # Function to read, crop, and save existing file using rioxarray or rasterio
    def crop_and_save(input_file, output_file, bounding_box):
        try:
            with rioxarray.open_rasterio(input_file) as dataset:
                clipped = dataset.rio.clip_box(
                    minx=bounding_box.left, 
                    miny=bounding_box.bottom, 
                    maxx=bounding_box.right, 
                    maxy=bounding_box.top
                )
                clipped.rio.to_raster(output_file)
            return True
        except Exception as e:
            print(f"Error cropping and saving {input_file}: {e}")
            return False

    # Check if basemap_layerid file exists in basemap_dir
    if os.path.isfile(bmap_existing):
        print('Reading from file', bmap_existing)
        #if not crop_and_save(bmap_existing, bmap_savename, bounding_box):
        #    bmap_savename = None
    else:
        try:           
            wcs_get(wcs_url, basemap_layerid, bounding_box, bmap_savename, resx=0.025, resy=0.025)
        except Exception as e:
            bmap_savename = None
            print(f"Error downloading basemap: {e}")
            pass

    # Check if dem_layerid file exists in basemap_dir
    if os.path.isfile(dem_existing):
        print('Reading from file', dem_existing)
        #if not crop_and_save(dem_existing, dem_savename, bounding_box):
        #    dem_savename = None
    else:
        try:           
            wcs_get(wcs_url, dem_layerid, bounding_box, dem_savename, resx=0.025, resy=0.025)
        except Exception as e:
            dem_savename = None
            print(f"Error downloading DEM: {e}")
            pass

    return bmap_savename, dem_savename



def process_scs_file(file):
    base_name, _ = os.path.splitext(os.path.basename(file))
    base_path = os.path.dirname(file)

    cos_name = f"{base_name}_COS.DAT"
    cos_file = os.path.join(base_path, cos_name)

    ncsim_name = f"I_{base_name[2:]}_NCSIM.DAT"
    ncsim_file = os.path.join(base_path, ncsim_name)

    def process_file(file_path, ParamDF, indexes, datatype='coh'):            
        scss = reader(file_path, ParamDF, indexes, datatype)            
        if len(scss) >1:
            stack_scs = np.stack(scss[0])
            stack_scs_pha = None
        else:
            stack_scs = scss
        scs_titles = scss[2]        

        return stack_scs, stack_scs_pha, scs_titles


    try:
        ParamDF = COH_params()
        indexes = np.arange(18, 30)
        print(cos_file)
        stack_scs, stack_scs_pha, scs_titles = process_file(cos_file, ParamDF, indexes,'coh')
        print('COH DATA FOUND!')
        return stack_scs, stack_scs_pha, scs_titles#, stack_scs_maxs
    except Exception as e:
        print(e)
        print('Searching NCSIM')
        try:
            ParamDF = NCSIM_params()
            #print(ParamDF)
            indexes = np.arange(9, 11)
            print(ncsim_file)
            stack_scs, stack_scs_pha, scs_titles = process_file(ncsim_file, ParamDF, indexes,'ncsim')      
            
            print('NCSIM DATA FOUND!', stack_scs.shape)
            return stack_scs, stack_scs_pha, scs_titles#, stack_scs_maxs
        except Exception as e:
            stack_scs = np.empty_like(stack_xdr)
            stack_scs_pha = np.empty_like(stack_xdr)
            scs_titles = ['no scs' for _ in xDRs[2]]
            #stack_scs_maxs = [0 for _ in stack_xdr_maxs]
            print('NO SCS DATA FOUND!', e)                
            return stack_scs, None, scs_titles#, stack_scs_maxs
    return stack_scs, stack_scs_pha, scs_titles#, stack_scs_maxs


def scale_3d_array(array, scaler_type='minmax'):
    """
    Function to scale a 3D array using either MinMaxScaler or StandardScaler.
    
    Parameters:
    - array: 3D numpy array of shape (x, width, height)
    - scaler_type: str, either 'minmax' or 'standard' to choose the scaler type
    
    Returns:
    - scaled_array: 3D numpy array, same shape as input array but scaled
    """
    # Get the shape of the array
    x, width, height = array.shape
    
    # Initialize the scaler based on the scaler_type flag
    if scaler_type == 'minmax':
        scaler = MinMaxScaler()
    elif scaler_type == 'standard':
        scaler = StandardScaler()
    else:
        raise ValueError("scaler_type must be either 'minmax' or 'standard'")
    
    # Create an empty array to store the scaled data
    scaled_array = np.zeros_like(array)
    
    # Loop over the first dimension and scale each (width, height) slice
    for i in range(x):
        # Reshape the (width, height) array to (width*height, 1)
        reshaped_data = array[i].reshape(-1, 1)
        
        # Fit and transform the data
        scaled_reshaped_data = scaler.fit_transform(reshaped_data)
        
        # Reshape the scaled data back to (width, height) and store it
        scaled_array[i] = scaled_reshaped_data.reshape(width, height)
    
    return scaled_array

def arrayscaler(array):
    for jj in range(array.shape[0]):
        for ii in range(array.shape[2]):
                array[jj,:,ii]  = array[jj,:,ii] - array[jj,:,ii].max()
                array[jj,:,ii]  = array[jj,:,ii] - array[jj,:,ii].max()
    return(array)

def processor(file, data_dir, basemap_layerid, dem_layerid, wcs_url,boundingbox):
    
    from utils.dataPlots import Formatters
    from utils.dataStructs import track_dict_builder
    from utils.profilers import dem_profiler_xarray, power_profiler
    from utils.marsisUtils import process_parameter
    from utils.DFUtils import xDR_params,  COH_params, NCSIM_params
    global geom
    global geom_length    
    global cut_geom
    global subsurface_df
    global dem_profile
    global frequencies_arrays
    global sc_altitudes
    global source
    global xdr_image_f1
    global xdr_image_f1_db
    global xdr_image_f2
    global xdr_image_f2_db
    global xdr_image_f1_ori
    global xdr_image_f1_db_ori
    global xdr_image_f2_ori
    global xdr_image_f2_db_ori
    global stack_xdr_scaled
    global dem
    global stack_scs
    global stack_scs_db
    global stack_scs_scaled
    global scs_image
    global max_width
    global max_height
    global geom
    global geom_length    
    global subsurface_df
    global dem_profile
    global p_image_xdr
    global stack_processed
    global selected_track
    track = track_select.value    
    width = Span(dimension="width")
    height = Span(dimension="height")
    cht = CrosshairTool(overlay=[width, height])
    cht2 = CrosshairTool(overlay=[height,width])
    
    # Processing xDR
    file = f"{data_dir}/{os.path.basename(file)}"
    #track, _ = os.path.splitext(os.path.basename(file))
    selected_track = track_select.value
    print(selected_track)

    ParamDF = xDR_params()
    indexes = np.arange(9, 20)
    indexes = np.insert(indexes, 0, 0)
    indexes = np.append(indexes, [28,29,30])
    
    xDRs = reader(file, ParamDF, indexes, 'xdr')
    #print(xDRs[0])
    frequencies_arrays = xDRs[3]
    sc_altitudes = xDRs[4][0]
    stack_xdr = np.stack(xDRs[0])

    max_width = stack_xdr[0].shape[1]
    #stack_xdr_scaled_maxs = []
    print(stack_xdr.shape)

    stack_xdr_scaled = stack_xdr.copy()
    stack_xdr_scaled = arrayscaler(stack_xdr_scaled)

    xdr_titles = xDRs[2]    
    
    xdr_image_f1 = stack_xdr_scaled[1,:, :]
    xdr_image_f2 = stack_xdr_scaled[4,:, :]
    xdr_image_f1_db = stack_xdr_scaled[1,:, :]
    xdr_image_f2_db = stack_xdr_scaled[4,:, :]
    xdr_image_f1_ori = stack_xdr[1,:, :]
    xdr_image_f2_ori = stack_xdr[4,:, :]
    xdr_image_f1_db_ori = stack_xdr[1,:, :]
    xdr_image_f2_db_ori = stack_xdr[4,:, :]
    
    
    p_image_xdr = fg(title=f'{xdr_titles[0]}',width=plot_size//2, height=hgt//2,  y_range=(xdr_image_f1.shape[0],0),tools=[' wheel_zoom,pan,box_zoom,reset',cht])
    stack_xdr_scaled_source = ColumnDataSource(data=dict(image=[xdr_image_f1]))
    render_xdr = p_image_xdr.image(image='image',source=stack_xdr_scaled_source, x=0, y=0, dw=xdr_image_f1.shape[1], dh=xdr_image_f1.shape[0], palette='Viridis256')


    def update_xdr(attr, old, new):
            index = slider_xdr.value                
            p_image_xdr.title.text=f'{xdr_titles[index]}: {selected_track}'        
            render_xdr.data_source.data['image']  = [np.array(stack_xdr_scaled[index,:, :])]

    slider_xdr = Slider(start=0, end=5, value=0, step=1, title="RGRM Amplitude Index")
    slider_xdr.on_change('value', update_xdr)
    
    ####### Create geometry footprint
    
    lon = xDRs[5][0].tolist()#[3][29][0]
    lat = xDRs[6][0].tolist()#[[30][0]
    print('Len lon, lat arrays', len(lon), len(lat))
    # Function to normalize longitude
    
    #def normalize_longitude(lon):
    #    if lon > 180:
    #        return lon - 360
    #    else:
    #        return lon
    #lon = [normalize_longitude(l) for l in lon]
    #geom = LineString(list(zip(lon,lat)))
    
    #transformer1 = Transformer.from_crs(MARS0360, DST_CRS, always_xy=True)
    #geom = transform(transformer1.transform, geom1)
    #print('GEOM COORDINATES')
    #print(f'LAT: {lat}')
    #print(f'LON: {lon}')
    #print(max(lon))


    ################### BIG EDIT

    # Function to normalize longitude to [-180, 180] range
    def normalize_longitude(lon):
        if lon > 180:
            return lon - 360
        elif lon < -180:
            return lon + 360
        else:
            return lon
    
    # Function to split and normalize geometry if it crosses the antimeridian
    def split_and_normalize_geometry(lon, lat):
        split_geometries = []
        current_line = []
        
        for i, (l, t) in enumerate(zip(lon, lat)):
            normalized_lon = normalize_longitude(l)
            
            if current_line:
                prev_lon = current_line[-1][0]
                # Check if there's a jump larger than 180 degrees (i.e., across the antimeridian)
                if abs(prev_lon - normalized_lon) > 180:
                    # If crossing the antimeridian, split the geometry here
                    if len(current_line) > 1:
                        split_geometries.append(LineString(current_line))
                    current_line = []
            
            current_line.append((normalized_lon, t))
        
        # Append the last segment if it has more than 1 point
        if len(current_line) > 1:
            split_geometries.append(LineString(current_line))
        
        # Return a MultiLineString if there are multiple geometries
        if len(split_geometries) > 1:
            return MultiLineString(split_geometries)
        elif len(split_geometries) == 1:
            return split_geometries[0]
        else:
            return None  # No valid geometry
        geom = split_and_normalize_geometry(lon, lat)


    # Split and normalize the geometry based on longitude
    geom = split_and_normalize_geometry(lon, lat)
    print('GEOM', geom)
    # Convert geometry to GeoDataFrame for easier handling
    gdf = gpd.GeoDataFrame(geometry=[geom], crs="ESRI:104905")  # Update CRS accordingly
    gdf.to_file(f'{data_dir}/{track}_geometry.gpkg', driver='GPKG')
    
    # Reproject to match DEM CRS (if different)
    
    
    


    ########################### END BIG EDIT

    transformer = Transformer.from_crs(MARS2000, DST_CRS, always_xy=True)
    transformed_geom = transform(transformer.transform, geom)
    
    geom_length = transformed_geom.length//1000
    print('Geom_length',geom_length)
    xFormatter, _ , yFormatter = Formatters(geom_length, stack_xdr_scaled.shape[2])
    
    min_Lon, min_Lat, max_Lon, max_Lat = boundingbox
    bbox = box(min_Lon, min_Lat, max_Lon, max_Lat)
    intersections = geom.intersection(bbox)
    
    # Function to map intersection points to pixel coordinates
    def map_to_pixels(point, geom, max_width):
        distance_along_line = geom.project(point)
        x_pixel = (distance_along_line / geom.length) * max_width
        return x_pixel
    
    # Initialize list to hold pixel coordinates
    pixels = []
    
    
    
    # Initialize the new geometry (this will hold the trimmed line)
    new_geom = None
    
    if intersections.geom_type == 'LineString':
        # Extract the start and end points of the intersecting segment
        start_point = Point(intersections.coords[0])
        end_point = Point(intersections.coords[-1])
    
        # Print the intersection points
        print(f"Intersection Point 1: {start_point}")
        print(f"Intersection Point 2: {end_point}")
    
        # Map these points to pixel coordinates
        start_x_pixel = map_to_pixels(start_point, geom, max_width)
        end_x_pixel = map_to_pixels(end_point, geom, max_width)
    
        print(f"Intersection Point 1 at x-pixel: {start_x_pixel}")
        print(f"Intersection Point 2 at x-pixel: {end_x_pixel}")
        pixels.append(math.ceil(start_x_pixel))
        pixels.append(math.ceil(end_x_pixel))
    
        # Set the new geometry to the intersecting segment
        new_geom = intersections
    
    elif intersections.geom_type == 'MultiLineString':
        # Initialize an empty list to hold all points from all lines
        points = []
    
        # If the intersection results in multiple LineStrings, combine them
        for line in intersections.geoms:  # Iterate over each LineString in MultiLineString
            points.extend(list(line.coords))  # Add the coordinates of each LineString to points
            
            # Process each line in the MultiLineString
            start_point = Point(line.coords[0])
            end_point = Point(line.coords[-1])
    
            print(f"Intersection Segment Start: {start_point}")
            print(f"Intersection Segment End: {end_point}")
    
            start_x_pixel = map_to_pixels(start_point, geom, max_width)
            end_x_pixel = map_to_pixels(end_point, geom, max_width)
    
            print(f"Intersection Segment Start at x-pixel: {start_x_pixel}")
            print(f"Intersection Segment End at x-pixel: {end_x_pixel}")
            pixels.append(math.ceil(start_x_pixel))
            pixels.append(math.ceil(end_x_pixel))
    
        # Combine all points from the MultiLineString into a new LineString
        if points:
            new_geom = LineString(points)
    
    # If there was an intersection, the new geometry represents the clipped line
    if new_geom:
        print(f"New Geometry: {new_geom}")
    else:
        print("No intersection geometry created.")

    
    print(f"Pixels list: {pixels}")
    #cut_geom = LineString(pixels)
    print(pixels)
    # Add vertical lines at the intersection points
    line1 = Span(location=pixels[0], dimension='height', line_color='red', line_width=1)
    line2 = Span(location=pixels[1], dimension='height', line_color='red', line_width=1)
    p_image_xdr.add_layout(line1)
    p_image_xdr.add_layout(line2)


    ########################
    
    # Processing SCS COS
    
    stack_scs, _ , scs_titles = process_scs_file(file)    
    stack_scs_db = 20*np.log10(abs(stack_scs))
    stack_scs_log = stack_scs_db.copy()
    #stack_scs_scaled = arrayscaler(stack_scs_scaled)
    stack_scs_scaled = stack_scs_db.copy()
    stack_scs_scaled = arrayscaler(stack_scs_scaled)

    print('STACK SCS_db', stack_scs_db)
    try:
        
        scs_image_f1 = stack_scs_scaled[1,:, :]
        scs_image_f2 = stack_scs_scaled[4,:, :]
        print('Stack SCS dB Done', stack_scs_db.shape)
    except:
        scs_image_f1 = stack_scs_scaled[0,:, :]
        scs_image_f2 = stack_scs_scaled[0,:, :]

    
    p_image_scs = fg(title=f'{scs_titles[0]}',width=plot_size//2, height=hgt//2,  x_range=p_image_xdr.x_range, y_range=p_image_xdr.y_range, tools=['wheel_zoom,pan,box_zoom,reset',cht])
    stack_scs_source = ColumnDataSource(data=dict(image=[stack_scs_db[1,:,:]]))
    render_scs = p_image_scs.image(image='image',source=stack_scs_source, x=0, y=0, dw=scs_image_f1.shape[1], dh=scs_image_f1.shape[0], palette='Viridis256')

    def update_scs(attr, old, new):
            index = slider_scs.value                
            p_image_scs.title.text=f'{scs_titles[index]}'        
            render_scs.data_source.data['image']  = [np.array(stack_scs_db[index,:, :])]

    slider_scs = Slider(start=0, end=5, value=0, step=1, title="SCS Amplitude Index")
    slider_scs.on_change('value', update_scs)



    ############################ FIX scs-xdr values

    
    #for i in range(stack_xdr_scaled.shape[0]):
    
    #   stack_scs[i,:,:] += abs(stack_scs[i,:,:].max() - stack_xdr_scaled[i,:,:].max())
    


    

    ####################### post-processing radargrams
    stack_xdr_scaled_proc = stack_xdr_scaled.copy()
    print(stack_xdr_scaled_proc.shape)
    processed_titles = []
    processed_xdf = []
    for i in [1,4]:
        if i == 1:
            name = 'F1'
        #    idx=20
        else:
            name = 'F2'
        #    idx=27
        #basename = os.path.basename(file)
        #name = f"{basename}_{ParamDF.iloc[idx].NAME}"
    
    
        from sklearn.impute import SimpleImputer

        imputer = SimpleImputer(strategy='median')  # or use 'median', 'most_frequent', etc.
        #stack_xdr_scaled[i] = imputer.fit_transform(stack_xdr_scaled[i])
        #stack_xdr_scaled_proc = stack_xdr_scaled - stack_xdr_scaled.max()
        
        #stack_xdr_scaled_proc[i]  = np.nan_to_num(stack_xdr_scaled[i], nan=0.0)
        
        #for j in range(stack_xdr_scaled_proc.shape[0]):
        #    for l in range(stack_xdr_scaled_proc.shape[2]):
        #        stack_xdr_scaled_proc[j,:,l] = stack_xdr_scaled_proc[j,:,l]-stack_xdr_scaled_proc[j,:,l].mean()
        
        mmsn = MinMaxScaler().fit_transform(normalize(stack_xdr_scaled_proc[i]))
        print(mmsn.shape)
        processed_xdf.append(mmsn)                
        processed_titles.append(f"Normalized MinMaxScaler_{name}")
        scaledblur = BLURfilter(mmsn,blur=2)
        print(scaledblur.shape)
        processed_xdf.append(scaledblur)
        processed_titles.append(f"ScaledBlur_{name}")
        blur = BLURfilter(stack_xdr_scaled_proc[i],blur=2)
        print(blur.shape)
        processed_xdf.append(blur)
        processed_titles.append(f"BLUR_{name}")
        usm = unsharp_mask(stack_xdr_scaled_proc[i], radius=13, amount=1)
        print(usm.shape)
        processed_xdf.append(usm)
        processed_titles.append(f"UnsharpMask_{name}")
        fft  = FFTfilter_vertical(normalize(stack_xdr_scaled_proc[i]), keep_fraction=0.3)
        print(fft.shape)
        processed_xdf.append(fft)
        processed_titles.append(f"FFT_Vertical_{name}")
        #idwt = IDWTfilter(mmsn, stack_xdr_scaled[i], 95)[:,0:stack_xdr_scaled[i].shape[1]]
        #print(idwt.shape)
        #processed_xdf.append(idwt)
        #processed_titles.append(f"{name}_IDWT")
        #tv_denoised_xdf = denoise_tv_chambolle(stack_xdr_scaled[i], weight=3)
        
        # Apply a denoising filter
        imagebit = (mmsn*255).astype(np.uint8)
        denoised_image = cv2.fastNlMeansDenoising(imagebit, h=25)        
        processed_xdf.append(denoised_image)
        processed_titles.append(f"{name}_NlMDen_{name}")
        #sigma = 50.0
        #theta = 0.0
        #frequency = 5
        #bandwidth = 1.5

        # Create a resized version of the Log-Gabor filter to match the image size
        #log_gabor = log_gabor_filter(stack_xdr_scaled[i].shape, sigma, theta, frequency, bandwidth)
        #log_gabor_resized = cv2.resize(log_gabor, (stack_xdr_scaled[i].shape[1], stack_xdr_scaled[i].shape[0]))
        #xdr_gabor = np.fft.ifft2(np.fft.fft2(mmsn) * log_gabor_resized).real
        #processed_xdf.append(np.uint8(255 * (xdr_gabor - np.min(xdr_gabor)) / np.ptp(xdr_gabor)))
        #processed_titles.append(f"{name}_LogGabor")
    stack_processed = np.stack(processed_xdf)
    
    
    p_image_processed = fg(title=f'{processed_titles[0]}',width=plot_size//2, height=hgt//2,  x_range=p_image_xdr.x_range, y_range=p_image_xdr.y_range, tools=['wheel_zoom,pan,box_zoom,reset',cht])
    stack_processed_source = ColumnDataSource(data=dict(image=[stack_processed[0,:,:]]))
    render_processed = p_image_processed.image(image='image',source=stack_processed_source, x=0, y=0, dw=xDRs[0][0].shape[1], dh=xDRs[0][0].shape[0], palette='Viridis256')
    print(stack_processed.shape)
    
    def update_processed(attr, old, new):
            index = slider_processed.value                
            p_image_processed.title.text=f'{processed_titles[index]}'
            render_processed.data_source.data['image']  = [np.array(stack_processed[index,:, :])]

    slider_processed = Slider(start=0, end=11, value=0, step=1, title="Processed Index")
    slider_processed.on_change('value', update_processed)
    
    
    ############ Power profiles
    try:
    
    
        pow_profile_scs_f1 = power_profiler(stack_scs_log[1,:, :],scaler=1)#, normalize='minmax')
        pow_profile_scs_f2 = power_profiler(stack_scs_log[4,:, :],scaler=1)#, normalize='minmax')
        print('Power profiles SCS Done', pow_profile_db_f1.shape)
    except:
        pow_profile_scs = power_profiler(stack_scs_log[0,:, :],scaler=1)#, normalize='minmax')
        pow_profile_scs_f2 = power_profiler(stack_scs_log[0,:, :],scaler=1)#, normalize='minmax')
        print('Power profiles SCS Error, using Index 0')

    pow_profile_xdr_f1 = -power_profiler(stack_xdr[1,:, :],scaler=1)#, normalize='minmax')
    pow_profile_xdr_f2 = -power_profiler(stack_xdr[4,:, :],scaler=1)#, normalize='minmax')
    #pow_profile_scs_cos=pow_profile_scs_cos[0:pow_profile_xdr.shape[0]]
    
    
    
    power_profiles = fg(title=f'Surface Power Profiles: {selected_track}',width=plot_size//2, height=int(hgt//2),  x_range=p_image_xdr.x_range, tools=['hover, wheel_zoom,pan,box_zoom,reset',cht])

    powerprof_xdr_f1_source = ColumnDataSource(data=dict(x=np.linspace(1,pow_profile_xdr_f1.shape[0],pow_profile_xdr_f1.shape[0]).astype(int),y=pow_profile_xdr_f1))
    powerprof_xdr_f2_source = ColumnDataSource(data=dict(x=np.linspace(1,pow_profile_xdr_f2.shape[0],pow_profile_xdr_f2.shape[0]).astype(int),y=pow_profile_xdr_f2))
    power_profiles.line(x='x',y='y', source=powerprof_xdr_f1_source, line_color='green', line_width=1,legend_label="ACQ-F1")
    power_profiles.line(x='x',y='y', source=powerprof_xdr_f2_source, line_color='blue', line_width=1,legend_label="ACQ-F2")
    
    powerprof_scs_f1_source = ColumnDataSource(data=dict(x=np.linspace(1,pow_profile_scs_f1.shape[0],pow_profile_scs_f1.shape[0]).astype(int),y=pow_profile_scs_f1))
    powerprof_scs_f2_source = ColumnDataSource(data=dict(x=np.linspace(1,pow_profile_scs_f2.shape[0],pow_profile_scs_f2.shape[0]).astype(int),y=pow_profile_scs_f2))
    power_profiles.line(x='x',y='y', source=powerprof_scs_f1_source, line_color='red', line_width=1,legend_label="SCS-F1")
    power_profiles.line(x='x',y='y', source=powerprof_scs_f2_source, line_color='orange', line_width=1,legend_label="SCS-F2")

    # Create a data source for storing the mouse position and cross-section data
    source_a = ColumnDataSource(data=dict(x=[0], y=[0]))
    source_b = ColumnDataSource(data=dict(x=[0], y=[0]))
    cross_section_source_a = ColumnDataSource(data=dict(x=[], y=[]))
    cross_section_source_b = ColumnDataSource(data=dict(x=[], y=[]))
    cross_section_source_c = ColumnDataSource(data=dict(x=[], y=[]))
    cross_section_source_d = ColumnDataSource(data=dict(x=[], y=[]))
    
    ################ Get Basemap
    
    #bmap_savename, dem_savename = basemap(geom, data_dir, basemap_layerid, dem_layerid, wcs_url)  #basemap(geom, data_dir, basemap_layerid, dem_layerid, wcs_url)
    
    ################ DEM PROFILE
    
    #dem_savename = f"{data_dir}/{dem_layerid}-crop_track-{selected_track}.tiff"
    #try:
    #    dem_profile = dem_profiler(dem_savename, geom, stack_xdr_scaled.shape[2])
    #except Exception as e:
    #    print(e)
    #    dem_profile = np.empty((1,stack_xdr_scaled.shape[2]))
    
    ################### BIG EDIT 2
    dem_basepath = os.path.join(data_dir,'Basemaps')
    dem_name = f'{dem_layerid}.tiff'
    dem_source = os.path.join(dem_basepath, dem_name)
    print('EDIT:',dem_source)
    try:
        print('QUERYING LOCAL DEM')
        dem = rioxarray.open_rasterio(dem_source, masked=True)
        # Initialize lists to store results
        all_elevations = []
        
        
        # Function to extract elevations and distances for each LineString
        
        
        # Check if the geometry is a LineString or MultiLineString
        if isinstance(geom, LineString):
            # Single LineString case
            elevations = dem_profiler_xarray(geom, dem)
            all_elevations.append(elevations)    
            
        elif isinstance(geom, MultiLineString):
            # MultiLineString case - iterate through each LineString in the MultiLineString using .geoms
            for line in geom.geoms:
                elevations = dem_profiler_xarray(line, dem)
                all_elevations.append(elevations)
                
        
        # Flatten the lists if there are multiple parts
        print('flattening')
        dem_profile = np.concatenate(all_elevations)
        distances = np.linspace(0, transformed_geom.length//1000, stack_xdr_scaled.shape[2])  # Distance in kilometers

    except Exception as e:
        print('LOCAL DEM FAILED',e)

        
    ################# END BIG EDIT 2




    print('ELEVATION DISTANCES')
    print(dem_profile.shape)
    print(distances.shape, distances.max())
    
    dem_profiles = fg(title=f'Elevation Profiles: {selected_track}',width=plot_size//2, height=hgt//2,  x_range=p_image_xdr.x_range, tools=['hover, wheel_zoom,pan,box_zoom,reset',cht])    
    dem_profile_source = ColumnDataSource(data=dict(x=np.linspace(1,dem_profile.shape[0],dem_profile.shape[0]).astype(int),y=dem_profile))
    dem_profiles.line(x='x',y='y', source=dem_profile_source, line_color='blue', line_width=1,legend_label="MOLA")
    ################ Crossections
    
    # Create a Bokeh figure for the cross-section plot
    min_xrange = -50 #stack_scs_scaled.min()
    max_xrange = 0#stack_scs_scaled.max()
    p_cross_section_a = fg(width=plot_size//5, height=hgt//2, y_range=p_image_xdr.y_range,tools=['hover, wheel_zoom,pan,box_zoom,reset',cht2], x_range=(min_xrange, max_xrange))#, y_range=(3600,0))
    p_cross_section_b = fg(width=plot_size//5, height=hgt//2, y_range=p_image_xdr.y_range,tools=['hover, wheel_zoom,pan,box_zoom,reset',cht2], x_range=(min_xrange, max_xrange))#, y_range=(3600,0))
    #p_cross_section_b = fg(width=plot_size, height=500)#, x_range=(0, 10), y_range=(0, 1))
    #p_cross_section_a.y_range.flipped = True
    # Plot the cross-section data
    p_cross_section_a.line(x='y', y='x', source=cross_section_source_a, line_color='green', line_width=1,legend_label="F1")
    p_cross_section_a.line(x='y', y='x', source=cross_section_source_b, line_color='red', line_width=1,legend_label="SCS_F1")
    p_cross_section_b.line(x='y', y='x', source=cross_section_source_c, line_color='blue', line_width=1,legend_label="F2")
    p_cross_section_b.line(x='y', y='x', source=cross_section_source_d, line_color='orange', line_width=1,legend_label="SCS_F2")
    
    
    ############# Callbacks for cross sections
    
    vline = Span(dimension='height', line_color='red', line_width=2)
    callback_f1 = CustomJS(args=dict(vline=vline, cross_section_source=cross_section_source_a), code="""
        const { x, y } = cb_obj;
        const xdr_image_f1 = %s;
        const image_width = %s;
        const image_height = %s;

        // Update the vertical line position
        cross_section_source.data.x = [x];
        vline.location = x;

        // Calculate the cross-section
        const cross_section = [];
        const colIndex = Math.round(x);
        for (let rowIndex = 0; rowIndex < image_height; rowIndex++) {
            cross_section.push(xdr_image_f1[rowIndex * image_width + colIndex]);
        }

        // Update the cross-section data
        cross_section_source.data = { x: [...Array(image_height).keys()], y: cross_section };
    """ % (xdr_image_f1.flatten().tolist(), xdr_image_f1.shape[1], xdr_image_f1.shape[0]))
    
    callback_f2 = CustomJS(args=dict(vline=vline, cross_section_source=cross_section_source_c), code="""
        const { x, y } = cb_obj;
        const xdr_image_f2 = %s;
        const image_width = %s;
        const image_height = %s;

        // Update the vertical line position
        cross_section_source.data.x = [x];
        vline.location = x;

        // Calculate the cross-section
        const cross_section = [];
        const colIndex = Math.round(x);
        for (let rowIndex = 0; rowIndex < image_height; rowIndex++) {
            cross_section.push(xdr_image_f2[rowIndex * image_width + colIndex]);
        }

        // Update the cross-section data
        cross_section_source.data = { x: [...Array(image_height).keys()], y: cross_section };
    """ % (xdr_image_f2.flatten().tolist(), xdr_image_f2.shape[1], xdr_image_f2.shape[0]))
    
    callback_scs_f1 = CustomJS(args=dict(vline=vline, cross_section_source=cross_section_source_b), code="""
        const { x, y } = cb_obj;
        const image = %s;
        const image_width = %s;
        const image_height = %s;

        // Update the vertical line position
        cross_section_source.data.x = [x];
        vline.location = x;

        // Calculate the cross-section
        const cross_section = [];
        const colIndex = Math.round(x);
        for (let rowIndex = 0; rowIndex < image_height; rowIndex++) {
            cross_section.push(image[rowIndex * image_width + colIndex]);
        }

        // Update the cross-section data
        cross_section_source.data = { x: [...Array(image_height).keys()], y: cross_section };
    """ % (scs_image_f1.flatten().tolist(), scs_image_f1.shape[1], scs_image_f1.shape[0]))

    callback_scs_f2 = CustomJS(args=dict(vline=vline, cross_section_source=cross_section_source_d), code="""
        const { x, y } = cb_obj;
        const xdr_image = %s;
        const image_width = %s;
        const image_height = %s;

        // Update the vertical line position
        cross_section_source.data.x = [x];
        vline.location = x;

        // Calculate the cross-section
        const cross_section = [];
        const colIndex = Math.round(x);
        for (let rowIndex = 0; rowIndex < image_height; rowIndex++) {
            cross_section.push(xdr_image[rowIndex * image_width + colIndex]);
        }

        // Update the cross-section data
        cross_section_source.data = { x: [...Array(image_height).keys()], y: cross_section };
    """ % (scs_image_f2.flatten().tolist(), scs_image_f2.shape[1], scs_image_f2.shape[0]))
    
    ####################################### Preparing Basemap + boundingbox + footprint
    
    url = ('https://explore.hyranet.info/geoserver/ows?service=WMS&'
   'request=GetMap&version=1.3.0&BGCOLOR=0xFFFFFF&&format=image/png&'
   'crs={crs}&layers={layer}&width={width}&height={height}')

    layer = 'Mars_Viking_MDIM21_ClrMosaic_global_232m-cog'
    width = 128
    height = 128
    interval = 1
    url_set = url.format(crs="EPSG:104905", width=width, height=height, layer=layer) + \
              '&bbox={XMIN},{YMIN},{XMAX},{YMAX}'
    
    x_range = Range1d(start=-180, end=180, bounds=None)
    y_range = Range1d(start=-90, end=90, bounds=None)
    tile_source = BBoxTileSource(url=url_set)
    x_range = Range1d(start=min_Lon, end=max_Lon, bounds=None, min_interval=interval)
    y_range = Range1d(start=min_Lat, end=max_Lat, bounds=None, min_interval=interval)
    
    p_image_base = fg(title=f'Acquisition: {selected_track}', tools=['hover, wheel_zoom,pan,box_zoom,reset'],
                        x_range=x_range,
                        y_range=y_range,
                        lod_threshold=None,              
                        background_fill_color='white',
                        width=plot_size//4, height=plot_size)
                      
    tile_source = BBoxTileSource(url=url_set)
    p_image_base.add_tile(tile_source)
    
    if geom.geom_type == 'LineString':
        gx, gy = geom.xy[0], geom.xy[1]
    elif geom.geom_type == 'MultiLineString':
        gx, gy = [], []
        for line in geom.geoms:  # Iterate through each LineString in the MultiLineString
            x, y = line.xy
            gx.extend(x)
            gy.extend(y)
    
    # Create the ColumnDataSource for the original geometry
    geom_source = ColumnDataSource(data=dict(x=gx, y=gy)) 
    
    # Do the same for the transformed geometry
    if transformed_geom.geom_type == 'LineString':
        gxm, gym = transformed_geom.xy[0], transformed_geom.xy[1]
    elif transformed_geom.geom_type == 'MultiLineString':
        gxm, gym = [], []
        for line in transformed_geom.geoms:
            x, y = line.xy
            gxm.extend(x)
            gym.extend(y)
    
    # Create the ColumnDataSource for the transformed geometry
    geom_source_M = ColumnDataSource(data=dict(x=gxm, y=gym))
    
    # Handle the bounding box
    min_Lon, min_Lat, max_Lon, max_Lat = boundingbox
    bounding_box_annotation = BoxAnnotation(left=min_Lon, right=max_Lon, 
                                            bottom=min_Lat, top=max_Lat, 
                                            fill_alpha=0, fill_color='blue', 
                                            line_color='blue', line_width=3)
    
    # Add the BoxAnnotation to the plot
    p_image_base.add_layout(bounding_box_annotation)
    
    # Create the LineString from the transformed coordinates
    line_string = LineString(zip(gxm, gym))
    
    # Calculate distances along the LineString in kilometers
    distances_km = [line_string.project(Point(x, y)) / 1000 for x, y in zip(gxm, gym)]
    
    # Add the distances to the ColumnDataSource
    geom_source.add(distances_km, 'distance_km')

    # Plot the line with the distance_km column in the HoverTool
    line = p_image_base.line(x='x', y='y', source=geom_source, line_color='green', line_width=5, alpha=0.5,
                         legend_label="Track footprint")
    
    kmFormatter = CustomJSTickFormatter(code=f'''
    var space = ' ';
    return (tick * {round(max(distances_km), 1)}).toFixed(1) + space + 'Km';
    ''')

    # Apply the custom formatter to the x-axis

    # Create a custom hover tooltip
    hover = HoverTool(renderers=[line], tooltips=[("Latitude", "@y{0.000}"), ("Longitude", "@x{0.000}"), ("Distance (km)", "@distance_km{0.00}")])

    # Add the hover tool to the figure
    p_image_base.add_tools(hover)
    
    
    subsurface_df, source = load_data()

    
    l1= p_image_xdr.multi_line(xs='x', ys='y', source = source, line_color='red', line_width=3)
    draw_tool_l1 = PolyDrawTool(renderers=[l1])
    p_image_xdr.add_tools(draw_tool_l1)

    
    ####################################### Styling        
    
    
    
    
    
    p_cross_section_a.xaxis.formatter=CustomJSTickFormatter(code = '''return `${(tick).toFixed(0)}`;''')
    p_cross_section_a.yaxis.formatter = yFormatter
    p_image_xdr.xaxis.formatter=xFormatter
    p_image_xdr.yaxis.formatter = yFormatter
    p_image_scs.xaxis.formatter=xFormatter
    p_image_scs.yaxis.formatter = yFormatter
    p_image_processed.xaxis.formatter = xFormatter
    p_image_processed.yaxis.formatter = yFormatter
    dem_profiles.xaxis.formatter = xFormatter
    #dem_profiles.yaxis.formatter = yFormatter
    power_profiles.xaxis.formatter = xFormatter
    #power_profiles.yaxis.formatter = yFormatter
    p_image_xdr.js_on_event('mousemove', callback_f1)
    p_image_xdr.js_on_event('mousemove', callback_f2)
    p_image_xdr.js_on_event('mousemove', callback_scs_f1)
    p_image_xdr.js_on_event('mousemove', callback_scs_f2)
    p_image_scs.js_on_event('mousemove', callback_f1)
    p_image_scs.js_on_event('mousemove', callback_f2)
    p_image_scs.js_on_event('mousemove', callback_scs_f1)
    p_image_scs.js_on_event('mousemove', callback_scs_f2)
    p_image_processed.js_on_event('mousemove', callback_f1)
    p_image_processed.js_on_event('mousemove', callback_f2)
    p_image_processed.js_on_event('mousemove', callback_scs_f1)
    p_image_processed.js_on_event('mousemove', callback_scs_f2)
    
    return(slider_xdr, p_image_xdr, slider_scs, p_image_scs, p_cross_section_a,p_cross_section_b, p_image_processed, slider_processed, p_image_base, dem_profiles, power_profiles, source, xdr_image_f1, xdr_image_f1_db, xdr_image_f2, xdr_image_f2_db, stack_xdr_scaled, stack_scs, stack_scs_db, stack_scs_scaled, geom,frequencies_arrays, sc_altitudes)#, p_image_ampha, slider_ampha)


def update_plots(attrname, old, new):    
    bounding_box[0] = float(min_lon_input.value)
    bounding_box[1] = float(min_lat_input.value)
    bounding_box[2] = float(max_lon_input.value)
    bounding_box[3] = float(max_lat_input.value)
    
    selected_track = track_select.value
    print(selected_track)
    file = f"{selected_track}.DAT"
    slider_xdr, p_image_xdr, slider_scs, p_image_scs, p_cross_section_a, p_cross_section_b, p_image_processed, slider_processed, p_image_base, dem_profiles, power_profiles, source, xdr_image_f1, xdr_image_f1_db, xdr_image_f2, xdr_image_f2_db, stack_xdr_scaled, stack_scs, stack_scs_db, stack_scs_scaled, geom,frequencies_arrays, sc_altitudes = processor(file, data_dir, basemap_layerid, dem_layerid, wcs_url,bounding_box)


    
    # Replace all plots inside the layout
    layout.children[0].children[1].children = [slider_xdr]
    layout.children[0].children[2].children = [min_lon_input, min_lat_input, max_lon_input, max_lat_input, update_button]
    layout.children[0].children[3].children = [p_image_xdr, p_cross_section_a, p_cross_section_b]
    layout.children[0].children[4].children = [
        column(slider_scs, p_image_scs), column(slider_processed, p_image_processed)
    ]
    layout.children[0].children[5].children = [power_profiles, dem_profiles]
    layout.children[1].children = [p_image_base]

    

    

def save_data():        
    selected_track = track_select.value
    selected_version = version_select.value
    selected_frequency = freq_select.value

    track = f"{selected_track}"
    if selected_version == 'Original':
        if selected_frequency == 'F1':
            hdf_file = os.path.join(data_dir, 'subsurface_layers_F1.h5')
        else:  # F2
            hdf_file = os.path.join(data_dir, 'subsurface_layers_F2.h5')
        print('Loading Original')
    else:  # Autopicked
        if selected_frequency == 'F1':
            hdf_file = os.path.join(data_dir, 'subsurface_layers_autopicked_F1.h5')
        else:  # F2
            hdf_file = os.path.join(data_dir, 'subsurface_layers_autopicked_F2.h5')
        print('Loading Autopicked')    
    
    
    subsurface_saver(source, track, hdf_file, [xdr_image_f1, xdr_image_f1_db_ori, xdr_image_f2, xdr_image_f2_db_ori], geom, geom_length, dem, data_dir,frequencies_arrays, sc_altitudes, selected_frequency, sampling=0.7143)
    #subsurface_saver(source, track, hdf_file, [xdr_image_f1, xdr_image_f1_db, xdr_image_f2, xdr_image_f2_db],  geom, geom_length, dem_profile, data_dir, layer_dict, selected_frequency, frequencies_array)
    
    #source, track, hdf_file, xdr_image_f1, xdr_image_f1_db, xdr_image_f2, xdr_image_f2_db, stack_xdr_scaled, stack_scs, stack_scs_db, stack_scs_scaled, geom, geom_length, dem_profile, data_dir, selected_frequency, frequencies_array
    print(f'Saved data for {selected_version} with {selected_frequency}')


def load_data():
    selected_track = track_select.value
    selected_version = version_select.value
    selected_frequency = freq_select.value

    track = f"{selected_track}"
    if selected_version == 'Original':
        if selected_frequency == 'F1':
            hdf_file = os.path.join(data_dir, 'subsurface_layers_F1.h5')
        else:  # F2
            hdf_file = os.path.join(data_dir, 'subsurface_layers_F2.h5')
        print('Loading Original')
    else:  # Autopicked
        if selected_frequency == 'F1':
            hdf_file = os.path.join(data_dir, 'subsurface_layers_autopicked_F1.h5')
        else:  # F2
            hdf_file = os.path.join(data_dir, 'subsurface_layers_autopicked_F2.h5')
        print('Loading Autopicked')
    
    try:
        subsurface_df = pd.read_hdf(hdf_file)
        subsurface_df = subsurface_df.reset_index(drop=True)
        #df = df[df["layer_id"].str.contains(f'{track}_surface') == False]
        print("TRACK: ", track)
        print(subsurface_df)
        subsurface_df = subsurface_df.loc[subsurface_df.track_num.str.contains(track)]
        print(subsurface_df.head)
        xs_arrays = []
        ys_arrays = []
        layers_ids = subsurface_df.loc[subsurface_df["track_num"].str.contains(track)]['layer_id'].unique()
        print(layers_ids)
        track_layers_coords = []
        for ii, val in enumerate(layers_ids):
            layer_df = subsurface_df.loc[subsurface_df["layer_id"] == val]
            xs_arrays.append(np.array(layer_df["pt_cols"].values))
            ys_arrays.append(np.array(layer_df["pt_lines"].values))
            layer_coords = list(zip(layer_df["pt_cols"], layer_df["pt_lines"]))
            track_layers_coords.append(layer_coords)
        #source.data = dict(x=[], y=[])
        source.data = dict(x=xs_arrays, y=ys_arrays)    
        #radargram_figure.multi_line(xs='x', ys='y', source=source, line_color='red', line_width=3)
        print(f'loaded {selected_version}')
        #print(xs_arrays)
        #print(ys_arrays)
        #print('len arrays')
        #print(len(xs_arrays), len(ys_arrays))
    except Exception as e:
        print(e)
    
    subsurface_df = subsurface_df.loc[subsurface_df.track_num.str.contains(track)]
    print(subsurface_df.head())

    xs_arrays = []
    ys_arrays = []
    layers_ids = subsurface_df['layer_id'].unique()
    print('Unique layer IDs:', layers_ids)

    track_layers_coords = []
    for ii, val in enumerate(layers_ids):
        layer_df = subsurface_df.loc[subsurface_df["layer_id"] == val]
        xs_arrays.append(np.array(layer_df["pt_cols"].values))
        ys_arrays.append(np.array(layer_df["pt_lines"].values))
        layer_coords = list(zip(layer_df["pt_cols"], layer_df["pt_lines"]))
        track_layers_coords.append(layer_coords)
    
    #source = ColumnDataSource(data=dict(x=[], y=[]))
    source.data = dict(x=xs_arrays, y=ys_arrays)    
        
    p_image_xdr.multi_line(xs='x', ys='y', source=source, line_color='red', line_width=3)
    
    print(f'Loaded {selected_version} with {selected_frequency}')
    print(xs_arrays)
    print(ys_arrays)
    print('Length of arrays:', len(xs_arrays), len(ys_arrays))
    
    return subsurface_df, source

def autopick_data():
    selected_track = track_select.value
    selected_frequency = freq_select.value

    print(selected_track)

    # Select the appropriate stack_processed index based on the selected frequency
    if selected_frequency == 'F1':
        stack_index = 1
    else:  # F2
        stack_index = 4
    subsurface_df, xs, ys =  autopicker(selected_track, dem, [xdr_image_f1, xdr_image_f1_db_ori, xdr_image_f2, xdr_image_f2_db_ori], geom, geom_length, data_dir, frequencies_arrays, sc_altitudes, selected_frequency, sampling=0.7143)
    
    
    source.data = dict(x=xs, y=ys)
    p_image_xdr.multi_line(xs='x', ys='y', source=source, line_color='red', line_width=3)


    



available_tracks = sorted(list(set([os.path.splitext(os.path.basename(track))[0] for track in get_paths(data_dir, '_M.DAT')])))
#avail    
selected_track = available_tracks[0]
track_select = Select(value=selected_track, title='track', options=sorted(available_tracks))
version_select = Select(value='Original', title='Version', options=['Original', 'Auto-Picked'])
freq_select = Select(value='F1', title='Frequency', options=['F1', 'F2'])

dummy = 'dummy'
    
#if track == available_tracks[0]:
if 'dummy' in dummy:
    p_image_xdr = fg(width=plot_size, height=plot_size//4)
    p_cross_section_a = fg(width=plot_size, height=plot_size//4)
    p_cross_section_b = fg(width=plot_size, height=plot_size//4)
    p_image_scs = fg(width=plot_size, height=plot_size//4)
    p_image_processed = fg(width=plot_size, height=plot_size//4)
    scs_figure = fg(width=plot_size//4, height=plot_size)
    power_profiles = fg(width=plot_size, height=plot_size//4)
    dem_profiles = fg(width=plot_size, height=plot_size//4)
    p_image_base = fg(width=plot_size, height=plot_size//4)
    slider_xdr = Slider(start=0, end=5, value=0, step=1, title="RGRM Amplitude Index")
    slider_scs = Slider(start=0, end=5, value=0, step=1, title="COS Simulation Amplitude Index")
    slider_processed = Slider(start=0, end=11, value=0, step=1, title="Processed Index")
    xdr_image, scs_image = np.empty([2, 2]), np.empty([2, 2])
    #load_original_button = Button(label="Load original picked", button_type="success")
    save_button = Button(label="Save", button_type="success")
    autopick_button = Button(label="Autopick", button_type="success")
    load_button = Button(label="Load Data", button_type="success")    
    source = ColumnDataSource(data=dict(x=[], y=[]))
    geom = None
    #frequencies_array = None
    cross_section_source_a= ColumnDataSource(data=dict(x=[], y=[]))
    cross_section_source_b = ColumnDataSource(data=dict(x=[], y=[]))
    cross_section_source_c = ColumnDataSource(data=dict(x=[], y=[]))
    cross_section_source_d = ColumnDataSource(data=dict(x=[], y=[]))
    
    
    
else:
    
    slider_xdr, p_image_xdr, slider_scs, p_image_scs, p_cross_section_a, p_cross_section_b, p_image_processed, slider_processed, p_image_base, dem_profiles, power_profiles, source, xdr_image_f1, xdr_image_f1_db, xdr_image_f2, xdr_image_f2_db, stack_xdr_scaled, stack_scs, stack_scs_db, stack_scs_scaled,  geom, frequencies_arrays, sc_altitudes,  = processor(f'{selected_track}.DAT', data_dir, basemap_layerid, dem_layerid, wcs_url, bounding_box)
            
    
#load_original_button = Button(label="Load original picked", button_type="success")
save_button = Button(label="Save", button_type="success")
autopick_button = Button(label="Autopick", button_type="success")
load_button = Button(label="Load Data", button_type="success")    
update_button = Button(label="Update Bounding Box", button_type="success")    



# Create bounding box input fields
min_lon_input = TextInput(title="Min Longitude", value=str(min_Lon))
min_lat_input = TextInput(title="Min Latitude", value=str(min_Lat))
max_lon_input = TextInput(title="Max Longitude", value=str(max_Lon))
max_lat_input = TextInput(title="Max Latitude", value=str(max_Lat))

# Attach on_change callbacks to update plots when bounding box values change
#min_lon_input.on_change('value', update_plots)
#min_lat_input.on_change('value', update_plots)
#max_lon_input.on_change('value', update_plots)
#max_lat_input.on_change('value', update_plots)







    
    

print("SOURCE", source)
# Define the callback function
callback4 = CustomJS(args=dict(src=source), code="""
    const data = cb_obj.data;
    src.data = data;
    src.change.emit();
""")

# Set up the callback for the 'source' variable
source.js_on_change("data", callback4)

# Set up the button callbacks
track_select.on_change('value', update_plots)
save_button.on_click(save_data)
load_button.on_click(load_data)
autopick_button.on_click(autopick_data)

def update_plots_wrapper(event):
    # Assuming track_select.value is available globally or passed in some other way
    update_plots('value', None, track_select.value)

update_button.on_click(update_plots_wrapper)          


             
             
#layout = row(column(row(track_select),                
#                    row(slider_xdr, slider_cos),
#                    row(p_image_xdr, p_cross_section_a, p_image_scs_cos, p_image_base),
#                    row(column(slider_processed, p_image_processed)),
#                    row(power_profiles, dem_profiles)))



layout = row(
    column(
        row(track_select, version_select, freq_select, load_button, save_button, autopick_button),
        row(min_lon_input, min_lat_input, max_lon_input, max_lat_input, update_button),
        row(slider_xdr),
        row(p_image_xdr, p_cross_section_a, p_cross_section_b),
        row(
            column(slider_scs, p_image_scs), 
            column(slider_processed, p_image_processed)
        ),
        row(power_profiles, dem_profiles)
    ),
    column(p_image_base)
)

curdoc().clear()
curdoc().title = "EchoTerraeTrace-Draw: MARSIS"  
curdoc().add_root(layout)        
