# You can vertically align the text using the box boundaries.
# But most of the time, you may want to use TeX's baseline for
# vertical alignment.
#
# Additionally, you have access to TeX's math axis. This is where
# TeX aligns mathematical symbols like plus, minus and equal signs.
# We're often use this axis to vertically align text, for example
# for labels at the axis ticks of vertical axes.

from pyx import *

c = canvas.canvas()
c.set([style.linestyle.dotted])

# apply global TeX setting
text.preamble(r"\parindent=0pt")
unit.set(xscale=1.5) # enlarge all text (we want to see the details)
w = 1.2 * unit.x_cm # an appropriate parbox width for spam & eggs

# vertical alignments by margins
c.stroke(path.line(0, 6, 12, 6), [style.linewidth.THin])
c.text(0, 6, r"spam \& eggs", [text.parbox(w), text.valign.top])
c.text(4, 6, r"spam \& eggs", [text.parbox(w), text.valign.middle])
c.text(8, 6, r"spam \& eggs", [text.parbox(w), text.valign.bottom])

# vertical alignments by baselines
c.stroke(path.line(0, 3, 12, 3), [style.linewidth.THin])
c.text(0, 3, r"spam \& eggs", [text.parbox(w, baseline=text.parbox.top)])
c.text(4, 3, r"spam \& eggs", [text.parbox(w, baseline=text.parbox.middle)])
c.text(8, 3, r"spam \& eggs", [text.parbox(w, baseline=text.parbox.bottom)])

# vertical shifts
c.stroke(path.line(0, 0, 12, 0), [style.linewidth.THin])
c.text(0, 0, r"x=0", [text.mathmode, text.vshift.topzero])
c.text(3, 0, r"x=0", [text.mathmode, text.vshift.middlezero])
c.text(6, 0, r"x=0", [text.mathmode, text.vshift.bottomzero])
c.text(9, 0, r"x=0", [text.mathmode, text.vshift.mathaxis])

c.writeEPSfile("valign")
c.writePDFfile("valign")
