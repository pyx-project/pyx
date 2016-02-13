from pyx import *
text.set(text.LatexRunner)

c = canvas.canvas()
c.text(0, 0, r"\font\manual=manfnt\manual\raisebox{0pt}[9pt][11pt]{\char127}")
c.writeEPSfile("bend")
