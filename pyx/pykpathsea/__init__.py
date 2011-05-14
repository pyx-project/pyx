# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2003-2004 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2004 André Wobst <wobsta@users.sourceforge.net>
# Copyright (C) 2010 Michael Schinler <m-schindler@users.sourceforge.net>
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


try:
    from _pykpathsea import find_file
except ImportError:
    def find_file(*args):
        raise NotImplemented
