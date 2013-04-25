#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Ourbunny
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# necessary because of how onefile and pyinstaller works
# http://www.pyinstaller.org/export/v2.0/project/doc/Manual.html#accessing-data-files

import os
import sys

def getpath(name=None):
    if getattr(sys, '_MEIPASS', None):
        basedir = sys._MEIPASS
    else:
        #basedir = os.path.dirname(__file__)
        basedir = os.getcwd()
        
    if name is None:
        return basedir

    return os.path.join(basedir, name)