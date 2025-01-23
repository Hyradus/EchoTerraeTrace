import geopandas as gpd
from bokeh.models import Select, ColumnDataSource, LinearAxis, Range1d, PolyDrawTool,PointDrawTool,LineEditTool,LabelSet, Label,HTMLTemplateFormatter, PolyEditTool,Slider
from bokeh.plotting import curdoc, figure, show
import rioxarray
from shapely.geometry import Point, LineString, Polygon
import numpy as np
from scipy.spatial import ConvexHull
from scipy.signal import argrelmin, find_peaks, find_peaks_cwt, peak_prominences
import math
from shapely.ops import unary_union
import ipywidgets as widgets
#from utils.mainFunc import subsurface_saver, main
from utils.genUtils import get_paths
from utils.profilers import dem_profiler_xarray, dem_profiler_api
import matplotlib.pyplot as plt
import os
import pandas as pd
from ast import literal_eval
from bokeh.models import CrosshairTool, Span, CustomJS, RangeTool, Div
from bokeh.plotting import figure as fg
from bokeh.layouts import column, row
from bokeh.events import Tap
from bokeh.models import HoverTool, CustomJSTickFormatter, Button
from bokeh.io import output_file
from datetime import date
from random import randint
from bokeh.io import show, export_svgs, export_png
from bokeh.models import ColumnDataSource, DataTable, DateFormatter, TableColumn
import json
from pyproj import CRS
from pathlib import Path
from pyproj import CRS, Transformer
from shapely.ops import transform
from shapely.geometry import LineString, Point
from shapely.ops import split, linemerge, substring
from bokeh.models import RangeSlider


MARS2000 = CRS.from_wkt('GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]')
DST_CRS = CRS.from_wkt('PROJCS["Mars_Equidistant_Cylindrical",GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Equidistant_Cylindrical"],PARAMETER["False_Easting",0],PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",0],PARAMETER["Standard_Parallel_1",0],UNIT["Meter",1]]')
MARS0360 = CRS.from_wkt('GEOGCRS["GCS_Mars",    DATUM["D_Mars",        ELLIPSOID["Mars_2000_IAU_IAG", 3396190, 169.8944472236118, LENGTHUNIT["metre", 1]]],    PRIMEM["Reference_Meridian", 0, ANGLEUNIT["degree", 1]],    CS[ellipsoidal, 2],        AXIS["longitude", east, ORDER[1], ANGLEUNIT["degree", 1, ID["EPSG", 9122]]],        AXIS["latitude", north, ORDER[2], ANGLEUNIT["degree", 1, ID["EPSG", 9122]]],    ID["EPSG", 49900]]')

#MARS2000 = CRS.from_wkt('GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]')
MARS2000 = CRS.from_wkt('GEOGCS["GCS_Mars_2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.894447223612]],PRIMEM["Reference_Meridian",0.0],UNIT["Degree",0.0174532925199433]]')
global data_dir
global source_table
global table_data2
global source_point_draw
global source_draw
global plot_width
global plot_height
global table_width
global table_height
global c
global def_eps
global eps
global final_gdf
global df
global dem_distances
global previous_range
global global_slider_range

plot_width=1920
plot_height=800
table_width=300
table_height=plot_height//2



# Data Directory Setup
home = '/app/'  # Replace with `Path.home()` if needed  # Replace with `Path.home()` if needed
print(f"Home Directory: {home}")

# Default data directory
data_dir = '/Data/MARSIS/'#os.path.join(home, 'SHARAD')
#data_dir = '/mnt/OrbitalData/Mars/MARSIS/MARSIS_DATA/Zephyria_Planum/'
print(data_dir)
file_list = get_paths(data_dir, 'dat')

# Create the Select widget
freq_select = Select(value='F1', title='Frequency', options=['F1', 'F2'])

# Function to load data based on the selected frequency
def load_data(selected_freq):
    global hdf_file, df
    hdf_file = os.path.join(data_dir, f'subsurface_layers_{selected_freq}.h5')
    if os.path.exists(hdf_file):
        df = pd.read_hdf(hdf_file)
        print(f"Data loaded for {selected_freq}:")
        print(df.head())  # Replace this with any Bokeh update logic
        return df
    else:
        print(f"File {hdf_file} does not exist.")
        return None

# Callback function for the Select widget
def update_data(attr, old, new):
    selected_freq = freq_select.value
    load_data(selected_freq)

# Attach the callback to the Select widget
freq_select.on_change('value', update_data)


# Load initial data
load_data(freq_select.value)

#hdf_file = os.path.join(data_dir, 'subsurface_layers_F1.h5')
#df = pd.read_hdf(hdf_file)
geometries = [Point(lon, lat) for lon,lat in list(zip(df.pt_lons,df.pt_lats))]


data_labels = list(df.track_num.unique())
print(data_labels)
data_labels.insert(0,'0000000')



def_eps = 10
c = 299792458




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


from shapely.geometry import LineString, Point
import numpy as np

def create_linestring_with_interpolated_points(point1, point2, num_points):
    # Extract the coordinates of the two points
    x1, y1 = point1.x, point1.y
    x2, y2 = point2.x, point2.y
    
    # Interpolate 'num_points' points between point1 and point2
    x_values = np.linspace(x1, x2, num_points)
    y_values = np.linspace(y1, y2, num_points)
    
    # Create a list of interpolated Point objects
    interpolated_points = [Point(x, y) for x, y in zip(x_values, y_values)]
    
    # Create and return the LineString from the list of points
    return LineString(interpolated_points)


# Define a function to update the plot based on the selected label
def update_plot(attr, old, new
               ):
    label = select_label.value
    eps = select_eps.value
    
    hdf_file = os.path.join(data_dir, 'subsurface_layers_F1.h5')
    df = pd.read_hdf(hdf_file)
    geom = gpd.read_file(f'{data_dir}/{label}_geometry.gpkg').loc[0].geometry
    array_size = len(geom.xy[0])
    label = select_label.value

    track_df = df[df.track_num.str.contains(label)]
    geometries = [Point(lon, lat) for lon,lat in list(zip(track_df.pt_lons,track_df.pt_lats))]
    print(label)


    dem_layerid = 'Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2-cog' # Default DEM available on EXPLORE WCS.  Is it 
    dem_basepath = os.path.join(data_dir,'Basemaps')
    dem_name = f'{dem_layerid}.tiff'
    dem_source = os.path.join(dem_basepath, dem_name)
    print('EDIT:',dem_source)
    transformer = Transformer.from_crs(MARS2000, DST_CRS, always_xy=True)
    transformed_geom = transform(transformer.transform, geom)
    dem_array_size = np.array(geom.xy[0]).shape[0]
    dem_distances = np.linspace(0, transformed_geom.length/1000, dem_array_size) 
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
        elevation_data = np.concatenate(all_elevations)
        print('done')
    
    except Exception as e:
        print('LOCAL DEM FAILED',e)
    
        try:
            print('Querying API')
            elevation_data = dem_profiler_api(geom,'Mars')
            
            
        except Exception as e:
            print('API FAILED',e)
            elevation_data = np.empty((1,array_size))
            
            





    pt_distances = []
    for point in geometries:
        # Project the point onto the line
        proj_point = geom.interpolate(geom.project(point))
        #surf_elev.append(dem_profiler2(point, dem))
        transformed_point = transform(transformer.transform, point)
        
        
        # Now you can use the project method on the transformed geometries
        pt_distances.append(transformed_geom.project(transformed_point)/1000)
        
    
        # Check if the projected point matches the original point
        if proj_point.equals(point):
            print("The point lies exactly on the line.")
        else:
            print("The point does not lie on the line.")
    #pt_distances
    pt_distances = np.array(pt_distances)

    tickness = [(c*float(diff_twt))/2/(1e6)/(np.sqrt(eps)) for diff_twt in track_df.twt2surf.values]

    dem = rioxarray.open_rasterio(dem_source, masked=True)
    surf_elev = dem_profiler_xarray(LineString(geometries), dem)

    subsurf_elevs = surf_elev - tickness    

    # Create a LineString with 50 interpolated points between point1 and point2
    num_interpolated_points = len(pt_distances)
    line = create_linestring_with_interpolated_points(geometries[0], geometries[-1], num_interpolated_points)
    
    # Output the new LineString and its length
    #print(f"LineString with {num_interpolated_points} points: {line}")
    #print(f"Number of points in LineString: {len(line.coords)}")
########################## TEMPORARY FIX

        # Step 1: Find the closest matching points between surf_eleves and elevation_data
    closest_indices = [np.argmin(np.abs(elevation_data - ele)) for ele in surf_elev]
    
    # Extract the corresponding distances from dem_distances
    matched_dem_distances = dem_distances[closest_indices]
    
    # Step 2: Compute the offset (difference in starting points)
    pt_start = pt_distances[0]
    dem_start = matched_dem_distances[0]
    
    offset = pt_start - dem_start





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
    # Define Line Plot + Hover
    
    source_dem = ColumnDataSource(data={'x': dem_distances+int(offset/2), 'y': elevation_data})
    dem_profile = plot.line(x='x', y='y', source=source_dem, line_width=5,line_color='dodgerblue')
    dem_points = plot.circle(x='x', y='y', source=source_dem, color='dodgerblue',size=3)
    source_subs = ColumnDataSource(data={'x': pt_distances, 'y': subsurf_elevs})
    subs = plot.circle(x='x', y='y', source=source_subs, size=5, color='blue')
    hover = HoverTool(renderers=[dem_profile], tooltips=[("Elevation", "@y{0.000}"), ("Distance (km)", "@x{0.00}")])
    plot.add_tools(hover)
    
    
    

    

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
        table_data['ID']=track_df.layer_id.values
        table_data['Distances']=dem_distances
        table_data['Elevations']=elevation_data
        table_data['Lengths']=dem_distances
    except Exception as e:        
        print(e)
        pass 
    
    xs = [list(el) for el in table_data['Distances']]
    ys = [list(el) for el in table_data['Elevations']]
    source_draw.data = dict(x=xs, y=ys)
    
    l1= plot.multi_line(xs='x', ys='y', source = source_draw, line_color='red', line_width=3)        
    c1 = plot.circle([], [], size=10, color='red')
    draw_tool_l1 = PolyDrawTool(renderers=[l1], vertex_renderer=c1)
    plot.add_tools(draw_tool_l1)
    
    edit_tool = PolyEditTool(renderers=[l1])
    plot.add_tools(edit_tool)
    
    # Define Draw Tool
    
    
    # Define Draw Tool
    table_data2 = {'ID':[],'Distances': [], 'Elevations': []}#, 'Type': []}
    #hdf_pt_file=f"{data_dir}/{label}_points.hdf"    
    #try:                
    #df = pd.read_hdf(hdf_pt_file,'points')
    #df['Distances'] = df['Distances'].apply(literal_eval)
    #df['Elevations'] = df['Elevations'].apply(literal_eval)
    table_data2['ID']=track_df.layer_id.values
    table_data2['Distances']=pt_distances
    table_data2['Elevations']=subsurf_elevs
    #table_data2['Type']=df['Type'].values
    print('PT_TABLE',table_data2)
    print(df)
    #except Exception as e:        
    #    print(e)
    #    pass 
    # Define Draw Tool
    
    
    pxs = table_data2['Distances']
    pys = table_data2['Elevations']
    source_point_draw.data = dict(x=pxs, y=pys)

    p1= plot.scatter(x='x', y='y', source = source_point_draw, color='darkgreen',  size=10)          
    draw_tool_p1 = PointDrawTool(renderers=[p1])
    plot.add_tools(draw_tool_p1)
    
    source_table.data = table_data
    source_table2.data = table_data2  
    source_subs.data = dict(x=pt_distances, y=subsurf_elevs)
    
    line_labels = LabelSet(x='Distances', y='Elevations', text='Lengths', text_font_size="30pt", level='glyph',
              x_offset=10, y_offset=10, source=source_table)
    #pt_labels = LabelSet(x='Distances', y='Elevations', text='Type', text_font_size="30pt", level='glyph',
    #          x_offset=10, y_offset=10, source=source_pt_table)

    citation = Label(x=100, y=100, x_units='screen', y_units='screen',
                 text='Nodjoumi et al., 2023',
                 border_line_color='black', border_line_alpha=1.0,
                 background_fill_color='white', background_fill_alpha=1.0)
    
    #plot.add_layout(pt_labels)
    # Set default or use the previous range values
    x_start, x_end = global_slider_range

    # Create the RangeSlider with global values
    x_range_slider = RangeSlider(start=0, end=transformed_geom.length//1000, value=(x_start, x_end), step=1, title="X-Axis Range")

    plot.x_range.start = x_start
    plot.x_range.end = x_end

    # Callback function to update plot x-axis range
    def update_range(attr, old, new):
        plot.x_range.start = new[0]  # Min value
        plot.x_range.end = new[1]    # Max value
        global global_slider_range   # Declare the global variable
        global_slider_range = (new[0], new[1])
    
    # Attach the callback to the slider
    x_range_slider.on_change('value', update_range)
    plot.add_layout(line_labels)
    layout.children[0].children[1] = plot
    layout.children[0].children[0].children[5] = x_range_slider 
    


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

#kmx, elevation_data,subsurface_twts,joined_gdf1 = profiler(src_df, mesh_gdf1, label, final_gdf)
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
pt_distances, dem_distances, elevation_data = [], [], []

source_dem = ColumnDataSource(data={'x': dem_distances, 'y': elevation_data})
subsurf_elevs = []
source_subs = ColumnDataSource(data={'x': pt_distances, 'y': subsurf_elevs})

# Create Plots
dem_profile = plot.line(x='x', y='y', source=source_dem, line_width=2,line_color='dodgerblue')
dem_points = plot.circle(x='x', y='y', source=source_dem, color='dodgerblue',size=3)
subs = plot.circle(x='x', y='y', source=source_subs, size=5, color='blue')

# Define Hover

hover = HoverTool(renderers=[dem_profile], tooltips=[("Elevation", "@y{0.000}"), ("Distance (km)", "@x{0.00}")])
hover2 = HoverTool(renderers=[subs], tooltips=[("Elevation", "@y{0.000}"), ("Distance (km)", "@x{0.00}")])
plot.add_tools(hover,hover2)

# Define LINE DRAW Tool

table_data = {'ID':[],'Distances': [], 'Elevations': [], 'Lengths': []}
hdf_file=f"{data_dir}/{label}_profiles.hdf"
try:        
    df = pd.read_hdf(hdf_file,'profiles')
    #table_data=df.to_json()
    df['Distances'] = df['Distances'].apply(literal_eval)
    df['Elevations'] = df['Elevations'].apply(literal_eval)
    print('FILE FOUND')
    print(table_data)
except Exception as e:    
    print(e)
    pass    

xs = [table_data['Distances']]
ys = [table_data['Elevations']]

source_draw = ColumnDataSource(data=dict(x=xs, y=ys))
l1= plot.multi_line(xs='x', ys='y', source = source_draw, line_color='red', line_width=3)        
c1 = plot.circle([], [], size=10, color='red')
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

hdf_pt_file=f"{data_dir}/{label}_points.hdf"
try:        
    df = pd.read_hdf(hdf_pt_file, 'points')
    df['Distances'] = df['Distances']
    df['Elevations'] = df['Elevations']
    #table_data=df.to_json()
    print('FILE FOUND')
    print(table_data)
except Exception as e:
    
    print(e)
    pass   

# Define Draw Tool
pxs = []
pys = []
source_point_draw = ColumnDataSource(data=dict(x=pxs, y=pys))

p1= plot.circle(x='x', y='y', source = source_point_draw, color='darkgreen',  size=20)    
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
select_eps = Slider(start=1, end=20, value=3, step=1, title="Permittivity")



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


global_slider_range = (0, 1)  
x_start, x_end = global_slider_range

# Create the RangeSlider with global values
x_range_slider = RangeSlider(start=x_start, end=x_end, value=(x_start, x_end), step=1, title="X-Axis Range")


# Callback function to update plot x-axis range
def update_range(attr, old, new):
    plot.x_range.start = new[0]  # Min value
    plot.x_range.end = new[1]    # Max value
    global global_slider_range   # Declare the global variable
    global_slider_range = (new[0], new[1])


freq_select.on_change('value', update_plot)

# Create layout
layout = row(column(row(select_label,select_eps,save_button,export_button,export_button_svg,x_range_slider),plot), column(row(download_button), row((column(title_line, data_table, title_points,data_table2)),column(title_bestfit,data_s2_table,data_s3_table))))


# Add layout to the current document
#curdoc().theme = 'dark_minimal'
curdoc().title = "EchoTerraeTrace-Profiler: MARSIS"  
curdoc().add_root(layout)