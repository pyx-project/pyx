from pyx import *

c = canvas.canvas()

# apply global TeX setting
text.preamble(r"\parindent=0pt")

# vertical alignments by margins
c.stroke(path.line(0, 4, 6, 4), canvas.linewidth.THin)
c.text(0, 4, r"spam \& eggs", text.vbox(1.2), text.valign.top)
c.text(2, 4, r"spam \& eggs", text.vbox(1.2), text.valign.middle)
c.text(4, 4, r"spam \& eggs", text.vbox(1.2), text.valign.bottom)

# vertical alignments by baselines
c.stroke(path.line(0, 2, 6, 2), canvas.linewidth.THin)
c.text(0, 2, r"spam \& eggs", text.vbox(1.2), text.valign.topbaseline)
c.text(2, 2, r"spam \& eggs", text.vbox(1.2), text.valign.middlebaseline)
c.text(4, 2, r"spam \& eggs", text.vbox(1.2), text.valign.bottombaseline)

# vertical shifts
c.stroke(path.line(0, 0, 8, 0), canvas.linewidth.THin)
c.text(0, 0, r"x=0", text.mathmode, text.vshift.topzero)
c.text(2, 0, r"x=0", text.mathmode, text.vshift.middlezero)
c.text(4, 0, r"x=0", text.mathmode, text.vshift.bottomzero)
c.text(6, 0, r"x=0", text.mathmode, text.vshift.mathaxis)

c.writetofile("valign")
