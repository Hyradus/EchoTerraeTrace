# Standard Library Imports
import os
import math
import warnings

# Third-Party Imports
import numpy as np
import pandas as pd
import geopandas as gpd
import rioxarray as riox
import rasterio as rio
from pyproj import CRS
from scipy.ndimage import maximum_filter
from shapely.geometry import LineString, box, Point
from shapely.ops import nearest_points
from sklearn.preprocessing import normalize, MinMaxScaler, StandardScaler, RobustScaler

# Visualization Libraries
import holoviews as hv
hv.extension('bokeh', 'webgl')

import plotly.graph_objects as go
import plotly.express as px

# Bokeh Imports
from bokeh.io import curdoc
from bokeh.plotting import figure as fg
#from bokeh.plotting import show
from bokeh.layouts import column, row
from bokeh.models import (
    CustomJS, Span, BoxAnnotation, PolyDrawTool, ColumnDataSource,
    Select, BBoxTileSource, Range1d, CrosshairTool, Slider, TextInput, HoverTool, 
    CustomJSTickFormatter, Button, Div
)

# OpenCV
import cv2 as cv

# Local Utilities
from utils.genUtils import get_paths
from utils.dataPreps import DataPrepSHARAD
from utils.dataStructs import track_dict_builder
from utils.dataPlots import Formatters
from utils.saveUtils import subsurface_saver, autopicker
from utils.profilers import dem_profiler_xarray
# CRS
from utils.CRS import MARS2000, DST_CRS
########################################## Initializations 

# Track Titles
track_titles = [
    'Gaussian Blur', 'Scaled Gaussian Blur',
    'Unsharp Mask', 'Scaled Unsharp Mask',
    'FFT', 'Scaled FFT',
    'Unsharp Mask + FFT', 'Scaled Unsharp Mask + FFT',
    'IDWT', 'Scaled IDWT',
    'IDWT + MinMaxScaler-normalizer', 'Scaled IDWT + MinMaxScaler-normalizer',
    'IDWT + MinMaxScaler-normalizer + Gaussian Blur', 'Scaled IDWT + MinMaxScaler-normalizer + Gaussian Blur',
    'Log-Gabor', 'Log-Gabor + MinMaxScaler-normalizer'
]

# Stack Titles

stack_titles = ['Gaussian Blur', 'Scaled Gaussian Blur',
                'Unsharp Mask','Scaled Unsharp Mask',
                'FFT','Scaled FFT',
                'Unsharp Mask + FFT','Scaled Unsharp Mask + FFT',
                'IDWT', 'Scaled IDWT',
                'IDWT + MinMaxScaler-normalizer', 'Scaled IDWT + MinMaxScaler-normalizer',
                'IDWT  + MinMaxScaler-normalizer + Gaussian Blur', 'Scaled IDWT  + MinMaxScaler-normalizer + Gaussian Blur',
                'Log-Gabor','Log-Gabor + MinMaxScaler-normalizer']


# Data Directory Setup
home = '/app/'  # Replace with `Path.home()` if needed  # Replace with `Path.home()` if needed
print(f"Home Directory: {home}")

# Default data directory
data_dir = '/Data/SHARAD/'#os.path.join(home, 'SHARAD')
track_dir = os.path.join(data_dir, 'SHARAD/')
# Uncomment and set the desired data directory path if needed
#data_dir = "/home/hyradus/SyncThing/SyncData/SHARAD_PIT_DATA/Site_4/SHARAD/"

print(f"Data Directory: {data_dir}")

# Geographic Bounding Box
min_Lon, min_Lat, max_Lon, max_Lat = -180, -90, 180, 90
boundingbox = [min_Lon, min_Lat, max_Lon, max_Lat]

# Plot Settings
plot_size = 1280

# WCS (Web Coverage Service) Configuration
wcs_url = 'https://explore.hyranet.info/geoserver/ows?service=WCS'
bmap_layerid = 'Mars_Viking_MDIM21_ClrMosaic_global_232m-cog'
dem_layerid = 'Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2-cog'

# Load Tracks
available_tracks = list(set(track.split('s_')[-1].split('_')[0] for track in get_paths(track_dir, 'IMG')))
available_tracks.insert(0, '0000000')
#print(f"Available tracks: {sorted(available_tracks)}")

# Reference Systems
#MARS2000 = CRS.from_wkt('GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]')
#DST_CRS = CRS.from_wkt('PROJCS["Mars_Equidistant_Cylindrical",GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Equidistant_Cylindrical"],PARAMETER["False_Easting",0],PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",0],PARAMETER["Standard_Parallel_1",0],UNIT["Meter",1]]')

        
def main(track, boundingbox, roll, stack_titles, compression_value, quality_value):
    global source
    global rolled_acq
    global rolled_acq_ori
    global rolled_scs
    global rolled_scs_ori
    global rolled_acq_db
    global rolled_scs_db
    global rolled_acq_db_ori
    global rolled_scs_db_ori
    global stack
    global dem_profile_ori
    #global stack_ori
    global max_width
    global max_height
    global geom
    global dem
    global geom_length    
    global subsurface_df
    global dem_profile
    global left, right
    global geom, geom_rep, geom_length, rolled_scs, rolled_acq, rolled_acq_scaled, rolled_acq_db, rolled_scs_db, max_width, max_height,  xFormatter, yFormatter, dem_profile, acq_pow_profile, scs_pow_profile, cross_section_source_rgram, cross_section_source_scs
    ### Try to load the dat
    try:
        data_prep = DataPrepSHARAD(track_dir, track, wcs_url, dem_layerid, bmap_layerid, boundingbox, plot_size, roll=1800)
        print(data_prep)
        geom, geom_rep, geom_length, rolled_scs, rolled_acq, rolled_acq_scaled, rolled_acq_db, rolled_scs_db, max_width, max_height, xFormatter, yFormatter, dem_profile, dem, acq_pow_profile, scs_pow_profile = data_prep.prepare_data()        
        print(geom)
        print('data generated')
        #track=f"s_{track}"    
        
        # try to post-process the radargram and stack them into a numpy 3D array
        try:
            #stack, _ = enhancer(rolled_acq, rolled_acq_scaled)    
            stack, _ = data_prep.enhancer(rolled_acq, rolled_acq_scaled)              
        except Exception as stack_error:
            stack = np.stack([rolled_acq,rolled_acq,rolled_acq])
            stack_titles = ['No data available']
            print('stack error', stack_error)
    except Exception as e:
        print('MAIN ERROR', e)              
        geom = None
        geom_length = plot_size
        rolled_scs = None
        rolled_acq = None
        rolled_acq_scaled = None
        #corr_nadir = []
        max_width, max_height = plot_size, plot_size//2                
        dem_profile= np.empty([plot_size,1])[0]
        acq_pow_profile= np.empty([plot_size,1])[0]
        scs_pow_profile = np.empty([plot_size,1])[0]
        stack = np.stack([rolled_acq,rolled_acq,rolled_acq])
        xFormatter, yFormatter, _ = Formatters(geom_length, max_width)
    print ("DEM PROFILE LENGTH", len(dem_profile))
    
    
    ### Check if a subsurface HDF exists, then read it, else create an empty one
    try:
        hdf_file = f"{track_dir}subsurface_layers.h5"
        print(f'reading, {hdf_file}')
        subsurface_df=pd.read_hdf(hdf_file).reset_index()        
        subsurface_df.drop("index",axis=1,inplace=True)
        print('Suburface_layers found!')
        print(subsurface_df)
    except Exception as e:
        print('HDF READING ERROR: ',e)
        #layer_dict["track_num"]=f"s_{track}"
        subsurface_df = pd.DataFrame()
        print(e, "Creating a new one")

    ### Initializing and defining interactive basemap plot using wms
    
    url = ('https://explore.hyranet.info/geoserver/ows?service=WMS&'
   'request=GetMap&version=1.3.0&BGCOLOR=0xFFFFFF&&format=image/png&'
   'crs={crs}&layers={layer}&width={width}&height={height}')

    layer = 'Mars_Viking_MDIM21_ClrMosaic_global_232m-cog'
    width = 128
    height = 128
    interval = 1
    url_set = url.format(crs="EPSG:104905", width=width, height=height, layer=layer) + '&bbox={XMIN},{YMIN},{XMAX},{YMAX}'
    
    x_range = Range1d(start=-180, end=180, bounds=None)
    y_range = Range1d(start=-90, end=90, bounds=None)
    tile_source = BBoxTileSource(url=url_set)
    min_Lon, min_Lat, max_Lon, max_Lat = boundingbox
    x_range = Range1d(start=min_Lon, end=max_Lon, bounds=None, min_interval=interval)
    y_range = Range1d(start=min_Lat, end=max_Lat, bounds=None, min_interval=interval)
    

    bbox = box(min_Lon, min_Lat, max_Lon, max_Lat)
    intersections = geom.intersection(bbox)
    boundingbox
    
    # Function to map intersection points to pixel coordinates
    def map_to_pixels(point, geom, max_width):
        distance_along_line = geom.project(point)
        x_pixel = (distance_along_line / geom.length) * max_width
        return x_pixel
    
    # Check if the intersection result is a LineString
    pixels = []
    if intersections.geom_type == 'LineString':
        # Extract the start and end points of the intersecting segment
        try:
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
        except Exception as e:
            print(e)
            print(intersections.coords)
            pixels.append(0)
            pixels.append(rolled_acq.shape[1])
    else:
        print("No intersections found.")
        pixels.append(0)
        pixels.append(rolled_acq.shape[1])
    
    
    
    print(f"Pixels list: {pixels}")
    
    
    # Add vertical lines at the intersection points
    line1 = Span(location=pixels[0], dimension='height', line_color='red', line_width=6)
    line2 = Span(location=pixels[1], dimension='height', line_color='red', line_width=6)
    
    # CROPPING with bb limits
    left = pixels[0]
    right = pixels[1]
    rolled_acq_ori = rolled_acq.copy()
    rolled_scs_ori = rolled_scs.copy()
    rolled_acq_db_ori = rolled_acq_db.copy()
    rolled_scs_db_ori = rolled_scs_db.copy()    
    stack_ori = stack.copy()
    dem_profile_ori = dem_profile.copy()


    rolled_acq = rolled_acq[:, left:right]
    rolled_scs = rolled_scs[:, left:right]
    rolled_acq_db = rolled_acq_db[:, left:right]
    rolled_scs_db = rolled_scs_db[:, left:right]  
    #stack = stack[:,left,right]
    stack = stack[:, :, left:right]

    acq_pow_profile = acq_pow_profile[left:right]
    scs_pow_profile = scs_pow_profile[left:right]
    dem_profile = dem_profile[left:right]
    
    max_width, max_height = rolled_acq.shape[1],rolled_acq.shape[0]
    print('stack shape', stack.shape)
    
    
    
    ### Initializing figures
    
    # Initializing crosshair tools
    width = Span(dimension="width")
    height = Span(dimension="height")
    cht = CrosshairTool(overlay=[width, height])
    cht2 = CrosshairTool(overlay=[height,width])
    
    ### Scaling plots height to image heights and plot_size
    scalx = 1
    scaly = 4
    print(rolled_acq.shape)
    aspect = rolled_acq.shape[1] / rolled_acq.shape[0]
    hgt = int((rolled_acq.shape[1] * plot_size / rolled_acq.shape[0]) // (aspect * scaly) if aspect < 1 else (rolled_acq.shape[1] * plot_size / rolled_acq.shape[0]) // scaly)
    
    # Radargram
    radargram_figure = fg(title=f'Acquisition: {track}',width=plot_size, height=hgt,  y_range=(3600,0),tools=[' wheel_zoom,pan,box_zoom,reset,hover',cht])
    # Radargram enhanced
    stack_figure = fg(title=f'{stack_titles[0]}: {track}',width=plot_size//2, height=hgt//2,  x_range=radargram_figure.x_range, y_range=radargram_figure.y_range, tools=['wheel_zoom,pan,box_zoom,reset',cht])
    # SCS
    scs_figure = fg(title=f'Surface Clutter Simulation: {track}',width=plot_size//2, height=hgt//2,  x_range=radargram_figure.x_range, y_range=radargram_figure.y_range ,tools=['wheel_zoom,pan,box_zoom,reset,hover',cht])
    
    
    from skimage.transform import resize  # Install: pip install scikit-image
    from PIL import Image

    ### 🔹 Step 1: Define Optimization Functions
    def normalize_to_uint8(image):
        """Normalize float image and convert to uint8 (0-255)."""
        image = (image - np.min(image)) / (np.max(image) - np.min(image))  # Normalize to 0-1
        return (image * 255).astype(np.uint8)  # Convert to 8-bit uint8

    def downsample_image(image, scale_factor=0.2):
        """Resize image to reduce resolution while preserving quality."""
        new_shape = (int(image.shape[0] * scale_factor), int(image.shape[1] * scale_factor))
        return resize(image, new_shape, anti_aliasing=True, preserve_range=True).astype(np.uint8)

    def lossy_compress(image, quality=50):
        """Apply JPEG compression to reduce weight."""
        img = Image.fromarray(image)
        img.save("temp.jpg", "JPEG", quality=quality)  # Save as JPEG
        return np.array(Image.open("temp.jpg"))  # Reload as NumPy array

    def convert_to_rgba(image):
        """Convert grayscale or 8-bit image to RGBA format."""
        if image.ndim == 2:  # Convert grayscale to RGBA
            image = np.stack([image] * 3 + [np.full_like(image, 255)], axis=-1)
        
        # Flip image vertically to match Bokeh’s coordinate system
        #image = np.flipud(image)

        return image.view(dtype=np.uint32).reshape(image.shape[0], image.shape[1])

    def process_image_stack(stack, scale_factor=0.5, quality=50):
        """Optimize a stacked array: normalize, downsample, compress, and convert to RGBA."""
        processed_stack = []
        
        for i in range(stack.shape[0]):
            img = normalize_to_uint8(stack[i, :, :])  # Step 1: Convert float to uint8
            img = downsample_image(img, scale_factor=scale_factor)  # Step 2: Downsample (optional)
            img = lossy_compress(img, quality=quality)  # Step 3: Apply compression (optional)
            img = convert_to_rgba(img)  # Step 4: Convert to RGBA
            processed_stack.append(img)

        return np.array(processed_stack, dtype=np.uint32)  # Convert list to NumPy array

    def process_single_image(image, scale_factor=0.2, quality=50):
        """Optimize a single image: normalize, downsample, compress, and convert to RGBA."""
        img = normalize_to_uint8(image)  # Step 1: Convert float to uint8
        img = downsample_image(img, scale_factor=scale_factor)  # Step 2: Downsample (optional)
        img = lossy_compress(img, quality=quality)  # Step 3: Apply compression (optional)
        return convert_to_rgba(img)  # Step 4: Convert to RGBA

    ### 🔹 Step 2: Apply Optimizations
    rgba_stack = process_image_stack(stack, scale_factor=compression_value, quality=quality_value)  # For stack (multiple images)
    rgba_acq = process_single_image(rolled_acq, scale_factor=compression_value, quality=quality_value)  # For single acquisition image
    rgba_scs = process_single_image(rolled_scs, scale_factor=compression_value, quality=quality_value)  # For single scs image

    ### 🔹 Step 3: Update Bokeh Data Sources
    # Only update if the data is actually changing
    if not np.array_equal(stack_source.data["image"], [rgba_stack[0]]):
        stack_source.data = dict(image=[rgba_stack[0]])

    if not np.array_equal(radargram_source.data["image"], [rgba_acq]):
        radargram_source.data = dict(image=[rgba_acq])

    if not np.array_equal(scs_source.data["image"], [rgba_scs]):
        scs_source.data = dict(image=[rgba_scs])

    #stack_source.data = dict(image=[rgba_stack[0]])  # First image from stack
    #radargram_source.data = dict(image=[rgba_acq])  # Processed acquisition image
    #scs_source.data = dict(image=[rgba_scs])  # Processed SCS image


    


    ### Plot the image
    # Initializing plot sources
    # Stack
    #stack_source = ColumnDataSource(data=dict(image=[stack[0, :, :]]))
    # Radargram
    #radargram_source = ColumnDataSource(data=dict(image=[rolled_acq]))
    # SCS
    #scs_source = ColumnDataSource(data=dict(image=[rolled_scs]))
    
    print('stack')
    #render_radargram = radargram_figure.image(image=[(rolled_acq)], x=0, y=0, dw=rolled_acq.shape[1], dh=image_data.shape[0], palette='Spectral11')
    render_radargram = radargram_figure.image(image='image',source=radargram_source, x=left, y=0, dw=rolled_acq.shape[1], dh=rolled_acq.shape[0], palette='Viridis256')
    render_stack = stack_figure.image(image='image',source=stack_source,x=left, y=0, dw=rolled_acq.shape[1], dh=rolled_acq.shape[0], palette='Viridis256')
    render_scs = scs_figure.image(image='image',source=scs_source, x=left, y=0, dw=rolled_acq.shape[1], dh=rolled_acq.shape[0], palette='Viridis256')

    radargram_figure.add_layout(line1)
    radargram_figure.add_layout(line2)

    basemap_figure = fg(title=f'Basemap and track footprint: {track}', tools=['hover, wheel_zoom,pan,box_zoom,reset'],
                        x_range=x_range,
                        y_range=y_range,
                        lod_threshold=None,              
                        background_fill_color='white',
                        width=plot_size//4, height=plot_size)

    tile_source = BBoxTileSource(url=url_set)
    basemap_figure.add_tile(tile_source)
    
    gx, gy = geom.xy[0], geom.xy[1]
    geom_source = ColumnDataSource(data=dict(x=gx, y=gy)) 
    gxm, gym = geom.xy[0], geom_rep.xy[1]
    geom_source_M = ColumnDataSource(data=dict(x=gxm, y=gym)) 

    bounding_box_annotation = BoxAnnotation(left=min_Lon, right=max_Lon, 
                                        bottom=min_Lat, top=max_Lat, 
                                        fill_alpha=0.1, fill_color='blue', 
                                        line_color='blue')

    # Add the BoxAnnotation to the plot
    basemap_figure.add_layout(bounding_box_annotation)
    
    line_string = LineString(zip(gxm, gym))
    distances_km = [line_string.project(Point(x, y)) / 1000 for x, y in zip(gxm, gym)]
    geom_source.add(distances_km, 'distance_km')

    # Plot the line with the distance_km column in the HoverTool
    line = basemap_figure.line(x='x', y='y', source=geom_source, line_color='green', line_width=5, alpha=0.5, legend_label="Track footprint")
    
    kmFormatter = CustomJSTickFormatter(code=f'''
    var space = ' ';
    return (tick * {round(max(distances_km), 1)}).toFixed(1) + space + 'Km';
    ''')

    # Create a custom hover tooltip
    hover = HoverTool(renderers=[line], tooltips=[("Latitude", "@y{0.000}"), ("Longitude", "@x{0.000}"), ("Distance (km)", "@distance_km{0.00}")])

    # Add the hover tool to the figure
    basemap_figure.add_tools(hover)

    #cross_section_source_rgram = ColumnDataSource(data=dict(x=[], y=[]))
    #cross_section_source_scs = ColumnDataSource(data=dict(x=[], y=[]))

    # Create a Bokeh figure for the cross-section plot
    p_cross_section = fg(width=250, height=hgt, y_range=radargram_figure.y_range,tools=['hover, wheel_zoom,pan,box_zoom,reset',cht2],)
    p_cross_section.line(x='y', y='x', source=cross_section_source_rgram, line_color='blue', line_width=1,legend_label="SCS")
    p_cross_section.line(x='y', y='x', source=cross_section_source_scs, line_color='red', line_width=1,legend_label="ACQ")

    # Create power profiles
    ## define sources
    powerprof_acq_source = ColumnDataSource(data=dict(x=np.linspace(1,len(acq_pow_profile),len(acq_pow_profile)).astype(int)+left,y=acq_pow_profile))
    powerprof_scs_source = ColumnDataSource(data=dict(x=np.linspace(1,len(acq_pow_profile),len(acq_pow_profile)).astype(int)+left,y=scs_pow_profile))
    # create figure and add lines
    powerprofs = fg(title=f'SCS Surface Power Profiles: {track}',width=plot_size//2, height=int(hgt*0.65),  x_range=radargram_figure.x_range, tools=['hover, wheel_zoom,pan,box_zoom,reset',cht])#, x_range=(0, 100), y_range=(3600,0))
    powerprofs.line(x='x',y='y', source=powerprof_acq_source, line_color='green', line_width=1,legend_label="ACQ")
    powerprofs.line(x='x',y='y', source=powerprof_scs_source, line_color='red', line_width=1,legend_label="SCS")

    # Create Elevation profiles
    dem_profiles = fg(title=f'Elevation Profiles: {track}',width=plot_size//2, height=int(hgt*0.65),  x_range=radargram_figure.x_range, tools=['hover, wheel_zoom,pan,box_zoom,reset',cht])#, x_range=(0, 100), y_range=(3600,0))
    dem_profile_lola_source = ColumnDataSource(data=dict(x=np.linspace(1,len(dem_profile),len(dem_profile)).astype(int)+left,y=dem_profile))
    dem_profiles.line(x='x',y='y', source=dem_profile_lola_source, line_color='blue', line_width=1,legend_label="MOLA-HRSC")

    ### Prepare Drawing tool
    ### Convert data from subsurface HDF, if any, and make it available to the polygon tool
    
    xs = []
    ys = []
    #print('track',track)
    #print('subsurfacedf',subsurface_df)
    layer_df = subsurface_df.loc[subsurface_df.track_num.str.contains(track.split('s_')[-1])]
    layers_ids = subsurface_df.loc[subsurface_df["track_num"].str.contains(track)]['layer_id'].unique()
    #layers_ids = layer_df.layer_id.unique()
    print('layerdf',layer_df)
    print(subsurface_df.layer_id.unique())
    print('unique ids',layers_ids)
    track_layers_coords = []
    for ii, val in enumerate(layers_ids):
        layer_df = subsurface_df.loc[(subsurface_df.track_num.str.contains(track)) & (subsurface_df.layer_id== str(val))]
        print('layer_DF',layer_df)
        xs.append(np.array(layer_df["pt_cols"].values))#.astype(int)
        ys.append(np.array(layer_df["pt_lines"].values))
        layer_coords = list(zip(layer_df["pt_cols"],layer_df["pt_lines"]))
        track_layers_coords.append(layer_coords)   
    
    #print(len(xs), len(ys))
    
    source.data = dict(x=xs, y=ys, ids=layers_ids)
    #dst = ColumnDataSource(data=dict(x=[], y=[]))                               
    #print(source.data)
    

    #drawn_data = []
    #range_tool = RangeTool(x_range=radargram_figure.x_range)
    #source_xys = ColumnDataSource(data=dict(x=xs, y=ys))
    
    l1= radargram_figure.multi_line(xs='x', ys='y', source = source, line_color='red', line_width=3)
    draw_tool_l1 = PolyDrawTool(renderers=[l1])
    radargram_figure.add_tools(draw_tool_l1)



    radargram_figure.add_tools(HoverTool(show_arrow=False, line_policy='next', tooltips=[
    ('ID', '@ids')]))

    #### FORMAT PLOTs styles
    
    radargram_figure.xaxis.formatter = xFormatter
    radargram_figure.yaxis.formatter = yFormatter
    stack_figure.xaxis.formatter=xFormatter
    stack_figure.yaxis.formatter = yFormatter
    

    scs_figure.xaxis.formatter=xFormatter
    scs_figure.yaxis.formatter = yFormatter
    powerprofs.xaxis.formatter = xFormatter
    #powerprofs.yaxis.formatter=CustomJSTickFormatter(code = '''return `${(tick * 0.137).toFixed(0)}`;''')
    dem_profiles.xaxis.formatter = xFormatter

    p_cross_section.xaxis.formatter=CustomJSTickFormatter(code = '''return `${(tick).toFixed(0)}`;''') # removed thicks  * 0.137, since proper dB array is passed
    p_cross_section.yaxis.formatter = yFormatter
    #radargram_figure.legend.location = "top_center"
    #radargram_figure.legend.orientation = "horizontal"
    #radargram_figure.legend.label_text_font_size = '10pt'
    
    #radargram_figure.legend.location = "top_right"
    #radargram_figure.legend.orientation = "horizontal"        
    #radargram_figure_leg = radargram_figure.legend[0]
    #radargram_figure.legend[0] = None
    #radargram_figure.add_layout(radargram_figure_leg, 'above')
    
    powerprofs_leg = powerprofs.legend[0]
    powerprofs.legend[0] = None
    powerprofs.add_layout(powerprofs_leg, 'above')
    

    #powerprofs.legend.location = "top_center"
    #powerprofs.legend.orientation = "horizontal"
    #powerprofs.legend.label_text_font_size = '10pt'
    #powerprofs.legend.label_text_font_size = '10pt'

    dem_profiles_leg = dem_profiles.legend[0]
    dem_profiles.legend[0] = None
    dem_profiles.add_layout(dem_profiles_leg, 'above')
    
    save_button = Button(label="Save", button_type="success")
    print('Plots done')
    return(radargram_figure, scs_figure, stack_figure, basemap_figure, p_cross_section, powerprofs, dem_profiles, render_stack, render_radargram, render_scs, stack, geom_source, rolled_acq,  rolled_scs, rolled_acq_db, rolled_scs_db, rolled_acq_ori,  rolled_scs_ori, rolled_acq_db_ori, rolled_scs_db_ori,  max_width, max_height, geom, geom_length, subsurface_df, track)





#### Define functions for interactive plots and updates

def update_plots(attrname, old, new):
    boundingbox[0] = float(min_lon_input.value)
    boundingbox[1] = float(min_lat_input.value)
    boundingbox[2] = float(max_lon_input.value)
    boundingbox[3] = float(max_lat_input.value)
    roll = int(roll_input.value.strip())
    compression_value = compression_slider.value
    quality_value = quality_slider.value
    selected_track = track_select.value
    print(selected_track)
    
    radargram_figure, scs_figure, stack_figure, basemap_figure, p_cross_section, powerprofs, dem_profiles, render_stack, render_radargram, render_scs, stack, geom_source, rolled_acq, rolled_scs, rolled_acq_db, rolled_scs_db, rolled_acq_ori, rolled_scs_ori, rolled_acq_db_ori, rolled_scs_db_ori, max_width, max_height, geom, geom_length, subsurface_df, track = main(selected_track, boundingbox, roll, stack_titles, compression_value, quality_value)
    print('update main')
    
    slider_enh = Slider(start=0, end=stack.shape[0]-1, value=0, step=1, title="Enhanced Image Index")
    
    def update_image(attr, old, new):
        index = slider_enh.value
        stack_figure.title.text = f'{stack_titles[index]}: {selected_track}'
        render_stack.data_source.data['image'] = [np.array(stack[index, :, :])]
        
    def roll_image(attr, old, new):
        index = slider_enh.value
        roll = int(roll_input.value.strip())
        print("roll", roll)
        render_stack.data_source.data['image'] = [np.roll(np.array(stack[index, :, :]), roll, axis=0)]
        render_radargram.data_source.data['image'] = [np.roll(np.array(rolled_acq), roll, axis=0)]
        render_scs.data_source.data['image'] = [np.roll(np.array(rolled_acq), roll, axis=0)]
        
    vline = Span(dimension='height', line_color='red', line_width=2)
    
    callback = CustomJS(args=dict(vline=vline, cross_section_source=cross_section_source_rgram, left=left), code="""
        const { x, y } = cb_obj;
        const rolled_acq_db = %s;
        const image_width = %s;
        const image_height = %s;
        const adjustedX = x - left;
        if (adjustedX >= 0 && adjustedX < image_width) {
            cross_section_source.data.x = [x];
            vline.location = x;
            const cross_section = [];
            const colIndex = Math.round(adjustedX);
            for (let rowIndex = 0; rowIndex < image_height; rowIndex++) {
                cross_section.push(rolled_acq_db[rowIndex * image_width + colIndex]);
            }
            cross_section_source.data = { x: [...Array(image_height).keys()], y: cross_section };
            cross_section_source.change.emit();
            vline.change.emit();
        }
    """ % ((rolled_acq_db).flatten().tolist(), rolled_acq_db.shape[1], rolled_acq_db.shape[0]))
    
    callback2 = CustomJS(args=dict(vline=vline, cross_section_source=cross_section_source_scs, left=left), code="""
        const { x, y } = cb_obj;
        const rolled_scs_db = %s;
        const image_width = %s;
        const image_height = %s;
        const adjustedX = x - left;
        if (adjustedX >= 0 && adjustedX < image_width) {
            cross_section_source.data.x = [x];
            vline.location = x;
            const cross_section = [];
            const colIndex = Math.round(adjustedX);
            for (let rowIndex = 0; rowIndex < image_height; rowIndex++) {
                cross_section.push(rolled_scs_db[rowIndex * image_width + colIndex]);
            }
            cross_section_source.data = { x: [...Array(image_height).keys()], y: cross_section };
            cross_section_source.change.emit();
            vline.change.emit();
        }
    """ % ((rolled_scs_db).flatten().tolist(), rolled_scs_db.shape[1], rolled_scs_db.shape[0]))
    
    roll_input.on_change('value', update_plots)
    slider_enh.on_change('value', update_image)
    compression_slider.on_change("value", update_plots)
    quality_slider.on_change("value", update_plots)
    radargram_figure.js_on_event('mousemove', callback)
    radargram_figure.js_on_event('mousemove', callback2)
    scs_figure.js_on_event('mousemove', callback)
    scs_figure.js_on_event('mousemove', callback2)
    stack_figure.js_on_event('mousemove', callback)
    stack_figure.js_on_event('mousemove', callback2)
    powerprofs.js_on_event('mousemove', callback)
    powerprofs.js_on_event('mousemove', callback2)
    dem_profiles.js_on_event('mousemove', callback)
    dem_profiles.js_on_event('mousemove', callback2)
    
    layout.children[0].children[1].children = [roll_input, compression_slider,quality_slider]
    layout.children[0].children[2].children = [min_lon_input, min_lat_input, max_lon_input, max_lat_input, update_button]
    layout.children[0].children[3].children = [radargram_figure, p_cross_section]
    layout.children[0].children[4].children = [scs_figure, stack_figure, slider_enh]
    layout.children[0].children[5].children = [powerprofs, dem_profiles]
    layout.children[1].children = [basemap_figure]

#

    
    

def save_data():        
    selected_track = track_select.value
    selected_version = version_select.value
    track = f"{selected_track}"
    if selected_version == 'Original':
        hdf_file = f"{track_dir}subsurface_layers.h5"
        print('Loading Original')
    else:
        hdf_file = f"{track_dir}subsurface_layers_autopicked.h5"
        print('Loading Autopicked')
    
    subsurface_saver(source, track, hdf_file, [rolled_acq_ori, rolled_acq_db_ori], geom, geom_length, dem, track_dir, frequencies_array=None, selected_frequency=None)
    
def load_data():    
    selected_track = track_select.value
    selected_version = version_select.value
    track = f"{selected_track}"
    if selected_version == 'Original':
        hdf_file = f"{track_dir}subsurface_layers.h5"
        print('Loading Original')
    else:
        hdf_file = f"{track_dir}subsurface_layers_autopicked.h5"
        print('Loading Autopicked')
    try:
        subsurface_df = pd.read_hdf(hdf_file)
        subsurface_df = subsurface_df.reset_index(drop=True)
        #df = df[df["layer_id"].str.contains(f'{track}_surface') == False]
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
        radargram_figure.multi_line(xs='x', ys='y', source=source, line_color='red', line_width=3)
        print(f'loaded {selected_version}')
        print(xs_arrays)
        print(ys_arrays)
        print('len arrays')
        print(len(xs_arrays), len(ys_arrays))
    except Exception as e:
        print(e)

def autopick_data():
    selected_track = track_select.value
    print(selected_track)
    #for i in range(10):
    subsurface_df, xs, ys =  autopicker(selected_track, dem, [rolled_acq_ori, rolled_acq_db_ori], geom, geom_length, track_dir, frequencies_array=None, selected_frequency=None)
#    subsurface_df, xs, ys = autopicker(selected_track,layer_dict,dem_profile_ori)
    source.data = dict(x=xs, y=ys)    
    radargram_figure.multi_line(xs='x', ys='y', source=source, line_color='red', line_width=3)

    

    
### Set dummy track for initial plot

track = available_tracks[0]
track_select = Select(value=track, title='track', options=sorted(available_tracks))
version_select = Select(value='Original', title='Version', options=['Original', 'Auto-Picked'])
# Define roll_input box
roll_input = TextInput(value="0",title="Image roll value")    



stack_source = ColumnDataSource(data=dict(image=[]))
radargram_source = ColumnDataSource(data=dict(image=[]))
scs_source = ColumnDataSource(data=dict(image=[]))
cross_section_source_rgram = ColumnDataSource(data=dict(x=[], y=[]))
cross_section_source_scs = ColumnDataSource(data=dict(x=[], y=[]))

if track == available_tracks[0]:
    radargram_figure = fg(width=plot_size, height=plot_size//4)
    p_cross_section = fg(width=plot_size, height=plot_size//4)
    scs_figure = fg(width=plot_size, height=plot_size//4)
    stack_figure = fg(width=plot_size, height=plot_size//4)
    scs_figure = fg(width=plot_size//4, height=plot_size)
    powerprofs = fg(width=plot_size, height=plot_size//4)
    dem_profiles = fg(width=plot_size, height=plot_size//4)
    basemap_figure = fg(width=plot_size, height=plot_size//4)
    slider_enh = Slider(start=0, end=10, value=0, step=1, title="Enhanced Image Index")    
    #roll_input = TextInput(value="0",title="Image roll value")

    compression_slider = Slider(start=0.1, end=1.0, value=0.5, step=0.1, title="Compression Level (Scale Factor)")
    quality_slider = Slider(start=10, end=100, value=50, step=10, title="Image Quality (JPEG Quality)")

    #load_original_button = Button(label="Load original picked", button_type="success")
    save_button = Button(label="Save", button_type="success")
    autopick_button = Button(label="Autopick", button_type="success")
    load_button = Button(label="Load Data", button_type="success")    
    source = ColumnDataSource(data=dict(x=[], y=[]))

    
    rolled_acq, rolled_scs = np.empty([2, 2]), np.empty([2, 2])
    
else:
    print('ELSEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE')
    roll = int(roll_input.value.strip())
    print("roll", roll)
    radargram_figure, scs_figure, stack_figure, basemap_figure, p_cross_section, powerprofs, dem_profiles, render_stack, render_radargram, render_scs, stack,  geom_source, rolled_acq, rolled_scs, rolled_acq_db, rolled_scs_db, rolled_acq_ori,  rolled_scs_ori, rolled_acq_db_ori, rolled_scs_db_ori, max_width, max_height, geom, geom_length, subsurface_df, track = main(selected_track, boundingbox, roll, stack_titles, compression_value, quality_value)





radargram_figure.xaxis.major_label_text_font_size = '20pt'
radargram_figure.yaxis.major_label_text_font_size = '20pt'
radargram_figure.title.text_font_size = '15pt'
radargram_figure.xaxis.axis_label_text_font_size = '15pt'  # Change the font size of the x-axis title
radargram_figure.yaxis.axis_label_text_font_size = '15pt'  # Change the font size of the y-axis title
radargram_figure.xaxis.axis_label = 'Distance (Km)'
scs_figure.xaxis.axis_label = 'Distance (Km)'
radargram_figure.yaxis.axis_label = 'TWT (us)'
scs_figure.yaxis.axis_label = 'TWT (us)'
scs_figure.xaxis.major_label_text_font_size = '20pt'
scs_figure.yaxis.major_label_text_font_size = '15pt'
scs_figure.title.text_font_size = '15pt'
scs_figure.xaxis.axis_label_text_font_size = '15pt'  # Change the font size of the x-axis title
scs_figure.yaxis.axis_label_text_font_size = '15pt'  # Change the font size of the y-axis title
powerprofs.xaxis.axis_label = 'Distance (Km)'
powerprofs.yaxis.axis_label =  'Power (dB)'
powerprofs.legend.location = "top_right"
powerprofs.legend.orientation = "horizontal"
powerprofs.xaxis.major_label_text_font_size = '20pt'
powerprofs.yaxis.major_label_text_font_size = '15pt'
stack_figure.xaxis.major_label_text_font_size = '20pt'
stack_figure.yaxis.major_label_text_font_size = '15pt'
stack_figure.title.text_font_size = '15pt'
stack_figure.xaxis.axis_label_text_font_size = '14pt'  # Change the font size of the x-axis title
stack_figure.yaxis.axis_label_text_font_size = '14pt'  # Change the font size of the y-axis title
stack_figure.xaxis.major_label_text_font_size = '20pt'
stack_figure.yaxis.major_label_text_font_size = '20pt'
stack_figure.title.text_font_size = '15pt'
powerprofs.title.text_font_size = '15pt'
powerprofs.xaxis.axis_label_text_font_size = '15pt'  # Change the font size of the x-axis title
powerprofs.yaxis.axis_label_text_font_size = '15pt'  # Change the font size of the y-axis title
dem_profiles.xaxis.axis_label = 'Distance (Km)'
dem_profiles.yaxis.axis_label = 'Elevation (m)'
dem_profiles.xaxis.axis_label = 'Distance (Km)'
dem_profiles.yaxis.axis_label =  'Elevation (m)'
dem_profiles.legend.location = "top_right"
dem_profiles.legend.orientation = "horizontal"
dem_profiles.xaxis.major_label_text_font_size = '20pt'
dem_profiles.yaxis.major_label_text_font_size = '15pt'
dem_profiles.title.text_font_size = '15pt'
dem_profiles.xaxis.axis_label_text_font_size = '15pt'  # Change the font size of the x-axis title
dem_profiles.yaxis.axis_label_text_font_size = '15pt'  # Change the font size of the y-axis title
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
    
update_button = Button(label="Update Bounding Box", button_type="success")    
update_button.on_click(update_plots_wrapper)       

# Define final plot layout
demo_text = Div(text="""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #ddd; width: 600px;">
        <strong>This is a demo version using slow speed internet connections. Expect higher computing time</strong><br>
        Please visit <a href="https://github.com/Hyradus/EchoTerraeTrace" target="_blank">our official site</a> for more details.
    </div>
""", width=300, height=80)

layout = row(column(row(track_select, version_select, load_button, save_button, autopick_button, demo_text),
                    row(roll_input, compression_slider, quality_slider),
                    row(min_lon_input, min_lat_input, max_lon_input, max_lat_input, update_button),  
                    row(radargram_figure, p_cross_section),
                    row(scs_figure, stack_figure, slider_enh),
                    row(powerprofs, dem_profiles)),
                    column(basemap_figure))



curdoc().clear()

curdoc().add_root(layout)
# Show the figure
#show(fig)



