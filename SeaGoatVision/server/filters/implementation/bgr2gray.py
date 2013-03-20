#! /usr/bin/env python

#    Copyright (C) 2012  Club Capra - capra.etsmtl.ca
#
#    This file is part of SeaGoatVision.
#
#    SeaGoatVision is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cv2
import cv2.cv as cv
from SeaGoatVision.server.core.filter import Filter

class BGR2Grayscale(Filter):
    """Convert to grayscale then convert back to BGR"""
    def __init__(self):
        Filter.__init__(self)

    def execute(self, image):
        cv2.cvtColor(image, cv.CV_BGR2GRAY, image)
        cv2.cvtColor(image, cv.CV_GRAY2BGR, image)
        return image