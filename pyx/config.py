#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2003 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003 André Wobst <wobsta@users.sourceforge.net>
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

import ConfigParser
import os.path

cflist = ["/etc/pyxrc",  os.path.expanduser("~/.pyxrc")]

config = ConfigParser.ConfigParser()
config.read(cflist)

def configgetdefault(section, option, default):
    if config.has_option(section, option):
        return config.get(section, option)
    else:
        return default

class fonts:
    fontmaps = configgetdefault("fonts", "fontmaps", "psfonts.map").split()

