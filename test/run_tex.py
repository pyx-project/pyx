#!/usr/bin/python 

#from canvas import *
#from graph import *
#from axis import *

#canvas(1,2,"1.5cm")
#amove(1,1)
#amove(1,1)
#aline(2,2)

#graph(1,3,title="Titelstring")
#linaxis(title="Achsentitel",min=0,max=20)
#ticks(step=5)
#joinaxis("x")
#linaxis(title="Achsentitel",min=0,max=50)
#ticks(step=10)
#joinaxis("y")

#DefaultGraph.DelNamespace("DefaultGraph",globals())
#DefaultCanvas.DelNamespaces()
#DefaultAxis.DelNamespaces()

#canvas(1,3,name="beispiel")
#amove(2,4)
#amove(3,5)

from tex import *

tex()

print "Breite von 'Hello world!': ",textwd("Hello world!")
print "Höhe von 'Hello world!': ",textht("Hello world!")
print "Tiefe von 'Hello world!': ",textdp("Hello world!")
print "Tiefe von 'was mit q': ",textdp("was mit q")
amove(5,1)
text("Hello world!")
amove(5,2)
text("\Large Hello world!",halign=center)
amove(5,3)
text("Hello world!",halign=right)
for angle in (-90,-80,-70,-60,-50,-40,-30,-20,-10,0,10,20,30,40,50,60,70,80,90):
  amove(11+angle/10,5)
  text(str(angle),angle=angle)
  amove(11+angle/10,6)
  text(str(angle),angle=angle,halign=center)
  amove(11+angle/10,7)
  text(str(angle),angle=angle,halign=right)
amove(5,12)
text("Beispiel:\\begin{itemie}\\item$\\alpha$\\item$\\beta$\\item$\\gamma$\\end{itemize}",parmode="2cm")
amove(10,12)
text("Beispiel:\\begin{itemize}\\item$\\alpha$\\item$\\beta$\\item$\\gamma$\\end{itemize}",parmode="2cm",valign=center)
amove(15,12)
text("Beispiel:\\begin{itemize}\\item$\\alpha$\\item$\\beta$\\item$\\gamma$\\end{itemize}",parmode="2cm",valign=bottom)

DefaultTex.TexRun()
