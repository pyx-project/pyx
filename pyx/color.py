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

import base

class color(base.PSAttr):

    """base class for all colors"""
    
    pass


class grey(color):
    
    """grey tones"""
    
    def __init__(self, level):
        assert 0<=level and level<=1, "grey value must be between 0 and 1"
        self.level=level

    def write(self, file):
        file.write("%f setgray\n" % self.level)

grey.black = grey(0.0)
grey.white = grey(1.0)
    

class rgb(color):

    """rgb colors"""
    
    def __init__(self, r=0.0, g=0.0, b=0.0):
        assert 0<=r and r<=1, "red value must be between 0 and 1"
        assert 0<=g and g<=1, "green value must be between 0 and 1"
        assert 0<=b and b<=1, "blue value must be between 0 and 1"
        self.r=r
        self.g=g
        self.b=b

    def write(self, file):
        file.write("%f %f %f setrgbcolor\n" % (self.r, self.g, self.b))

rgb.red   = rgb(1,0,0)
rgb.green = rgb(0,1,0)
rgb.blue  = rgb(0,0,1)
       

class hsb(color):

    """hsb colors"""
    
    def __init__(self, h=0.0, s=0.0, b=0.0):
        assert 0<=h and h<=1, "hue value must be between 0 and 1"
        assert 0<=s and s<=1, "saturation value must be between 0 and 1"
        assert 0<=b and b<=1, "brightness value must be between 0 and 1"
        self.h=h
        self.s=s
        self.b=b

    def write(self, file):
        file.write("%f %f %f sethsbcolor\n" % (self.h, self.s, self.b))
        

class cmyk(color):

    """cmyk colors"""
    
    def __init__(self, c=0.0, m=0.0, y=0.0, k=0.0):
        assert 0<=c and c<=1, "cyan value must be between 0 and 1"
        assert 0<=m and m<=1, "magenta value must be between 0 and 1"
        assert 0<=y and y<=1, "yellow value must be between 0 and 1"
        assert 0<=k and k<=1, "black value must be between 0 and 1"
        self.c=c
        self.m=m
        self.y=y
        self.k=k

    def write(self, file):
        file.write("%f %f %f %f setcmykcolor\n" %
                   (self.c, self.m, self.y, self.k))

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
cmyk.Black          = cmyk(0, 0, 0, 1)
cmyk.White          = cmyk(0, 0, 0, 0)
