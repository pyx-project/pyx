# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2003-2011 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2011 André Wobst <wobsta@users.sourceforge.net>
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

import ConfigParser, os.path, warnings
import filelocator

class _marker: pass

config = ConfigParser.ConfigParser()
config.readfp(filelocator.locator_classes["internal"]().openers("pyxrc", [], [""], "r")[0]())
config.read(os.path.expanduser("~/.pyxrc"))

def get(section, option, default=_marker):
    if default is _marker:
        return config.get(section, option)
    else:
        try:
            return config.get(section, option)
        except ConfigParser.Error:
            return default

def getint(section, option, default=_marker):
    if default is _marker:
        return config.getint(section, option)
    else:
        try:
            return config.getint(section, option)
        except ConfigParser.Error:
            return default

def getfloat(section, option, default=_marker):
    if default is _marker:
        return config.getfloat(section, option)
    else:
        try:
            return config.getfloat(section, option)
        except ConfigParser.Error:
            return default

def getboolean(section, option, default=_marker):
    if default is _marker:
        return config.getboolean(section, option)
    else:
        try:
            return config.getboolean(section, option)
        except ConfigParser.Error:
            return default

def getlist(section, option, default=_marker):
    if default is _marker:
        l = config.get(section, option).split()
    else:
        try:
            l = config.get(section, option).split()
        except ConfigParser.Error:
            return default
    if space:
        l = [item.replace(space, ' ') for item in l]
    return l


space = get("general", "space", None)
formatWarnings = get("general", "warnings", "default")
if formatWarnings not in ["default", "short", "shortest"]:
    raise RuntimeError("invalid config value for option 'warnings' in section 'general'")
if formatWarnings != "default":
    def formatwarning(message, category, filename, lineno, line=None):
        if formatWarnings == "short":
            return "%s:%s: %s: %s\n" % (filename, lineno, category.__name__, message)
        else:
            return "%s\n" % message
    warnings.formatwarning = formatwarning

filelocator.init()
