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

class _resource:

    """ a generic resource as needed by some canvas item """

    def __init__(self, type, id):
        self.type = type
        self.id = id

    def merge(self, other):
        """ merge other to self by modifying self

        since type and id of other are identical to self, we usually
        do not need to modify self at all"""
        pass


class definition(_resource):

    """ a definition """

    def __init__(self, id, body):
        _resource.__init__(self, "definition", id)
        self.body = body


class type1font(_resource):

    """ a type1 font (*.pfb file) """

    def __init__(self, id, fontfile, usedchars, encodingfile):
        _resource.__init__(self, "type1font", id)
        self.fontfile = fontfile
        self.usedchars = usedchars
        self.encodingfile = encodingfile

    def merge(self, other):
        # TODO: As far as I understand, the following is a totally unnecessary
        # restriction. We should, in the future, translate "usedchars" to glyph
        # names and merge those. The font stripping should work on the glyph
        # names. A type1font should not even know which reencoding are applied
        # to it later on. And it should be possible to reencode a font with
        # different encodings. However, for the moment it works ...
        assert self.encodingfile == other.encodingfile, "different encoding not supported"
        for i in range(len(self.usedchars)):
            self.usedchars[i] = self.usedchars[i] or other.usedchars[i]


class fontencoding(_resource):

    """ a encoding vector (*.enc file) """

    def __init__(self, id, encoding, encodingfile):
        _resource.__init__(self, "encoding", id)
        self.encoding = encoding
        self.encodingfile = encodingfile


class fontreencoding(_resource):

    """ a reencoded font """

    def __init__(self, id, psname, basepsname, encoding):
        _resource.__init__(self, "reencoding", id)
        self.psname = psname
        self.basepsname = basepsname
        self.encoding = encoding


class resourceregistry:

    """ storage class for resources """

    def __init__(self):
        self.resources = {}

    def registerresource(self, resource):
        """registers resource and merge it with possibly already existing ones"""
        resourcesoftype = self.resources.setdefault(resource.type, {})
        if resourcesoftype.has_key(resource.id):
             resourcesoftype[resource.id].merge(resource)
        else:
             resourcesoftype[resource.id] = resource

