#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2003-2005 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2005 André Wobst <wobsta@users.sourceforge.net>
#
# This file is part of PyX (http://pyx.sourceforge.net/).
#
# PyX is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# PyX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyX; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""resource module:

This module contains various resources like fonts and definitions
needed by canvasitems and a resource registry class.

"""

import pswriter, pdfwriter

class _resource:

    """ a resource needed by a canvasitem """

    def __init__(self, id):
        self.id = id

    def PSregister(self, registry):
        return []


#
# various standard resources
#

class definition(_resource):

    """ function definition """

    def __init__(self, id, body):
        self.id = id
        self.body = body

    def PSregister(self, registry):
        pswriter.PSdefinition(self.id, self.body).register(registry)


class font(_resource):

    """ font definition """

    def __init__(self, font):
        """ include Type 1 font defined by the following parameters """
        # XXX passing the font instance is probably not so nice
        self.id = self.fontname = font.getpsname()
        self.basepsname = font.getbasepsname()
        self.fontfile = font.getfontfile()
        self.encodingfile = font.getencodingfile()
        self.encoding = font.getencoding()
        self.usedchars = font.usedchars
        self.font = font

    def PSregister(self, registry):
        if self.fontfile:
            registry.add(pswriter.PSfontfile(self.basepsname, self.fontfile, self.encodingfile, self.usedchars))
        if self.encoding:
            registry.add(pswriter._ReEncodeFont)
            registry.add(pswriter.PSfontencoding(self.encoding, self.encodingfile))
            registry.add(pswriter.PSfontreencoding(self.fontname, self.basepsname, self.encoding))

    def PDFregister(self, registry):
        pdfwriter.PDFfont(self.fontname, self.basepsname, self.font).register(registry)
