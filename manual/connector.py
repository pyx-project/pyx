#!/usr/bin/env python
# -*- coding: ISO-8859-15 -*-
import sys
sys.path.insert(0, "..")
from math import *
from pyx import *

startbox = box.polygon(corners=[[0,-0.6], [0.5,0.1], [-0.25,0.1]])
endbox = box.polygon(corners=[[4.5,3.9], [5.5,4.0], [5.2,3.4]])

# the arc connector <<<
c1 = canvas.canvas()
for b in [startbox, endbox]:
    c1.stroke(b.path(), [style.linewidth.Thick, style.linejoin.round])
    c1.fill(path.circle_pt(b.center[0], b.center[1], 2))
absangle = atan2(endbox.center[1] - startbox.center[1], endbox.center[0] - startbox.center[0])*180/pi
relangle = 60
len = 2

# the direct connection
direct = path.line_pt(startbox.center[0], startbox.center[1], endbox.center[0], endbox.center[1])
c1.stroke(direct, [style.linestyle.dashed])

# the arc connector
l = connector.arc(startbox, endbox, relangle=relangle, boxdists=[0.0,0.0])
c1.stroke(l, [style.linewidth.Thick, color.rgb.red, deco.earrow.Large])

# the relangle parameter
comp1 = path.path(path.moveto(*direct.atbegin()),
                  path.rlineto(len*cos((absangle + relangle)*pi/180), len*sin((absangle + relangle)*pi/180)))
c1.stroke(comp1)
ang = path.path(path.arc(direct.atbegin()[0], direct.atbegin()[1], 0.8*len, absangle, absangle+relangle))
c1.stroke(ang, [deco.earrow.large])
pos = ang.at(0.5*ang.arclen())
c1.text(pos[0], pos[1], r"~relangle", [text.halign.left])

# the bulge parameter
bulge = 0.5 * direct.arclen() * tan(0.5*relangle*pi/180)
bul = path.path(path.moveto(*direct.at(0.5*direct.arclen())),
                path.rlineto(bulge * cos((absangle+90)*pi/180), bulge * sin((absangle+90)*pi/180)))
c1.stroke(bul, [deco.earrow.large])
pos = bul.at(0.5*bul.arclen())
c1.text(pos[0], pos[1], r"~(rel)bulge", [text.halign.left])

# >>>

# the curve connector <<<
c2 = canvas.canvas()
for b in [startbox, endbox]:
    c2.stroke(b.path(), [style.linewidth.Thick, style.linejoin.round])
    c2.fill(path.circle_pt(b.center[0], b.center[1], 2))
absangle = atan2(endbox.center[1] - startbox.center[1], endbox.center[0] - startbox.center[0])*180/pi
relangle1 = 60
relangle2 = 30
absbulge = 0
relbulge = 0.5
len = 2

# the direct connection
direct = path.line_pt(startbox.center[0], startbox.center[1], endbox.center[0], endbox.center[1])
c2.stroke(direct, [style.linestyle.dashed])

# the arc connector
l = connector.curve(startbox, endbox, relangle1=relangle1, relangle2=relangle2, absbulge=absbulge, relbulge=relbulge, boxdists=[0.0,0.0])
#l = connector.curve(startbox, endbox, absangle1=absangle+relangle1, absangle2=absangle+relangle2, absbulge=absbulge, relbulge=relbulge, boxdists=[0.0,0.0])
c2.stroke(l, [style.linewidth.Thick, color.rgb.red, deco.earrow.Large])

# the relangle parameters
# relangle1
c2.stroke(path.path(path.moveto(*direct.atbegin()),
                   path.rlineto(len*cos((absangle + relangle1)*pi/180),
                                len*sin((absangle + relangle1)*pi/180))))
ang = path.path(path.arc(direct.atbegin()[0], direct.atbegin()[1], 0.8*len, absangle, absangle+relangle1))
c2.stroke(ang, [deco.earrow.large])
pos = ang.at(0.5*ang.arclen())
c2.text(pos[0], pos[1], r"~relangle1", [text.halign.left])

# absangle1
c2.stroke(path.path(path.moveto(*direct.atbegin()), path.rlineto(len, 0)))
ang = path.path(path.arc(direct.atbegin()[0], direct.atbegin()[1], 0.5*len, 0, absangle+relangle1))
c2.stroke(ang, [deco.earrow.large])
pos = ang.at(0.2*ang.arclen())
c2.text(pos[0], pos[1], r"~absangle1", [text.halign.left])

# relangle2
c2.stroke(path.path(path.moveto(*direct.atend()),
                   path.rlineto(len*cos(absangle*pi/180),
                                len*sin(absangle*pi/180))))
c2.stroke(path.path(path.moveto(*direct.atend()),
                   path.rlineto(len*cos((absangle + relangle2)*pi/180),
                                len*sin((absangle + relangle2)*pi/180))))
ang = path.path(path.arc(direct.atend()[0], direct.atend()[1],
                         0.8*len, absangle, absangle+relangle2))
c2.stroke(ang, [deco.earrow.large])
pos = ang.at(0.5*ang.arclen())
c2.text(pos[0], pos[1], r"~relangle2", [text.halign.left])

# the bulge parameter
bulge = absbulge + direct.arclen() * relbulge
bul = path.path(path.moveto(*direct.atbegin()),
                path.rlineto(bulge * cos((absangle+relangle1)*pi/180), bulge * sin((absangle+relangle1)*pi/180)))
c2.stroke(bul, [deco.earrow.large])
pos = bul.at(0.7*bul.arclen())
c2.text(pos[0], pos[1], r"~(rel)bulge", [text.halign.left])

bul = path.path(path.moveto(*direct.atend()),
                path.rlineto(-bulge * cos((absangle+relangle2)*pi/180), -bulge * sin((absangle+relangle2)*pi/180)))
c2.stroke(bul, [deco.earrow.large])
pos = bul.at(0.7*bul.arclen())
c2.text(pos[0], pos[1], r"~(rel)bulge", [text.halign.left, text.vshift(1)])
# >>>


# write everything
c1.insert(c2, [trafo.translate(6.5, 0)])
c1.writeEPSfile("connector", paperformat=document.paperformat.A4)
c1.writePDFfile("connector")

# vim:foldmethod=marker:foldmarker=<<<,>>>
