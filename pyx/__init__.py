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

""" PyX := PostScript + Python + TeX

PyX is a python package for the creation of encapsulated PostScript
figures. It provides both an abstraction of PostScript and a TeX/LaTeX
interface. Complex tasks like 2d plots in publication-ready quality
are build out of these primitives.

"""

import version
__version__ = version.version

__all__ = ["attr", "box", "bitmap", "canvas", "color", "connector", "deco", "deformer", "epsfile", "graph", "path",
           "style", "trafo", "text", "unit"]


# automatically import main modules into pyx namespace
for module in __all__:
    __import__(module, globals(), locals(), [])

