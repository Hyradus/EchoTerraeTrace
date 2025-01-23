#!/bin/bash
bokeh serve ett_marsis.py --allow-websocket-origin=* --port=5006 &
bokeh serve ett_sharad.py --allow-websocket-origin=* --port=5008 &
bokeh serve ett_profiler_marsis.py --allow-websocket-origin=* --port=5007 &
bokeh serve ett_profiler_sharad.py --allow-websocket-origin=* --port=5009 &
jupyter lab --no-browser --ip=0.0.0.0 --allow-root --notebook-dir=/Notebooks &
gunicorn "dash_app:server" --bind 0.0.0.0:8050 --workers 12      

