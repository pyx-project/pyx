# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2002-2005 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002-2006 André Wobst <wobsta@users.sourceforge.net>
# Copyright (C) 2006 Michael Schindler <m-schindler@users.sourceforge.net>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

"""Python graphics package

PyX is a Python package for the creation of PostScript and PDF files. It
combines an abstraction of the PostScript drawing model with a TeX/LaTeX
interface. Complex tasks like 2d and 3d plots in publication-ready quality are
built out of these primitives.
"""

from . import version
__version__ = version.version

__all__ = ["attr", "box", "bitmap", "canvas", "color", "connector", "deco", "deformer", "document",
           "epsfile", "graph", "mesh", "metapost", "path", "pattern", "pdfextra", "style", "trafo", "text", "unit"]

import importlib

# automatically import main modules into pyx namespace
for module in __all__:
    importlib.import_module('.' + module, package='pyx')

def pyxinfo(show_files=True, show_executes=True):
    import os, sys
    from . import config
    print("--- PyX info", "-"*37)
    print("Platform name is:", os.name)
    print("Python executable:", sys.executable)
    print("Python version:", sys.version)
    print("PyX comes from:", __file__)
    print("PyX version:", __version__)
    print("pyxrc", "is" if os.path.isfile(config.user_pyxrc) else "would be" ,"loaded from:", config.user_pyxrc)
    print("pykpathsea:", "available" if config.has_pykpathsea else "not available")
    print("file locators in use:", ", ".join(method.__class__.__name__ for method in config.methods))
    print("show files:", show_files)
    print("show executes:", show_executes)
    print("-"*50)
    config.show_files = show_files
    config.show_executes = show_executes

__all__.append("__version__")
__all__.append("pyxinfo")
