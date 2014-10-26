#!/usr/bin/env python

#    Copyright (C) 2014  Club Capra - capra.etsmtl.ca
#
#    This file is part of CapraVision.
#    
#    CapraVision is free software: you can redistribute it and/or modify
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

"""
Description : Start web server 
Authors: Benoit Paquet
Date : October 2014
"""

from flask import Flask, render_template, Response
from PIL import Image

from CapraVision.server.core.manager import VisionManager
from CapraVision.server import imageproviders
import CapraVision.server.filters.implementation

import StringIO
import threading

class FlaskServer:
    
    def __init__(self):
        self.image = None
        self.evt = threading.Event()

    def send(self, filtre, output):
        if "Resize" not in str(filtre):
            return
        if output is None:
            return
        bgr2rgb = CapraVision.server.filters.implementation.BGR2RGB()
        output = bgr2rgb.execute(output)
        img = Image.fromarray(output)
        buff = StringIO.StringIO()
        img.save(buff, 'bmp')
        contents = buff.getvalue()
        buff.close()
        self.image = contents
        self.evt.set()
    
    def gen(self):
        while True:
            self.evt.clear()
            self.evt.wait()
            yield (b'--frame\r\n'
                   b'Content-Type: image/bmp\r\n\r\n' + self.image + b'\r\n')
    
web = FlaskServer()
app = Flask(__name__)

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(web.gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

def run():

    # Directly connected to the vision server
    c = VisionManager()
    
    assert c.load_chain('<new>')
    
    #source
    sources = imageproviders.load_sources()

    c.change_source(sources["Movie"])
    c.source.open_video_file("/home/benoit/test.avi") 
    c.add_image_observer(web.send)
    c.source.play()
    assert c.is_thread_running()

    app.run(debug=True)
     

