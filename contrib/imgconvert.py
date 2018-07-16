#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2005 André Wobst <wobsta@pyx-project.org>
#
# epstopng is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# epstopng is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with epstopng; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from optparse import OptionParser
from pyx import *
from pyx import version

parser = OptionParser(usage="usage: %prog -o output-file [-r resolution] image-file",
                      version="%prog " + version.version)
parser.add_option("-o", "--output",
                  type="string", dest="output",
                  help="output-file")
parser.add_option("-r", "--resolution",
                  type="string", dest="resolution", default=None,
                  help="resolution of the image in dpi (optional when available in the image data)")
(options, args) = parser.parse_args()
if len(args) != 1:
    parser.error("can process a single image-file only")

try:
    im = bitmap.jpegimage(args[0])
except ValueError:
    from PIL import Image
    im = Image.open(args[0])
    compressmode = "Flate"
else:
    compressmode = None
if options.resolution is None:
    width = None
else:
    width = im.size[0] / float(options.resolution) * unit.inch
c = canvas.canvas()
c.insert(bitmap.bitmap(0, 0, im, compressmode=compressmode, width=width))
c.writetofile(options.output)
