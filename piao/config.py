#!/usr/bin/env python
#-*-coding: utf-8 -*-
import os

DATA_DIR = 'cache'

try:
    os.mkdir(DATA_DIR)
except OSError:
    pass
