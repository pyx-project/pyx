#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2005 André Wobst <wobsta@users.sourceforge.net>
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

import array

def decoder(code, r, n):
    c1 = 52845
    c2 = 22719
    plain = array.array("B")
    for x in array.array("B", code):
        plain.append(x ^ (r >> 8))
        r = ((x + r) * c1 + c2) & 0xffff
    return plain.tostring()[n:]

def encoder(data, r, random):
    c1 = 52845
    c2 = 22719
    code = array.array("B")
    for x in array.array("B", random+data):
        code.append(x ^ (r>>8))
        r = ((code[-1] + r) * c1 + c2) & 0xffff;
    return code.tostring()
