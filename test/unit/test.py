#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
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

import sys; sys.path[:0] = ["../..", ".."]

import unittest

from test_data import DataTestCase
from test_mathtree import MathTreeTestCase
from test_frac import FracTestCase
from test_part import LinPartTestCase, LogPartTestCase
from test_texter import TexterTestCase
from test_trafo import TrafoTestCase
from test_unit import UnitTestCase
from test_helper import AttrTestCase

# construct the test suite automagically

suite = unittest.TestSuite((unittest.makeSuite(DataTestCase, 'test'),
                            unittest.makeSuite(MathTreeTestCase, 'test'),
                            unittest.makeSuite(FracTestCase, 'test'),
                            unittest.makeSuite(LinPartTestCase, 'test'),
                            unittest.makeSuite(LogPartTestCase, 'test'),
                            unittest.makeSuite(TexterTestCase, 'test'),
                            unittest.makeSuite(UnitTestCase, 'test'),
                            unittest.makeSuite(AttrTestCase, 'test'),
                            unittest.makeSuite(TrafoTestCase, 'test'),
                          ))

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite)
