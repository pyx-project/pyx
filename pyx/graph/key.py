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

    def __init__(self, dist=0.2*unit.v_cm, pos="tr", hinside=1, vinside=1, hdist=0.6*unit.v_cm, vdist=0.4*unit.v_cm,
                 symbolwidth=0.5*unit.v_cm, symbolheight=0.25*unit.v_cm, symbolspace=0.2*unit.v_cm,
                 textattrs=[]):
        self.dist = dist
        self.pos = pos
        self.hinside = hinside
        self.vinside = vinside
        self.hdist = hdist
        self.vdist = vdist
        self.symbolwidth = symbolwidth
        self.symbolheight = symbolheight
        self.symbolspace = symbolspace
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
        plotdata = [plotdat for plotdat in plotdata if plotdat.title is not None]
        c = canvas.canvas()
        self.dist_pt = unit.topt(self.dist)
        self.hdist_pt = unit.topt(self.hdist)
        self.vdist_pt = unit.topt(self.vdist)
        self.symbolwidth_pt = unit.topt(self.symbolwidth)
        self.symbolheight_pt = unit.topt(self.symbolheight)
        self.symbolspace_pt = unit.topt(self.symbolspace)
        for plotdat in plotdata:
            plotdat.temp_titlebox = c.texrunner.text_pt(0, 0, plotdat.title, self.defaulttextattrs + self.textattrs)
        box.tile_pt([plotdat.temp_titlebox for plotdat in plotdata], self.dist_pt, 0, -1)
        box.linealignequal_pt([plotdat.temp_titlebox for plotdat in plotdata], self.symbolwidth_pt + self.symbolspace_pt, 1, 0)
        for plotdat in plotdata:
            plotdat.style.key_pt(c, 0, -0.5 * self.symbolheight_pt + plotdat.temp_titlebox.center[1],
                                 self.symbolwidth_pt, self.symbolheight_pt, plotdat)
            c.insert(plotdat.temp_titlebox)

        # for plotdat in plotdata:
        #     del plotdat.temp_titlebox
        return c
