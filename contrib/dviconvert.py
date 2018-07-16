#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2005-2011 André Wobst <wobsta@pyx-project.org>
#
# dviconvert is free software; you can redistribute it and/or modify
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
from pyx import bbox, version
from pyx.dvi import dvifile

parser = OptionParser(usage="usage: %prog [-b] [-p paperformat] -o output-file dvi-file",
                      version="%prog " + version.version)
parser.add_option("-o", "--output",
                  type="string", dest="output",
                  help="output-file")
parser.add_option("-p", "--paperformat",
                  type="string", dest="paperformat", default=None,
                  help="optional paper format string")
parser.add_option("-b", "--writebbox",
                  action="store_true", dest="writebbox", default=0,
                  help="Add bouding box information on PS and PDF when a paperformat is defined")
(options, args) = parser.parse_args()
if len(args) != 1:
    parser.error("can process a single dvi-file only")

if options.paperformat:
    options.paperformat = getattr(document.paperformat, options.paperformat)
df = dvifile.DVIfile(args[0])
d = document.document()
while 1:
    dvipage = df.readpage()
    if not dvipage:
        break
    if options.paperformat:
        aligntrafo = trafo.translate(unit.t_inch, -unit.t_inch + options.paperformat.height)
        aligneddvipage = canvas.canvas([aligntrafo])
        aligneddvipage.insert(dvipage)
        p = document.page(aligneddvipage, paperformat=options.paperformat, centered=0)
    else:
        p = document.page(dvipage)
    d.append(p)
if options.writebbox:
    d.writetofile(options.output)
else:
    d.writetofile(options.output, writebbox=1)
