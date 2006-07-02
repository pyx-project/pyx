from pyx import *

text.set(mode="latex")
text.preamble(r"\usepackage{exscale}")

spameggswidth = 2.7
arrowdist = 0.1
arrowlen = 0.2
textdist = 0.1

c = canvas.canvas()


def label(x, y, width, t): # x == -1 -> left; x == 1 -> right
    c.stroke(path.line(width*(0.5*x+0.5) + x*arrowdist, y,
                       width*(0.5*x+0.5) + x*(arrowdist + arrowlen), y),
             [deco.barrow.Small])
    c.text(width*(0.5*x+0.5) + x*(arrowdist + arrowlen + textdist), y,
           t, [text.vshift.mathaxis, text.boxhalign(0.5-0.5*x)])


t = c.text(0, 0, r"\noindent spam \& eggs", [text.parbox(2.7), text.size.Huge])
t2 = text.text(0, 0, "eggs", [text.size.Huge])

c.stroke(t.bbox().path(), [style.linewidth.THin])
c.stroke(path.line(0, 0, 2.7, 0) +
         path.line(0, t2.depth-t.depth, 2.7, t2.depth-t.depth),
         [style.linestyle.dashed, style.linewidth.THin])

label(-1, t.height, spameggswidth, "valign.top")
label(-1, 0.5*(t.height-t.depth), spameggswidth, "valign.middle")
label(-1, -t.depth, spameggswidth, "valign.bottom")
label(1, 0, spameggswidth, "parbox.top")
label(1, 0.5*(t2.depth-t.depth), spameggswidth, "parbox.middle")
label(1, t2.depth-t.depth, spameggswidth, "parbox.bottom")

mathypos = -2.5
mathstr = r"\sum_{i=0}^{\infty}\frac{1}{i^2}=\frac{1}{6}\pi^2"

t = c.text(0, mathypos, mathstr, [text.mathmode, text.vshift.mathaxis, text.size.LARGE])
t2 = text.text(0, mathypos, mathstr, [text.mathmode, text.size.LARGE])

c.stroke(t.bbox().path(), [style.linewidth.THin])
c.stroke(path.line(0, mathypos, t.width, mathypos)+
         path.line(0, mathypos+t.height-t2.height, t.width, mathypos+t.height-t2.height),
         [style.linestyle.dashed, style.linewidth.THin])

label(-1, mathypos, t.width, "vshift.mathaxis")
label(1, mathypos+t.height-t2.height, t.width, "baseline")

c.writeEPSfile("valign")
