import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output, State

###################################################
#               DATA LOADING/SETUP
###################################################
home = '/app/'
data_dir = '/home/hyradus/SyncThing/SyncData/SHARAD_PIT_DATA/Site_4/SHARAD/'
original_h5 = 'subsurface_layers.h5'
updated_h5 = 'subsurface_layers_updated.h5'
autopicked_f1 = 'subsurface_layers.h5'  # For naming .gpkg

try:
    global_df = pd.read_hdf(os.path.join(data_dir, updated_h5))
    print("Loaded updated HDF.")
except FileNotFoundError:
    global_df = pd.read_hdf(os.path.join(data_dir, original_h5))
    print("Loaded original HDF.")

###################################################
#        DASH APP INITIALIZATION
###################################################
app = Dash(__name__)
app.title = "3D Interactive Dashboard (Per-User Isolation)"

###################################################
#   HELPER: BUILD MARKS FOR RANGE SLIDERS
###################################################
def build_marks(start, end, interval=0.5):
    vals = np.arange(start, end + 0.0001, interval)
    return {round(v,2): str(round(v,2)) for v in vals}

###################################################
#   HELPER: CREATE 3D FIGURE
###################################################
def create_3d_figure(df, x_range=None, y_range=None, z_range=None, aspectratio=None):
    """
    Returns a combined 3D figure with:
      - Red lines: surf_twts
      - Green lines: pt_twts
    Z-axis reversed, fewer ticks, and uirevision='constant' 
    for persistent camera.
    """
    fig_surf = px.line_3d(
        df, x="pt_lons", y="pt_lats", z="surf_twts",
        color="track_num",
        line_group="layer_id",
        color_discrete_sequence=["red"]
    )
    fig_pt = px.line_3d(
        df, x="pt_lons", y="pt_lats", z="pt_twts",
        color="track_num",
        line_group="layer_id",
        color_discrete_sequence=["green"]
    )

    fig = go.Figure(data=fig_surf.data + fig_pt.data)
    fig.update_traces(line=dict(width=5))

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=x_range, nticks=5),
            yaxis=dict(range=y_range, nticks=5),
            zaxis=dict(range=z_range, nticks=5, autorange="reversed"),
            aspectratio=aspectratio
        ),
        height=700,
        uirevision="constant"
    )
    return fig

###################################################
#    CONVERT DF <--> JSON FOR dcc.Store
###################################################
def df_to_json(df):
    return df.to_json(date_format='iso', orient='split')

def df_from_json(json_str):
    return pd.read_json(json_str, orient='split')

###################################################
#   DEFINE SLIDER RANGES & MARKS (FROM global_df)
###################################################
xmin, xmax = global_df['pt_lons'].min(), global_df['pt_lons'].max()
ymin, ymax = global_df['pt_lats'].min(), global_df['pt_lats'].max()
zmin, zmax = global_df['surf_twts'].min(), global_df['surf_twts'].max()

x_marks = build_marks(xmin, xmax, 0.5)
y_marks = build_marks(ymin, ymax, 0.5)
z_marks = build_marks(zmin, zmax, 0.5)

###################################################
#   DASH LAYOUT: dcc.Store + UI
###################################################
app.layout = html.Div([
    html.H2("3D Interactive Dashboard (Per-User Isolation)"),
    
    # 1) Hidden store to keep each user's DataFrame
    dcc.Store(id='df-store', storage_type='session'),

    # Row 1: Track # dropdown, slider, text input, Save button
    html.Div([
        html.Div([
            html.Label("Select Track Number"),
            dcc.Dropdown(
                id='track-num-select',
                clearable=False
            )
        ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        
        html.Div([
            html.Label("Modify pt_twts"),
            dcc.Slider(
                id='pt-twts-slider',
                min=-5, max=5, step=0.25, value=0,
                marks={i: str(i) for i in range(-5, 6)}
            )
        ], style={'width': '25%', 'display': 'inline-block', 'padding': '0 20px'}),

        html.Div([
            html.Label("Set Modifier Manually"),
            dcc.Input(
                id='pt-twts-input',
                type='text',
                value='0',
                style={'width': '60px'}
            )
        ], style={'width': '15%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        
        html.Div([
            html.Button("Save Data", id='save-button', n_clicks=0)
        ], style={'width': '10%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        
    ], style={'padding': '10px 0'}),

    # Row 2: X/Y/Z axis range sliders
    html.Div([
        html.Div([
            html.Label("X-Axis Scale"),
            dcc.RangeSlider(
                id='x-axis-range',
                min=xmin,
                max=xmax,
                step=0.1,
                value=[xmin, xmax],
                marks=x_marks
            )
        ], style={'width': '30%', 'display': 'inline-block'}),
        
        html.Div([
            html.Label("Y-Axis Scale"),
            dcc.RangeSlider(
                id='y-axis-range',
                min=ymin,
                max=ymax,
                step=0.1,
                value=[ymin, ymax],
                marks=y_marks
            )
        ], style={'width': '30%', 'display': 'inline-block'}),
        
        html.Div([
            html.Label("Z-Axis Scale"),
            dcc.RangeSlider(
                id='z-axis-range',
                min=zmin,
                max=zmax,
                step=0.1,
                value=[zmin, zmax],
                marks=z_marks
            )
        ], style={'width': '30%', 'display': 'inline-block'}),
        
    ], style={'padding': '10px 0'}),

    # Row 3: Aspect ratio sliders
    html.Div([
        html.Div([
            html.Label("Aspect Ratio X"),
            dcc.Slider(
                id='aspect-x',
                min=1, max=10, step=0.1,
                value=5,
                marks={i: str(i) for i in range(1, 11)}
            )
        ], style={'width': '30%', 'display': 'inline-block'}),
        
        html.Div([
            html.Label("Aspect Ratio Y"),
            dcc.Slider(
                id='aspect-y',
                min=1, max=10, step=0.1,
                value=5,
                marks={i: str(i) for i in range(1, 11)}
            )
        ], style={'width': '30%', 'display': 'inline-block'}),
        
        html.Div([
            html.Label("Aspect Ratio Z"),
            dcc.Slider(
                id='aspect-z',
                min=0.1, max=5, step=0.1,
                value=0.5,
                marks={round(i,2): str(round(i,2)) for i in [0.1,1,2,3,4,5]}
            )
        ], style={'width': '30%', 'display': 'inline-block'}),
        
    ], style={'padding': '10px 0'}),

    html.Div(id='save-output', style={'color': 'green', 'padding': '10px 0'}),

    dcc.Graph(id='plot-3d')
])

###################################################
# CALLBACK #1: Sync text input & slider
###################################################
@app.callback(
    Output('pt-twts-slider', 'value'),
    Input('pt-twts-input', 'value'),
    State('pt-twts-slider', 'value')
)
def sync_text_to_slider(text_val, slider_val):
    """
    If user enters a valid float, override slider.
    """
    try:
        val = float(text_val)
        return val
    except (ValueError, TypeError):
        return slider_val

###################################################
# CALLBACK #2: Initialize & Update figure/store
###################################################
@app.callback(
    Output('df-store', 'data'),               # updated JSON data
    Output('track-num-select', 'options'),    # updated dropdown options
    Output('plot-3d', 'figure'),              # updated figure
    Input('df-store', 'data'),                # triggers on page load if None
    Input('track-num-select', 'value'),
    Input('pt-twts-slider', 'value'),
    Input('x-axis-range', 'value'),
    Input('y-axis-range', 'value'),
    Input('z-axis-range', 'value'),
    Input('aspect-x', 'value'),
    Input('aspect-y', 'value'),
    Input('aspect-z', 'value'),
    prevent_initial_call=True
)
def update_figure(json_df,
                  track_num,
                  modifier,
                  x_range, y_range, z_range,
                  asp_x, asp_y, asp_z):
    """
    Single callback that:
     1) Initializes df-store if None (first page load).
     2) Applies track_num & slider changes to the user's df.
     3) Builds the updated figure.
     4) Returns updated store + figure + track options.
    """
    # 1) If df-store is empty, load from global_df
    if json_df is None:
        df_local = global_df.copy()
    else:
        df_local = df_from_json(json_df)
    
    # 2) If we haven't chosen track_num yet, set a default
    #    (This ensures we don't error out if track_num is None)
    if track_num is None:
        track_num = df_local['track_num'].unique()[0]  # pick first

    # Apply modifications for the selected track
    df_local.loc[df_local['track_num'] == track_num, 'surf_twts'] += modifier
    df_local.loc[df_local['track_num'] == track_num, 'pt_twts']    += modifier
    df_local['twt2surf'] = df_local['pt_twts'] - df_local['surf_twts']

    # 3) Build the figure
    aspect_dict = dict(x=asp_x, y=asp_y, z=asp_z)
    fig = create_3d_figure(
        df_local,
        x_range=x_range,
        y_range=y_range,
        z_range=z_range,
        aspectratio=aspect_dict
    )

    # Build track-num dropdown options
    track_options = [{'label': str(t), 'value': t} for t in df_local['track_num'].unique()]

    # Convert updated df back to JSON
    updated_json = df_to_json(df_local)

    # Return new store, new track options, new figure
    return updated_json, track_options, fig

###################################################
# CALLBACK #3: Save data from user's store
###################################################
@app.callback(
    Output('save-output', 'children'),
    Input('save-button', 'n_clicks'),
    State('df-store', 'data'),
    prevent_initial_call=True
)
def save_data(n, json_df):
    if not json_df:
        return "No data to save."

    df_to_save = df_from_json(json_df)

    # Save to gpkg
    geometries = [Point(lon, lat) for lon, lat in zip(df_to_save['pt_lons'], df_to_save['pt_lats'])]
    gdf = gpd.GeoDataFrame(df_to_save, geometry=geometries, crs="EPSG:4326")
    gpkg_name = os.path.join(data_dir, f'{os.path.splitext(autopicked_f1)[0]}_updated.gpkg')
    gdf.to_file(gpkg_name, driver='GPKG')

    # Save to hdf
    hdf_name = os.path.join(data_dir, 'subsurface_layers_updated.h5')
    df_to_save.to_hdf(hdf_name, key='data', mode='w')

    return f"Data saved to: {gpkg_name} and {hdf_name}"

###################################################
# MAIN
###################################################
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
