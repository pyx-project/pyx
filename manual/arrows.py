from pyx import *

text.set(text.LatexRunner)
text.preamble(r"\renewcommand{\familydefault}{\ttdefault}")
c = canvas.canvas()

# positioning is quite ugly ... but it works at the moment
x = 0
y = 0
dx = 6
dy = -0.65
length = 1.2

def drawdeco(name, showpath=0, default=0):
    global x,y
    p = path.path(path.moveto(x + 0.1, y+0.1 ),
                       path.rlineto(length/2.0, 0.3),
                       path.rlineto(length/2.0, -0.3))
    c.stroke(p, [style.linewidth.THIck,  eval("deco."+name)])
    if showpath:
        c.stroke(p, [style.linewidth.Thin, color.gray.white])
    if default:
        name = name + r"\rm\quad (default)"
    c.text(x + 1.5, y + 0.15, name, [text.size.footnotesize])
    y += dy
    if y < -16:
        y = 0
        x += dx

drawdeco("earrow.Small")
drawdeco("earrow.small")
drawdeco("earrow.normal")
drawdeco("earrow.large")
drawdeco("earrow.Large")

y += dy

drawdeco("barrow.normal")

y += dy

drawdeco("earrow.Large([deco.filled([color.rgb.red]), style.linewidth.normal])")
drawdeco("earrow.normal(constriction=None)")
drawdeco("earrow.Large([style.linejoin.round])")
drawdeco("earrow.Large([deco.stroked.clear])")

c.writePDFfile()
