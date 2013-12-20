from pyx import *

text.set(text.LatexRunner)
text.preamble(r"\renewcommand{\familydefault}{\ttdefault}")
c = canvas.canvas()

# positioning is quite ugly ... but it works at the moment
x = 0
y = 0
dx = 6
dy = -0.65
length = 0.8

def drawstyle(name, showpath=0, default=0):
    global x,y
    p = path.path(path.moveto(x + 0.1, y+0.1 ),
                       path.rlineto(length/2.0, 0.3),
                       path.rlineto(length/2.0, -0.3))
    c.stroke(p, [style.linewidth.THIck,  eval("style."+name)])
    if showpath:
        c.stroke(p, [style.linewidth.Thin, color.gray.white])
    if default:
        name = name + r"\rm\quad (default)"
    c.text(x + 1.5, y + 0.15, name, [text.size.footnotesize])
    y += dy
    if y < -16:
        y = 0
        x += dx


drawstyle("linecap.butt", showpath=1, default=1)
drawstyle("linecap.round", showpath=1)
drawstyle("linecap.square", showpath=1)

y += dy

drawstyle("linejoin.miter", showpath=1, default=1)
drawstyle("linejoin.round", showpath=1)
drawstyle("linejoin.bevel", showpath=1)

y += dy

drawstyle("linestyle.solid", default=1)
drawstyle("linestyle.dashed")
drawstyle("linestyle.dotted")
drawstyle("linestyle.dashdotted")

y += dy

drawstyle("linewidth.THIN")
drawstyle("linewidth.THIn")
drawstyle("linewidth.THin")
drawstyle("linewidth.Thin")
drawstyle("linewidth.thin")
drawstyle("linewidth.normal", default=1)
drawstyle("linewidth.thick")
drawstyle("linewidth.Thick")
drawstyle("linewidth.THick")
drawstyle("linewidth.THIck")
drawstyle("linewidth.THICk")
drawstyle("linewidth.THICK")

drawstyle("miterlimit.lessthan180deg", showpath=1)
drawstyle("miterlimit.lessthan90deg", showpath=1)
drawstyle("miterlimit.lessthan60deg", showpath=1)
drawstyle("miterlimit.lessthan45deg", showpath=1)
drawstyle("miterlimit.lessthan11deg", showpath=1, default=1)

y += dy

drawstyle("dash((1, 1, 2, 2, 3, 3), 0)")
drawstyle("dash((1, 1, 2, 2, 3, 3), 1)")
drawstyle("dash((1, 2, 3), 2)")
drawstyle("dash((1, 2, 3), 3)")
drawstyle("dash((1, 2, 3), 4)")
drawstyle("dash((1, 2, 3), rellengths=1)")


c.writePDFfile()
