#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2005 André Wobst <wobsta@users.sourceforge.net>
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
from pyx import dvifile, document, version

parser = OptionParser(usage="usage: %prog -o output-file [-p paperformat] dvi-file", version="%prog " + version.version)
parser.add_option("-o", "--output", type="string", dest="output", help="output-file")
parser.add_option("-p", "--paperformat", type="string", dest="paperformat", default="A4", help="paper format string (default A4)")
(options, args) = parser.parse_args()
if len(args) != 1:
    parser.error("can process a single dvi-file only")

df = dvifile.dvifile(args[0], dvifile.readfontmap(["psfonts.map"]))
d = document.document()
while 1:
    c = df.readpage()
    if not c:
        break
    p = document.page(c, paperformat=getattr(document.paperformat, options.paperformat))
    d.append(p)
d.writetofile(options.output, pagebbox=0)
