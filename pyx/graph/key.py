#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2002-2004 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2003-2004 Michael Schindler <m-schindler@users.sourceforge.net>
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


from pyx import box, canvas, text, unit


class key:

    defaulttextattrs = [text.vshift.mathaxis]

    def __init__(self, dist="0.2 cm", pos="tr", hinside=1, vinside=1, hdist="0.6 cm", vdist="0.4 cm",
                 symbolwidth="0.5 cm", symbolheight="0.25 cm", symbolspace="0.2 cm",
                 textattrs=[]):
        self.dist_str = dist
        self.pos = pos
        self.hinside = hinside
        self.vinside = vinside
        self.hdist_str = hdist
        self.vdist_str = vdist
        self.symbolwidth_str = symbolwidth
        self.symbolheight_str = symbolheight
        self.symbolspace_str = symbolspace
        self.textattrs = textattrs
        if self.pos in ("tr", "rt"):
            self.right = 1
            self.top = 1
        elif self.pos in ("br", "rb"):
            self.right = 1
            self.top = 0
        elif self.pos in ("tl", "lt"):
            self.right = 0
            self.top = 1
        elif self.pos in ("bl", "lb"):
            self.right = 0
            self.top = 0
        else:
            raise RuntimeError("invalid pos attribute")

    def paint(self, plotdata):
        "creates the layout of the key"
        c = canvas.canvas()
        self.dist_pt = unit.topt(unit.length(self.dist_str, default_type="v"))
        self.hdist_pt = unit.topt(unit.length(self.hdist_str, default_type="v"))
        self.vdist_pt = unit.topt(unit.length(self.vdist_str, default_type="v"))
        self.symbolwidth_pt = unit.topt(unit.length(self.symbolwidth_str, default_type="v"))
        self.symbolheight_pt = unit.topt(unit.length(self.symbolheight_str, default_type="v"))
        self.symbolspace_pt = unit.topt(unit.length(self.symbolspace_str, default_type="v"))
        titles = []
        for plotdat in plotdata:
            titles.append(c.texrunner.text_pt(0, 0, plotdat.title, self.defaulttextattrs + self.textattrs))
        box.tile_pt(titles, self.dist_pt, 0, -1)
        box.linealignequal_pt(titles, self.symbolwidth_pt + self.symbolspace_pt, 1, 0)
        for plotdat, title in zip(plotdata, titles):
            plotdat.style.key_pt(c, 0, -0.5 * self.symbolheight_pt + title.center[1],
                                   self.symbolwidth_pt, self.symbolheight_pt, plotdat)
            c.insert(title)
        return c
