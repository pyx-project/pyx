#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2005-2011 André Wobst <wobsta@pyx-project.org>
#
# dvitype is free software; you can redistribute it and/or modify
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
from pyx import version
from pyx.dvi import dvifile

parser = OptionParser(usage="usage: %prog dvi-file",
                      version="%prog " + version.version)
(options, args) = parser.parse_args()
if len(args) != 1:
    parser.error("can process a single dvi-file only")

df = dvifile.DVIfile(args[0], debug=True)
while df.readpage():
    pass
