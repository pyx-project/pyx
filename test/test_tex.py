#!/usr/bin/python 
import sys
sys.path.append("..")

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

from pyx import *

c=canvas.canvas()
t=c.insert(tex.tex())

t.text(0, 0, "Hello, world!")
print "width of 'Hello, world!': ", t.textwd("Hello, world!")
print "height of 'Hello, world!': ", t.textht("Hello, world!")
print "depth of 'Hello, world!': ", t.textdp("Hello, world!")

c.writetofile("test_tex")

