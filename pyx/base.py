#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002-2004 André Wobst <wobsta@users.sourceforge.net>
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

#
# Postscript operators
#

__metaclass__ = type

class canvasitem:

    """Base class for everything which can be inserted into a canvas"""

    def outputPS(self, file):
        """write PS code corresponding to canvasitem to file"""
        pass

    def outputPDF(self, file):
        """write PDF code corresponding to canvasitem to file"""
        pass

    def prolog(self):
        """return list of prolog items required by canvasitem"""
        return []

    def bbox(self):
        """return bounding box of canvasitem or None"""
        pass


#
# PyX Exception class
#

class PyXExcept(Exception):

    """base class for all PyX Exceptions"""

    pass
