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

import pswriter

class resource:

    """ a resource needed by a canvasitem """

    def __init__(self):
        self.id = None

    def __str__(self):
        return "resource(%s)" % self.id

    def merge(self, other):
        """ merge contents of similar resource with self """
        assert self.id == other.id, "Cannot merge resources with different ids"

    def PSprolog(self):
        """ return list of PS prolog items needed for resource """
        return []


#
# various standard resources
#

class definition(resource):

    """ function definition """

    def __init__(self, id, body):
        self.id = id
        self.body = body

    def merge(self, other):
        assert self.id == other.id, "Cannot merge resources with different ids"
        if self.body != other.body:
            raise ValueError("Conflicting function definitions!")

    def PSprolog(self):
        return [pswriter.PSdefinition(self.id, self.body)]


class font(resource):

    """ font definition """

    def __init__(self, font):
        """ include Type 1 font defined by the following parameters """
        # XXX passing the font instance is probably not so nice
        self.id = self.fontname = font.getpsname()
        self.basepsname = font.getbasepsname()
        self.fontfile = font.getfontfile()
        self.encodingfile = font.getencodingfile()
        self.encoding = font.getencoding()
        self.usedchars = font.usedchars

    def merge(self, other):
        assert self.id == other.id, "Cannot merge resources with different ids"
        assert self.fontname == other.fontname and self.encoding == other.encoding, "font and/or encoding do not match"
        for i in range(len(self.usedchars)):
            self.usedchars[i] = self.usedchars[i] or other.usedchars[i]

    def PSprolog(self):
        # XXX maybe we should move this into pswriter.py
        result = [pswriter.PSfontfile(None,
                                      self.basepsname,
                                      self.fontfile,
                                      self.encodingfile,
                                      self.usedchars)]
        if self.encoding:
            result.append(pswriter._ReEncodeFont)
            result.append(pswriter.PSfontencoding(self.encoding, self.encodingfile))
            result.append(pswriter.PSfontreencoding(self.fontname, self.basepsname, self.encoding))
        return result


class resourceregistry:

    """ storage class for resources """

    def __init__(self):
        self.resources = {}

    def registerresource(self, resource):
        """registers resource and merge it with possibly already existing ones"""
        resourceid = resource.id
        if self.resources.has_key(resourceid):
             self.resources[resourceid].merge(resource)
        else:
             self.resources[resourceid] = resource

    def queryresource(self, resourceid):
        return self.resources[resourceid]
