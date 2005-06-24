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

class resource:

    """ a resource needed by a canvasitem """

    def PSregister(self, registry):
        """ register PSresources in registry """
        pass


#
# various standard resources
#

class definition(resource):

    """ function definition """

    def __init__(self, id, body):
        self.id = id
        self.body = body

    def PSregister(self, registry):
        registry.add(pswriter.PSdefinition(self.id, self.body))


class font(resource):

    """ font definition """

    def __init__(self, font):
        """ include Type 1 font defined by the following parameters """
        self.font = font

    def PSregister(self, registry):
        pswriter.PSfont(self.font, registry)
