#!/usr/bin/env python
#
#
# Copyright (C) 2002 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2002 André Wobst <wobsta@users.sourceforge.net>
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

import unittest
from pyx import *

class UnitTestCase(unittest.TestCase):
    def testTrueUnits(self):
        assert unit.topt(unit.t_pt(42)) == 42, "wrong unit definition"
        assert unit.tom(unit.t_m(42)) == 42, "wrong unit definition"

    def testUserUnits(self):
        unit.set(uscale=2)
        assert unit.topt(unit.pt(42)) == 84, "wrong unit definition"
        assert unit.tom(unit.m(42)) == 84, "wrong unit definition"
        unit.set(uscale=1)
