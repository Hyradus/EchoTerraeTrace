#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: giacomo.nodjoumi@hyranet.info - g.nodjoumi@jacobs-university.de
"""

from bokeh.models import CustomJSTickFormatter
import holoviews as hv
from holoviews.operation.timeseries import rolling
import numpy as np

def create_formatter(code):
    return CustomJSTickFormatter(code=code)

def Formatters(geom_length, max_width):
    xFormatter = create_formatter(f'''
        var space = ' ';
        return (Math.round(tick * {geom_length / max_width})).toFixed(1) + space + 'Km';
    ''')
    yFormatter = create_formatter('''
        var space = ' ';
        return (tick * 0.0375).toFixed(2);
    ''')
    yFormatterM = create_formatter('''
        var space = ' ';
        return (tick * 0.7143).toFixed(2);
    ''')
    return xFormatter, yFormatter, yFormatterM
