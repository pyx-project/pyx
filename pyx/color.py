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

import attr, style

class color(attr.exclusiveattr, style.strokestyle, style.fillstyle):

    """base class for all colors"""

    def __init__(self):
        attr.exclusiveattr.__init__(self, color)


clear = attr.clearclass(color)


class grey(color):

    """grey tones"""

    def __init__(self, gray):
        color.__init__(self)
        if gray<0 or gray>1: raise ValueError
        self.color = {"gray": gray}

    def write(self, file):
        file.write("%(gray)f setgray\n" % self.color)

grey.black = grey(0.0)
grey.white = grey(1.0)
gray = grey


class rgb(color):

    """rgb colors"""

    def __init__(self, r=0.0, g=0.0, b=0.0):
        color.__init__(self)
        if r<0 or r>1 or g<0 or g>1 or b<0 or b>1: raise ValueError
        self.color = {"r": r, "g": g, "b": b}

    def write(self, file):
        file.write("%(r)f %(g)f %(b)f setrgbcolor\n" % self.color)

rgb.red   = rgb(1 ,0, 0)
rgb.green = rgb(0 ,1, 0)
rgb.blue  = rgb(0 ,0, 1)
rgb.white = rgb(1 ,1, 1)
rgb.black = rgb(0 ,0, 0)


class hsb(color):

    """hsb colors"""

    def __init__(self, h=0.0, s=0.0, b=0.0):
        color.__init__(self)
        if h<0 or h>1 or s<0 or s>1 or b<0 or b>1: raise ValueError
        self.color = {"h": h, "s": s, "b": b}

    def write(self, file):
        file.write("%(h)f %(s)f %(b)f sethsbcolor\n" % self.color)


class cmyk(color):

    """cmyk colors"""

    def __init__(self, c=0.0, m=0.0, y=0.0, k=0.0):
        color.__init__(self)
        if c<0 or c>1 or m<0 or m>1 or y<0 or y>1 or k<0 or k>1: raise ValueError
        self.color = {"c": c, "m": m, "y": y, "k": k}

    def write(self, file):
        file.write("%(c)f %(m)f %(y)f %(k)f setcmykcolor\n" % self.color)


cmyk.GreenYellow    = cmyk(0.15, 0, 0.69, 0)
cmyk.Yellow         = cmyk(0, 0, 1, 0)
cmyk.Goldenrod      = cmyk(0, 0.10, 0.84, 0)
cmyk.Dandelion      = cmyk(0, 0.29, 0.84, 0)
cmyk.Apricot        = cmyk(0, 0.32, 0.52, 0)
cmyk.Peach          = cmyk(0, 0.50, 0.70, 0)
cmyk.Melon          = cmyk(0, 0.46, 0.50, 0)
cmyk.YellowOrange   = cmyk(0, 0.42, 1, 0)
cmyk.Orange         = cmyk(0, 0.61, 0.87, 0)
cmyk.BurntOrange    = cmyk(0, 0.51, 1, 0)
cmyk.Bittersweet    = cmyk(0, 0.75, 1, 0.24)
cmyk.RedOrange      = cmyk(0, 0.77, 0.87, 0)
cmyk.Mahogany       = cmyk(0, 0.85, 0.87, 0.35)
cmyk.Maroon         = cmyk(0, 0.87, 0.68, 0.32)
cmyk.BrickRed       = cmyk(0, 0.89, 0.94, 0.28)
cmyk.Red            = cmyk(0, 1, 1, 0)
cmyk.OrangeRed      = cmyk(0, 1, 0.50, 0)
cmyk.RubineRed      = cmyk(0, 1, 0.13, 0)
cmyk.WildStrawberry = cmyk(0, 0.96, 0.39, 0)
cmyk.Salmon         = cmyk(0, 0.53, 0.38, 0)
cmyk.CarnationPink  = cmyk(0, 0.63, 0, 0)
cmyk.Magenta        = cmyk(0, 1, 0, 0)
cmyk.VioletRed      = cmyk(0, 0.81, 0, 0)
cmyk.Rhodamine      = cmyk(0, 0.82, 0, 0)
cmyk.Mulberry       = cmyk(0.34, 0.90, 0, 0.02)
cmyk.RedViolet      = cmyk(0.07, 0.90, 0, 0.34)
cmyk.Fuchsia        = cmyk(0.47, 0.91, 0, 0.08)
cmyk.Lavender       = cmyk(0, 0.48, 0, 0)
cmyk.Thistle        = cmyk(0.12, 0.59, 0, 0)
cmyk.Orchid         = cmyk(0.32, 0.64, 0, 0)
cmyk.DarkOrchid     = cmyk(0.40, 0.80, 0.20, 0)
cmyk.Purple         = cmyk(0.45, 0.86, 0, 0)
cmyk.Plum           = cmyk(0.50, 1, 0, 0)
cmyk.Violet         = cmyk(0.79, 0.88, 0, 0)
cmyk.RoyalPurple    = cmyk(0.75, 0.90, 0, 0)
cmyk.BlueViolet     = cmyk(0.86, 0.91, 0, 0.04)
cmyk.Periwinkle     = cmyk(0.57, 0.55, 0, 0)
cmyk.CadetBlue      = cmyk(0.62, 0.57, 0.23, 0)
cmyk.CornflowerBlue = cmyk(0.65, 0.13, 0, 0)
cmyk.MidnightBlue   = cmyk(0.98, 0.13, 0, 0.43)
cmyk.NavyBlue       = cmyk(0.94, 0.54, 0, 0)
cmyk.RoyalBlue      = cmyk(1, 0.50, 0, 0)
cmyk.Blue           = cmyk(1, 1, 0, 0)
cmyk.Cerulean       = cmyk(0.94, 0.11, 0, 0)
cmyk.Cyan           = cmyk(1, 0, 0, 0)
cmyk.ProcessBlue    = cmyk(0.96, 0, 0, 0)
cmyk.SkyBlue        = cmyk(0.62, 0, 0.12, 0)
cmyk.Turquoise      = cmyk(0.85, 0, 0.20, 0)
cmyk.TealBlue       = cmyk(0.86, 0, 0.34, 0.02)
cmyk.Aquamarine     = cmyk(0.82, 0, 0.30, 0)
cmyk.BlueGreen      = cmyk(0.85, 0, 0.33, 0)
cmyk.Emerald        = cmyk(1, 0, 0.50, 0)
cmyk.JungleGreen    = cmyk(0.99, 0, 0.52, 0)
cmyk.SeaGreen       = cmyk(0.69, 0, 0.50, 0)
cmyk.Green          = cmyk(1, 0, 1, 0)
cmyk.ForestGreen    = cmyk(0.91, 0, 0.88, 0.12)
cmyk.PineGreen      = cmyk(0.92, 0, 0.59, 0.25)
cmyk.LimeGreen      = cmyk(0.50, 0, 1, 0)
cmyk.YellowGreen    = cmyk(0.44, 0, 0.74, 0)
cmyk.SpringGreen    = cmyk(0.26, 0, 0.76, 0)
cmyk.OliveGreen     = cmyk(0.64, 0, 0.95, 0.40)
cmyk.RawSienna      = cmyk(0, 0.72, 1, 0.45)
cmyk.Sepia          = cmyk(0, 0.83, 1, 0.70)
cmyk.Brown          = cmyk(0, 0.81, 1, 0.60)
cmyk.Tan            = cmyk(0.14, 0.42, 0.56, 0)
cmyk.Gray           = cmyk(0, 0, 0, 0.50)
cmyk.Grey           = cmyk.Gray
cmyk.Black          = cmyk(0, 0, 0, 1)
cmyk.White          = cmyk(0, 0, 0, 0)
cmyk.white          = cmyk.White
cmyk.black          = cmyk.Black


class palette(color, attr.changeattr):

    """palette is a collection of two colors for calculating transitions between them"""

    def __init__(self, mincolor, maxcolor, min=0, max=1):
        color.__init__(self)
        if mincolor.__class__ != maxcolor.__class__:
            raise ValueError
        self.colorclass = mincolor.__class__
        self.mincolor = mincolor
        self.maxcolor = maxcolor
        self.min = min
        self.max = max

    def getcolor(self, index):
        color = {}
        for key in self.mincolor.color.keys():
            color[key] = ((index - self.min) * self.maxcolor.color[key] +
                          (self.max - index) * self.mincolor.color[key]) / float(self.max - self.min)
        return self.colorclass(**color)

    def select(self, index, total):
        return self.getcolor(index/(total-1.0))

    def write(self, file):
        self.getcolor(0).write(file)


palette.Gray           = palette(gray.white, gray.black)
palette.Grey           = palette.Gray
palette.ReverseGray    = palette(gray.black, gray.white)
palette.ReverseGrey    = palette.ReverseGray
palette.RedGreen       = palette(rgb.red, rgb.green)
palette.RedBlue        = palette(rgb.red, rgb.blue)
palette.GreenRed       = palette(rgb.green, rgb.red)
palette.GreenBlue      = palette(rgb.green, rgb.blue)
palette.BlueRed        = palette(rgb.blue, rgb.red)
palette.BlueGreen      = palette(rgb.blue, rgb.green)
palette.RedBlack       = palette(rgb.red, rgb.black)
palette.BlackRed       = palette(rgb.black, rgb.red)
palette.RedWhite       = palette(rgb.red, rgb.white)
palette.WhiteRed       = palette(rgb.white, rgb.red)
palette.GreenBlack     = palette(rgb.green, rgb.black)
palette.BlackGreen     = palette(rgb.black, rgb.green)
palette.GreenWhite     = palette(rgb.green, rgb.white)
palette.WhiteGreen     = palette(rgb.white, rgb.green)
palette.BlueBlack      = palette(rgb.blue, rgb.black)
palette.BlackBlue      = palette(rgb.black, rgb.blue)
palette.BlueWhite      = palette(rgb.blue, rgb.white)
palette.WhiteBlue      = palette(rgb.white, rgb.blue)
palette.Rainbow        = palette(hsb(0, 1, 1), hsb(2.0/3.0, 1, 1))
palette.ReverseRainbow = palette(hsb(2.0/3.0, 1, 1), hsb(0, 1, 1))
palette.Hue            = palette(hsb(0, 1, 1), hsb(1, 1, 1))
palette.ReverseHue     = palette(hsb(1, 1, 1), hsb(0, 1, 1))

