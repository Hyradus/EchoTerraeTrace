# Geospatial libraries
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiLineString, box
from shapely.ops import unary_union, transform
from pyproj import CRS, Transformer
import rioxarray as riox

# Bokeh for visualization
from bokeh.plotting import curdoc, figure, show
from bokeh.io import output_file, export_svgs, export_png
from bokeh.models import (
    Select, ColumnDataSource, LinearAxis, Range1d, PolyDrawTool, PointDrawTool, 
    LineEditTool, PolyEditTool, LabelSet, Label, HTMLTemplateFormatter, Slider, 
    CrosshairTool, Span, CustomJS, RangeTool, Div, HoverTool, CustomJSTickFormatter, 
    Button, Legend, DataTable, DateFormatter, TableColumn, Div
)
from bokeh.layouts import column, row
from bokeh.events import Tap

# Widgets
import ipywidgets as widgets

# Data handling and utilities
import pandas as pd
import numpy as np
from scipy.spatial import ConvexHull
from scipy.signal import argrelmin, find_peaks, find_peaks_cwt, peak_prominences
import json
from ast import literal_eval
from datetime import date
from random import randint
import os
import math

# Matplotlib for additional plotting
import matplotlib.pyplot as plt

# Custom utilities
from utils.genUtils import get_paths
from utils.profilers import dem_profiler_xarray, dem_profiler_sampling, power_profiler, dem_profiler_api

# Reference System
MARS2000 = CRS.from_wkt(
    'GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]'
)
DST_CRS = CRS.from_wkt(
    'PROJCS["Mars_Equidistant_Cylindrical",GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Equidistant_Cylindrical"],PARAMETER["False_Easting",0],PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",0],PARAMETER["Standard_Parallel_1",0],UNIT["Meter",1]]'
)

# Globals for file paths and data
global data_dir, source_table, table_data2, source_point_draw, source_draw
global plot_width, plot_height, table_width, table_height
global c, def_eps, eps, final_gdf, src_gdf, dem

# Constants and defaults
plot_width = 1920
plot_height = 800
table_width = 300
table_height = plot_height // 2
def_eps = 10
c = 299792458

# Directories and data paths
# Data Directory Setup
# Data Directory Setup
home = '/app/'  # Replace with `Path.home()` if needed  # Replace with `Path.home()` if needed
print(f"Home Directory: {home}")

# Default data directory
data_dir = '/Data/SHARAD/'#os.path.join(home, 'SHARAD')
#data_dir = '/home/hyradus/SyncThing/SyncData/SHARAD_PIT_DATA/Site_4/'
wcs_url = 'https://explore.hyranet.info/geoserver/ows?service=WCS'
dem_layerid = 'Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2-cog'
bmap_layerid = 'Mars_Viking_MDIM21_ClrMosaic_global_232m_crs'

track_dir = os.path.join(data_dir, 'SHARAD')
products_dir = os.path.join(data_dir, 'Products/Vectorial')
sharad_coverage = os.path.join(data_dir, 'SHARAD/Coverage/mars_mro_sharad_usrdr_c0l.shp')

# Read data and process GeoDataFrame
autopicked_f1 = 'subsurface_layers_autopicked.h5'
autopicked_gdf_name = os.path.join(products_dir,'subsurface_layers_autopicked.gpkg')

new_df = pd.read_hdf(os.path.join(track_dir, autopicked_f1))
new_df.twt2surf = new_df.pt_twts - new_df.surf_twts

# Create GeoDataFrame
#geometries = [Point(lon, lat) for lon, lat in zip(new_df.pt_lons, new_df.pt_lats)]
#src_gdf = gpd.GeoDataFrame(new_df, geometry=geometries, crs=MARS2000)
#filename = f'{os.path.splitext(autopicked_f1)[0]}.gpkg'
#savename = os.path.join(products_dir, autopicked_gdf_name)
#src_gdf.to_file(savename, driver='GPKG')

# Load existing GeoDataFrame or initialize
src_gdf = gpd.read_file(autopicked_gdf_name)
try:
    lava_flows_area_gpkg = os.path.join(products_dir, 'LavaFieldGroups_buffer_01.gpkg')
    lava_gdf = gpd.read_file(lava_flows_area_gpkg)        
except Exception as e:
    lava_gdf = None
    print(e)

basename, _ = os.path.splitext(autopicked_gdf_name)
final_gpkg = f'{basename}_final.gpkg'
try:
    final_gdf = gpd.read_file(final_gpkg)
    print('Final GDF Found')
    final_gdf = final_gdf.to_crs(MARS2000)
except Exception as e:
    final_gdf = gpd.GeoDataFrame(src_gdf)
    final_gdf = final_gdf.to_crs(MARS2000)
    print('Final GDF Initialized')

# DEM setup
dem_basepath = os.path.join(data_dir, 'Basemaps')
dem_name = f'{dem_layerid}.tiff'
dem_source = os.path.join(dem_basepath, dem_name)
print('QUERYING LOCAL DEM')
dem = riox.open_rasterio(dem_source, masked=True)
print('Local DEM found')

# Track number labels
data_labels = sorted(list(src_gdf.track_num.unique()))
print(data_labels)

def map_to_pixels(point, geom, max_width):
        distance_along_line = geom.project(point)
        x_pixel = (distance_along_line / geom.length) * max_width
        return x_pixel





    

def profiler(src_gdf, label,final_gdf, dem, lava_gdf):
    src_sub_df = src_gdf[src_gdf.track_num.str.contains(label)].copy()
    #print(src_sub_df.crs)
    #print(len(src_sub_df))#
    #[0:10]
    sub_df = src_gdf[src_gdf.track_num.str.contains(label.lower())].copy().to_crs(src_sub_df.crs)
#    sub_df.geometry = sub_df.geometry.buffer(10)
    print('sub_df shape',sub_df.shape)
    print(sub_df)
    try:
        track_file = os.path.join(track_dir,f's_{label}_footprint.gpkg')
        print(track_file)
        track_df = gpd.read_file(track_file)
        #track_df.to_crs(src_gdf)
        #print(track_df)
    except Exception as e:
        print('Error:' ,e)
    from shapely.geometry import MultiPolygon, LineString
        
    # Ensure both GeoDataFrames share the same CRS
    #lava_gdf = lava_gdf.to_crs(track_df.crs)
    
    # Extract the single polygon and line from the respective GeoDataFrames
    try:
        polygon = lava_gdf.loc[0].geometry
        track_df = track_df.to_crs(lava_gdf.crs)
        min_Lon, min_Lat, max_Lon, max_Lat = polygon.bounds
    except Exception as e:
        track_df = track_df.to_crs(MARS2000)
        min_Lon, min_Lat = list(track_df.geometry[0].coords)[0]
        max_Lon, max_Lat = list(track_df.geometry[0].coords)[-1]
    
    #print(polygon)
    
    line = track_df.geometry.loc[0]
#    print(line)
    
    # Initialize an empty geometry to store the cut results
    #cut_geometry = None
    #cut_geometry = line.intersection(polygon.geoms[0].buffer(0))
    
    transformer = Transformer.from_crs(MARS2000, DST_CRS, always_xy=True)
    transformed_geom = transform(transformer.transform, line)
    #elevation_data = sub_df.SurfElev
    geom_length = transformed_geom.length//1000
    
    # Save or analyze cut_track_df as needed

    # Function to map intersection points to pixel coordinates

    
    
    #elevation_data = getMOLA(line, dem, resolution=0.05)
    try:
        print('Acquiring DEM profile')
        #shape = acq_img_scaled.shape[1]
        import cv2 as cv
        track_image = os.path.join(track_dir,f's_{label}_rgram.png')
        img = cv.imread(track_image)
        
        #kmx2 =  np.array(np.array(src_gdf.pt_cols.values.astype('float64'))*math.ceil(geom_length/img.shape[1])).astype('float64')# for x_arr in src_gdf.pt_cols.values.astype('float64')]
        #kmx2 = src_gdf.pt_cols*geom_length/img_shape[1]
        
        
        shape = img.shape[1]
        print('image shape',shape)
        
        dem_basepath = os.path.join(data_dir,'Basemaps')
        dem_name = f'{dem_layerid}.tiff'
        dem_source = os.path.join(dem_basepath, dem_name)
        dem = riox.open_rasterio(dem_source, masked=True)
        print('EDIT:', dem_source)
        elevation_data = dem_profiler_sampling(dem_source, line, shape)
        print('elevation data shape',elevation_data.shape)
    except Exception as e:
        elevation_data = empty_array = np.empty(100)
        print('DEM Error: ',e)
    

    # Create a bounding box using the box function
    bbox = box(min_Lon, min_Lat, max_Lon, max_Lat)
    
    intersections = line.intersection(bbox.buffer(0))
    print('INTERSECTIONS',intersections)
    print(bbox)
    print(line)
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
            start_x_pixel = map_to_pixels(start_point, line, geom_length)#len(elevation_data))
            end_x_pixel = map_to_pixels(end_point, line, geom_length)#len(elevation_data))
            
            print(f"Intersection Point 1 at x-pixel: {start_x_pixel}")
            print(f"Intersection Point 2 at x-pixel: {end_x_pixel}")
            pixels.append(math.ceil(start_x_pixel))
            pixels.append(math.ceil(end_x_pixel))
        except Exception as e:
            print('Intersection error: ', e)
            print(intersections.coords)
            pixels.append(0)
            pixels.append(geom_length)
        print(pixels)
    else:
        print("No intersections found.")
        pixels.append(0)
        pixels.append(geom_length)    
        
    
    #cumulative_length = unary_union(geom_length)
    #kmx = np.linspace(src_gdf.pt_distances.values[0], src_gdf.pt_distances.values[-1], len(elevation_data))    
    # Step 1: Use the pixel values to find corresponding indices in kmx
    min_pixel = math.ceil(pixels[0])
    max_pixel = math.ceil(pixels[1])
    
    # Create visual Spans (lines for the selected range)
    line1 = Span(location=pixels[0], dimension='height', line_color='red', line_width=6)
    line2 = Span(location=pixels[1], dimension='height', line_color='red', line_width=6)
    
    # Generate the kmx array
    kmx = np.linspace(0, geom_length, len(elevation_data))   
    sub_df = sub_df.reset_index()
    kmx2 = sub_df.pt_cols.values.astype('float')*geom_length/img.shape[1]
    # Find the closest values in kmx for the pixels
    min_kmx_index = np.abs(kmx - min_pixel).argmin()  # Closest value in kmx to pixel[0]
    max_kmx_index = np.abs(kmx - max_pixel).argmin()  # Closest value in kmx to pixel[1]
    
    print('kmx', kmx, len(kmx))
    print('min max indexes', kmx[min_kmx_index], kmx[max_kmx_index])
    
    kmx_cut = kmx[min_kmx_index:max_kmx_index+1]
    min_kmx2_index = np.abs(kmx2 - kmx_cut.min()).argmin() # Closest value in kmx2 to kmx[min_kmx_index]
    max_kmx2_index = np.abs(kmx2 - kmx_cut.max()).argmin()# Closest value in kmx2 to kmx[max_kmx_index]
    print('min max indexes2', min_kmx2_index, max_kmx2_index)
    print('kmx2', kmx2, len(kmx2))
    
    kmx_min = kmx_cut.min()
    kmx_max = kmx_cut.max()
    
    
    kmx2_cut = kmx2[(kmx2 >= kmx_min) & (kmx2 <= kmx_max)]
    print(sub_df.index)
    sub_df_reset = sub_df.reset_index()  # Reset the index without inplace
    sub_df_cut = sub_df_reset.iloc[(kmx2 >= kmx_min) & (kmx2 <= kmx_max)]
    subsurface_twts_cut=sub_df_cut.pt_twts
    
    
    elevation_data_cut = elevation_data[min_kmx_index:max_kmx_index+1]
    
    
    print('kmx2_cut', kmx2_cut)
    
    
    
    
    print('cut sub_df', sub_df_cut)
    
    # Return all the relevant outputs
    return kmx_cut, kmx2_cut, elevation_data_cut, subsurface_twts_cut, sub_df_cut, line1, line2, pixels
    
    
#    return(kmx, kmx2, elevation_data, subsurface_twts,sub_df, line1,line2,pixels)

# Function to calculate the length of a line
def calculate_line_lengths(xs, ys):
    lengths = []
    for i in range(len(xs)):
        x = xs[i]
        y = ys[i]
        length = 0
        for j in range(1, len(x)):
            dx = x[j] - x[j - 1]
            dy = y[j] - y[j - 1]
            segment_length = ((dx ** 2) + (dy ** 2)) ** 0.5
            length += segment_length
        lengths.append(length)
    return lengths


# Function to handle line edit events
def update_table(attr, old, new):
    
    label = select_label.value
    xs = [i for i in l1.data_source.data['x']]
    ys = [i for i in l1.data_source.data['y']]
    #print('xs', xs)
    #print('ys', ys)
    ids = list(np.arange(0,len(xs)))
    if xs:
        # Calculate the length for the current geometry
        length = calculate_line_lengths(xs, ys)
        # Update the table data source
        source_table.data = {'ID':ids,'Distances': xs, 'Elevations': ys, 'Lengths': length}
        #print(source_table.data)


def update_pt_table(attr, old, new):
    
    label = select_label.value
    xs = [i for i in p1.data_source.data['x']]
    ys = [i for i in p1.data_source.data['y']]
    print('xs', xs)
    print('ys', ys)
    #print('SOURCE DATA',p1.data_source.data)
    ids = list(np.arange(0,len(xs)))
    types = ['' for el in ids]
           
    # Update the table data source
    source_table2.data = {'ID':ids,'Distances': xs, 'Elevations': ys, 'Type': types}     
    print(source_table2.data)
        
        
def download_table():
    label = select_label.value
    data = source_table.data
    
    print(data)
    
    for k in data:
        print('K:', k)
        print('VALUE:', data[k])        
        print('DTYPE:',type(data[k]))
    #columns = ("Distances","Elevations","Lengths")
    df = pd.DataFrame.from_dict(data)
    df.to_hdf(f"{data_dir}/{label}_profiles.hdf", 'profiles')
        
    # save points
    pt_data = source_table2.data
    print(pt_data)
    
    pt_df = pd.DataFrame.from_dict(pt_data)
    pt_df.to_hdf(f"{data_dir}/{label}_points.hdf", 'points')
    print('SAVE DONE')
    
def save_geopackage():    
    final_gdf.to_file(f"{basename}_final.gpkg",driver='GPKG')

def save_plot():
    plot_file=f"{data_dir}/{label}_plot.svg"  # save the results to a file
    plot_png=f"{data_dir}/{label}_plot.png" 
    plot.write_image(plot_file, engine="kaleido")
    #export_png(plot, filename=plot_png)
    #plot.output_backend = "svg"
    #export_svgs(plot, filename=plot_file) 


import math
def real_permittivity(delta_t, h):
    c = 3 * 10**8  # Speed of light in m/s
    # Calculate the real permittivity
    eps = ((c * delta_t*10**-6) / (2 * h)) ** 2
    return eps
def calculate_thickness(delta_t, epsilon_prime):
    c = 3 * 10**8  # Speed of light in m/s
    # Calculate the thickness
    h = (c * delta_t*10**-6) / (2 * math.sqrt(epsilon_prime))
    return h


# Define a function to update the plot based on the selected label
def update_plot(attr, old, new):
    global src_gdf
    eps = select_eps.value
    try:
        final_gdf = gpd.read_file(final_gpkg)
        print('Final GDF Found')
        if final_gdf.crs!=DST_CRS:
            final_gdf=final_gdf.to_crs(DST_CRS)
    except Exception as e:
        print(e)
        
        final_gdf=gpd.GeoDataFrame(src_gdf)
        final_gdf=final_gdf.to_crs(DST_CRS)
        print('Final GDF Initialized')

    print(eps)
    label = select_label.value
    print(label)
    src_gdf = gpd.read_file(autopicked_gdf_name)
    kmx, kmx2, elevation_data, subsurface_twts,src_gdf, line1, line2,pixels = profiler(src_gdf, label, final_gdf, dem, lava_gdf)
    print('Profiler Done')



    
    #print(subsurface_twts)
    #tickness = [(c*float(diff_twt))/2/(1e6)/(np.sqrt(eps)) for diff_twt in subsurface_twts]
    #subsurf_elevs = src_gdf.surf_elevs - tickness    
    #src_gdf['Relative Tickness']=tickness
    #src_gdf['Elevation']=subsurf_elevs
    #src_gdf['Eps']=eps
    #src = src_gdf.copy()
    src_gdf['twt2surf'] = abs(src_gdf.surf_twts - src_gdf.pt_twts)
    print(src_gdf.twt2surf)
    # Calculate thickness using Eps = 7
    src_gdf['Thickness'] = src_gdf.apply(lambda row: calculate_thickness(row['twt2surf'], eps), axis=1)
    
    print('THICKNESSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS',src_gdf['Thickness'])
    subsurf_elevs = src_gdf.surf_elevs - src_gdf.Thickness
    #subsurf_elevs = np.empty_like(subsurf_elevs)
    #subsurf_elevs, kmx2 = [], []
    #joined_gdf1.crs=mesh_gdf1.crs
    final_gdf=final_gdf[final_gdf.track_num.str.contains(label)==False]
    src_gdf=src_gdf.to_crs(MARS2000)
    #final_gdf = pd.concat([final_gdf,src_gdf]).reset_index(drop=True)
    #final_gdf = final_gdf[['track_num','layer_id','Site4_TPIC', 'Site4_MOLA', 'Relative Tickness', 'Elevation', 'Eps','pt_lons', 'pt_lons_m', 'pt_lats', 'pt_lats_m', 'pt_twts', 'twt2surf','pt_cols', 'pt_lines', 'geometry']]
    #final_gdf.to_file(final_gpkg)
    #print('GPKG Saved')
    #mesh_gdf1[mesh_gdf1.layer_id.str.contains(label[0:10].lower()),'Elevation']=subsurf_elevs    
    width = Span(dimension="width")
    height = Span(dimension="height")
    cht = CrosshairTool(overlay=[width, height])
    plot = figure(title=f'Acquisition: {label}',width=plot_width, height=plot_height,tools=[' wheel_zoom,pan,box_zoom,reset,lasso_select',cht])
    plot.xaxis.major_label_text_font_size = '20pt'
    plot.yaxis.major_label_text_font_size = '20pt'
    plot.title.text_font_size = '15pt'
    plot.xaxis.axis_label = "Distance (Km)"
    plot.yaxis.axis_label = "Elevation (m)"
    plot.xaxis.axis_label_text_font_size = "18pt"
    plot.yaxis.axis_label_text_font_size = "18pt"
    plot.xaxis.axis_label_text_font_style = "bold"
    plot.yaxis.axis_label_text_font_style = "bold"
    plot.x_range.start = pixels[0]#kmx2[0]-100
    plot.x_range.end = pixels[1]#kmx2[-1]+100
    # Define Line Plot + Hover
    plot.add_layout(line1)
    plot.add_layout(line2)
    source_dem = ColumnDataSource(data={'x': kmx, 'y': elevation_data})
    dem_profile = plot.line(x='x', y='y', source=source_dem, line_width=5,line_color='dodgerblue')
    dem_points = plot.scatter(x='x', y='y', source=source_dem, color='dodgerblue',size=3)
    source_subs = ColumnDataSource(data={'layer_id':src_gdf.layer_id.values,'x': kmx2, 'y': subsurf_elevs})
    subs = plot.scatter(x='x', y='y', source=source_subs, size=5, color='blue')
    hover = HoverTool(renderers=[dem_profile], tooltips=[("Elevation", "@y{0.000}"), ("Distance (km)", "@x{0.00}")])
    hover2 = HoverTool(renderers=[subs], tooltips=[("Layer ID", "@layer_id"), ("Distance (km)", "@x{0.00}")])
    plot.add_tools(hover)
    plot.add_tools(hover2)
    
    
    

    

    # Create a new data source for the best-fit line
    s2.data=dict(x=[], ym=[],slope=[],intercept=[])
    sline = plot.line(x='x', y='ym', color="orange", line_width=5, alpha=0.6, source=s2)
    

    source_dem.selected.js_on_change('indices', CustomJS(args=dict(s=source_dem, s2=s2), code="""
        const inds = s.selected.indices;
        if (inds.length > 1) {
            const x = s.data.x;
            const y = s.data.y;

            // Create arrays to store the selected data points
            let selectedX = [];
            let selectedY = [];
            for (let i = 0; i < inds.length; i++) {
                selectedX.push(x[inds[i]]);
                selectedY.push(y[inds[i]]);
            }

            // Calculate the coefficients for the best-fit line (linear regression)
            const sumX = selectedX.reduce((a, b) => a + b, 0);
            const sumY = selectedY.reduce((a, b) => a + b, 0);
            const sumXY = selectedX.map((x, i) => x * selectedY[i]).reduce((a, b) => a + b, 0);
            const sumX2 = selectedX.map(x => x ** 2).reduce((a, b) => a + b, 0);
            const n = selectedX.length;

            const m = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX ** 2);
            const c = (sumY - m * sumX) / n;

            // Calculate the best fit line using the full range of x values
            const bestFitLine = x.map(x => m * x + c);
            // Create an array of the same length as x filled with the same slope value
            const slopeArray = Array(x.length).fill(m);

            // Create an array of the same length as x filled with the same intercept value
            const interceptArray = Array(x.length).fill(c);

            // Update s2's data with the best fit line, slope, and intercept
            s2.data = { x: x, ym: bestFitLine, slope: slopeArray, intercept: interceptArray };

        } else {
            // If fewer than 2 points are selected, clear the best fit line
            s2.data = { x: [], ym: [], slope: [], intercept:[] };
        }
    """))
    s3.data=dict(x=[], ym=[],slope=[],intercept=[])
    sline2 = plot.line(x='x', y='ym', color="purple", line_width=5, alpha=0.6, source=s3)
    source_subs.selected.js_on_change('indices', CustomJS(args=dict(s=source_subs, s2=s3), code="""
        const inds = s.selected.indices;
        if (inds.length > 1) {
            const x = s.data.x;
            const y = s.data.y;

            // Create arrays to store the selected data points
            let selectedX = [];
            let selectedY = [];
            for (let i = 0; i < inds.length; i++) {
                selectedX.push(x[inds[i]]);
                selectedY.push(y[inds[i]]);
            }

            // Calculate the coefficients for the best-fit line (linear regression)
            const sumX = selectedX.reduce((a, b) => a + b, 0);
            const sumY = selectedY.reduce((a, b) => a + b, 0);
            const sumXY = selectedX.map((x, i) => x * selectedY[i]).reduce((a, b) => a + b, 0);
            const sumX2 = selectedX.map(x => x ** 2).reduce((a, b) => a + b, 0);
            const n = selectedX.length;

            const m = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX ** 2);
            const c = (sumY - m * sumX) / n;

            // Calculate the best fit line using the full range of x values
            const bestFitLine = x.map(x => m * x + c);
            // Create an array of the same length as x filled with the same slope value
            const slopeArray = Array(x.length).fill(m);

            // Create an array of the same length as x filled with the same intercept value
            const interceptArray = Array(x.length).fill(c);

            // Update s2's data with the best fit line, slope, and intercept
            s2.data = { x: x, ym: bestFitLine, slope: slopeArray, intercept: interceptArray };

        } else {
            // If fewer than 2 points are selected, clear the best fit line
            s2.data = { x: [], ym: [], slope: [], intercept:[] };
        }
    """))

    # Check if draw Define Draw Tool
    
    
    table_data = {'ID':[],'Distances': [], 'Elevations': [], 'Lengths': []}
    hdf_file=f"{data_dir}/{label}_profiles.hdf"
    try:                
        df = pd.read_hdf(hdf_file,'profiles')
        #df['Distances'] = df['Distances'].apply(literal_eval)
        #df['Elevations'] = df['Elevations'].apply(literal_eval)
        table_data['ID']=df.ID.values
        table_data['Distances']=df.Distances.values
        table_data['Elevations']=df.Elevations.values
        table_data['Lengths']=df.Lengths.values
    except Exception as e:        
        print(e)
        pass 
    
    xs = [list(el) for el in table_data['Distances']]
    ys = [list(el) for el in table_data['Elevations']]
    source_draw.data = dict(x=xs, y=ys)
    
    l1= plot.multi_line(xs='x', ys='y', source = source_draw, line_color='red', line_width=3)        
    c1 = plot.scatter([], [], size=10, color='red')
    draw_tool_l1 = PolyDrawTool(renderers=[l1], vertex_renderer=c1)
    plot.add_tools(draw_tool_l1)
    
    edit_tool = PolyEditTool(renderers=[l1])
    plot.add_tools(edit_tool)
    
    # Define Draw Tool
    
    
    # Define Draw Tool
    table_data2 = {'ID':[],'Distances': [], 'Elevations': [], 'Type': []}
    hdf_pt_file=f"{data_dir}/{label}_points.hdf"    
    try:                
        df = pd.read_hdf(hdf_pt_file,'points')
        #df['Distances'] = df['Distances'].apply(literal_eval)
        #df['Elevations'] = df['Elevations'].apply(literal_eval)
        table_data2['ID']=df.ID.values
        table_data2['Distances']=df.Distances.values
        table_data2['Elevations']=df.Elevations.values
        table_data2['Type']=df['Type'].values
        print('PT_TABLE',table_data2)
        print(df)
    except Exception as e:        
        print(e)
        pass 
    # Define Draw Tool
    
    
    pxs = table_data2['Distances']
    pys = table_data2['Elevations']
    source_point_draw.data = dict(x=pxs, y=pys)

    p1= plot.scatter(x='x', y='y', source = source_point_draw, color='darkgreen',  size=20)          
    draw_tool_p1 = PointDrawTool(renderers=[p1])
    plot.add_tools(draw_tool_p1)
    
    source_table.data = table_data
    source_table2.data = table_data2  
    #source_subs.data = dict(x=kmx2, y=subsurf_elevs)
    
    line_labels = LabelSet(x='Distances', y='Elevations', text='Lengths', text_font_size="30pt", level='glyph',
              x_offset=10, y_offset=10, source=source_table)
    #pt_labels = LabelSet(x='Distances', y='Elevations', text='Type', text_font_size="30pt", level='glyph',
    #          x_offset=10, y_offset=10, source=source_pt_table)

    citation = Label(x=100, y=100, x_units='screen', y_units='screen',
                 text='Nodjoumi et al., 2023',
                 border_line_color='black', border_line_alpha=1.0,
                 background_fill_color='white', background_fill_alpha=1.0)
    
    #plot.add_layout(pt_labels)
    plot.add_layout(line_labels)
    layout.children[0].children[1] = plot
    


# Create an initial Line plot with a placeholder
plot = figure(title="Elevation Profile", x_axis_label="Distance (km)", y_axis_label="Elevation (m)",
              width=800, height=400)
width = Span(dimension="width")
height = Span(dimension="height")
cht = CrosshairTool(overlay=[width, height])
# Set plot axis ranges
plot.x_range = Range1d(0, 1)
plot.y_range = Range1d(0, 1)

label=data_labels[0]

kmx, kmx2, elevation_data,subsurface_twts,src_gdf, line1, line2,pixels = profiler(src_gdf, label, final_gdf, dem, lava_gdf)
# Step 1: Find the closest values to kmx2's min and max in kmx
print('kmx2',kmx2)
try:
    min_kmx2 = kmx2.min()
    max_kmx2 = kmx2.max()
except:
    min_kmx2, max_kmx2 = 0,0


# Step 3: Slice the elevation_data and kmx using the buffered indices
#elevation_data = elevation_data[min_index_buffered:max_index_buffered+1]
#kmx = kmx[min_index_buffered:max_index_buffered+1]



width = Span(dimension="width")
height = Span(dimension="height")
cht = CrosshairTool(overlay=[width, height])
plot = figure(title=f'Acquisition: {label}',width=plot_width, height=plot_height,tools=[' wheel_zoom,pan,box_zoom,reset',cht])
plot.xaxis.major_label_text_font_size = '20pt'
plot.yaxis.major_label_text_font_size = '20pt'
plot.title.text_font_size = '15pt'
plot.xaxis.axis_label = "Distance (Km)"
plot.yaxis.axis_label = "Elevation (m)"
# Initialize plot sources
source_dem = ColumnDataSource(data={'x': kmx, 'y': elevation_data})
#subsurf_elevs = src_gdf.surf_elevs - [(c*float(diff_twt))/2/(1e6)/(np.sqrt(def_eps)) for diff_twt in subsurface_twts]
src_gdf['twt2surf'] = abs(src_gdf.surf_twts - src_gdf.pt_twts)
print('twt2surf',src_gdf.twt2surf)
src_gdf['Thickness'] = src_gdf.apply(lambda row: calculate_thickness(row['twt2surf'], def_eps), axis=1)
print('Thickness',src_gdf['Thickness'])
subsurf_elevs = src_gdf.surf_elevs - src_gdf.Thickness
#joined_gdf1.crs=mesh_gdf1.crs
source_subs = ColumnDataSource(data={'x': kmx2, 'y': subsurf_elevs})

# Create Plots
dem_profile = plot.line(x='x', y='y', source=source_dem, line_width=2,line_color='dodgerblue')
dem_points = plot.scatter(x='x', y='y', source=source_dem, color='dodgerblue',size=3)
subs = plot.scatter(x='x', y='y', source=source_subs, size=5, color='blue')
plot.add_layout(line1)
plot.add_layout(line2)
# Define Hover

hover = HoverTool(renderers=[dem_profile], tooltips=[("Elevation", "@y{0.000}"), ("Distance (km)", "@x{0.00}")])
hover2 = HoverTool(renderers=[subs], tooltips=[("Elevation", "@y{0.000}"), ("Distance (km)", "@x{0.00}")])
plot.add_tools(hover,hover2)

# Define LINE DRAW Tool

table_data = {'ID':[],'Distances': [], 'Elevations': [], 'Lengths': []}
   

xs = [table_data['Distances']]
ys = [table_data['Elevations']]

source_draw = ColumnDataSource(data=dict(x=xs, y=ys))
l1= plot.multi_line(xs='x', ys='y', source = source_draw, line_color='red', line_width=3)        
c1 = plot.scatter([], [], size=10, color='red')
draw_tool_l1 = PolyDrawTool(renderers=[l1], vertex_renderer=c1)
plot.add_tools(draw_tool_l1)

edit_tool = PolyEditTool(renderers=[l1])
plot.add_tools(edit_tool)

source_table = ColumnDataSource(data=table_data)

columns = [
    TableColumn(field="ID", title="ID"),
    TableColumn(field="Distances", title="Distances"),
    TableColumn(field="Elevations", title="Elevations"),
    TableColumn(field="Lengths", title="Lengths"),
]

data_table = DataTable(source=source_table, columns=columns,editable=True, width=table_width, height=table_height, autosize_mode='fit_columns')



table_data2 = {'ID':[],'Distances': [], 'Elevations': [], 'Type': []}

# Define Draw Tool
pxs = []
pys = []
source_point_draw = ColumnDataSource(data=dict(x=pxs, y=pys))

p1= plot.scatter(x='x', y='y', source = source_point_draw, color='darkgreen',  size=20)    
draw_tool_p1 = PointDrawTool(renderers=[p1])
plot.add_tools(draw_tool_p1)

source_table2 = ColumnDataSource(data=table_data2)

columns2 = [
    TableColumn(field="ID", title="ID"),
    TableColumn(field="Distances", title="Distances"),
    TableColumn(field="Elevations", title="Elevations"),
    TableColumn(field="Lengths", title="Lengths"),
]

data_table2 = DataTable(source=source_table2, columns=columns2,editable=True, width=table_width, height=table_height, autosize_mode='fit_columns')



# Define the custom CSS style to change the font size
custom_style = """
<style>
    .slick-cell {
        font-size: 20px; 
    }
</style>
"""

# Create a template with the custom style
template = HTMLTemplateFormatter(template=custom_style)
#data_pt_table.columns.formatter = template
#################################

s2 = ColumnDataSource(data=dict(x=[], ym=[], slope=[],intercept=[]))
s2_columns = [
    TableColumn(field="x", title="x"),
    TableColumn(field="ym", title="y"),    
    TableColumn(field="slope", title="Slope"),    
    TableColumn(field="intercept", title="Intercept"),
]
table_s2_data = {'ID':[],'x': [], 'y': [], 'Slope': [], 'Intercept': []}
data_s2_table = DataTable(source=s2, columns=s2_columns,editable=True, width=table_width, height=table_height, autosize_mode='fit_columns')

s3 = ColumnDataSource(data=dict(x=[], ym=[], slope=[],intercept=[]))
s3_columns = [
    TableColumn(field="x", title="x"),
    TableColumn(field="ym", title="y"),    
    TableColumn(field="slope", title="Slope"),    
    TableColumn(field="intercept", title="Intercept"),
]
table_s3_data = {'ID':[],'x': [], 'y': [], 'Slope': [], 'Intercept': []}
data_s3_table = DataTable(source=s3, columns=s3_columns,editable=True, width=table_width, height=table_height, autosize_mode='fit_columns')

# Define widgets
save_button = Button(label="Save GeoPackage")
download_button = Button(label="Save Tables")
save_plot_button = Button(label="Save Plot")
select_label = Select(title="Select Label:", options=data_labels)
select_eps = Slider(start=5, end=20, value=10, step=1, title="Permittivity")



# Define Callbacks
callback_table = CustomJS(args=dict(src=source_table), code="""
    const data = cb_obj.data;
    src.data = data;
    src.change.emit();
""")

callback_l1 = CustomJS(args=dict(src=source_draw), code="""
    const data = cb_obj.data;
    src.data = data;
    src.change.emit();
""")

callback_table2 = CustomJS(args=dict(src=source_table2), code="""
    const data = cb_obj.data;
    src.data = data;
    src.change.emit();
""")

callback_p1 = CustomJS(args=dict(src=source_point_draw), code="""
    const data = cb_obj.data;
    src.data = data;
    src.change.emit();
""")

callback_eps_data = CustomJS(args=dict(src=source_subs), code="""
    const data = cb_obj.data;
    src.data = data;
    src.change.emit();
""")

# Set listeners





download_button.on_click(download_table)  
save_button.on_click(save_geopackage)
save_plot_button.on_click(save_plot)
# Set up the listener for the 'label' variable
select_label.on_change('value', update_plot)
#subs.data_source.on_change('data',update_table)
# Set up a listener for the line edit tool
l1.data_source.on_change('data', update_table)
# Set up the listener for the 'point' tool
p1.data_source.on_change('data', update_pt_table)
########################

# Set up listener for the eps calculator
#select_eps.js_on_change('value', callback_eps)
select_eps.on_change('value', update_plot)

# Set up the listener for the 'source_table' variable
source_table.js_on_change("data", callback_table)
# Set up the listener for the 'source_draw' variable
source_draw.js_on_change("data", callback_l1)
source_subs.js_on_change("data", callback_eps_data)
# Set up the listener for the 'source_pt_table' variable
source_table2.js_on_change("data", callback_table2)
# Set up the listener for the 'source_draw' variable
source_point_draw.js_on_change("data", callback_p1)   
#######################
#s2.js_on_change("data",callback_s2)


from bokeh.io import export_svg, export_png
from bokeh.plotting import figure, output_file, save
# Create a button to trigger the export
export_button = Button(label="Export PNG")
export_button_svg = Button(label="Export SVG")

# Function to export the plot to a PNG file
def export_to_png():
    label = select_label.value
    export_png(layout, filename=f"{label}_plot.png")


def export_to_svg():   
    label = select_label.value
    export_svg(layout, filename=f"{label}_plot.svg")
    
export_button.on_click(export_to_png)
export_button_svg.on_click(export_to_svg)
 
                             
# Attach a callback to update the label when the Select widget value changes
#def update_label(attr, old_value, new_value):
#    download_button.label = f"Download {new_value} Table"  # Update the button label
#select_label.on_change('value', update_label)
title_line = Div(text="""<h2 style="text-align: center;">Draw Lines</h2>""")
title_points = Div(text="""<h2 style="text-align: center;">Draw Points</h2>""")
title_bestfit = Div(text="""<h2 style="text-align: center;">BestFit lines</h2>""")


demo_text = Div(text="""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #ddd; width: 600px;">
        <strong>This is a demo version using slow speed internet connections. Expect higher computing time</strong><br>
        Please visit <a href="https://github.com/Hyradus/EchoTerraeTrace" target="_blank">our official site</a> for more details.
    </div>
""", width=300, height=80)

# Create layout
layout = row(column(row(select_label,select_eps,save_button,export_button,export_button_svg,demo_text,),plot), column(row(download_button), row((column(title_line, data_table, title_points,data_table2)),column(title_bestfit,data_s2_table,data_s3_table))))


# Add layout to the current document
#curdoc().theme = 'dark_minimal'
curdoc().clear()
curdoc().title = "EchoTerraeTrace -Profiler"  
curdoc().add_root(layout)