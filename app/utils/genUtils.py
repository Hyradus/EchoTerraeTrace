#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: giacomo.nodjoumi@hyranet.info
"""

import fnmatch
import os
import re

def get_paths(path, ext):
    ext_pattern = f"*{ext}"
    chk_case = re.compile(fnmatch.translate(ext_pattern), re.IGNORECASE)
    files = [os.path.join(path, f) for f in os.listdir(path) if chk_case.match(f)]
    return files