#!/usr/bin/env python
import sys
sys.path.append("..")
from pyx import *
import pyx.canvas 
from pyx.graph import *
from pyx.tex   import *
from pyx.path  import *
from pyx.trafo import *
from pyx.color import *
import pyx.unit

c=canvas.canvas()
t=c.insert(tex())

#for x in range(11):
#    amove(x,0)
#    rline(0,20)
#for y in range(21):
#   amove(0,y)
#   rline(10,0)
 
c.draw(path( moveto(1,1), 
              lineto(2,2), 
              moveto(1,2), 
              lineto(2,1) 
             )
       )


c.draw(line(1, 1, 1,2)) 

print "Breite von 'Hello world!': ",t.textwd("Hello  world!")
print "Höhe von 'Hello world!': ",t.textht("Hello world!")
print "Höhe von 'Hello world!' in large: ",t.textht("Hello world!", fontsize.large)
print "Höhe von 'Hello world!' in Large: ",t.textht("Hello world!", fontsize.Large)
print "Höhe von 'Hello world' in huge: ",t.textht("Hello world!", fontsize.huge)
print "Tiefe von 'Hello world!': ",t.textwd("Hello world!")
print "Tiefe von 'Hello world!': ",t.textht("Hello world!")
print "Tiefe von 'Hello world!': ",t.textdp("Hello world!")
print "Tiefe von 'was mit q': ",t.textdp("was mit q")
print "Tiefe von 'was mit q': ",t.textdp("was mit q")
t.text(5, 1, "Hello world!")
t.text(15, 1, "Hello world!", fontsize.huge)
t.text(5, 2, "Hello world!", halign.center)
t.text(5, 3, "Hello world!", halign.right)
for angle in (-90,-80,-70,-60,-50,-40,-30,-20,-10,0,10,20,30,40,50,60,70,80,90):
    t.text(11+angle/10, 5, str(angle), direction(angle))
    t.text(11+angle/10, 6, str(angle), direction(angle), halign.center)
    t.text(11+angle/10, 7, str(angle), direction(angle), halign.right)
    
for pos in range(2,21):
    c.draw(line(pos, 4.5, pos, 7.5)) 
    c.draw(line(1.5, 5, 20.5, 5)) 
    c.draw(line(1.5, 6, 20.5, 6)) 
    c.draw(line(1.5, 7, 20.5, 7)) 
    
p=path( moveto(5,12), 
         lineto(7,12), 
         moveto(5,10), 
         lineto(5,14), 
         moveto(7,10), 
         lineto(7,14) )

c.set(canvas.linestyle.dotted)
t.text(5, 12, "a b c d e f g h i j k l m n o p q r s t u v w x y z", valign.top("2 cm"))
c.draw(p)

p=path( moveto(10,12), 
         lineto(12,12), 
         moveto(10,10), 
         lineto(10,14), 
         moveto(12,10), 
         lineto(12,14))
c.set(canvas.linestyle.dashdotted, rgb(1,0,0))
t.text("10 cm", 12, "a b c d e f g h i j k l m n o p q r s t u v w x y z", valign.bottom("2 cm"), gray(0.5))
c.draw(p)

p=path(moveto(5,15), arc(5,15, 1, 0, 45), closepath())
c.fill(p, canvas.linestyle.dotted, canvas.linewidth.THICK)

p=path(moveto(5,17), curveto(6,18, 5,16, 7,15))
c.draw(p, canvas.linestyle.dashed)

   
for angle in range(20):
    s=c.insert(canvas.canvas(translate(10,10)*rotate(angle))).draw(p, canvas.linestyle.dashed, canvas.linewidth(0.01*angle), gray((20-angle)/20.0))

c.set(canvas.linestyle.solid)
    
c.draw(path(moveto("5 cm", "5 cm"), rlineto(0.1,0.1)), canvas.linewidth.THICK)

c.writetofile("example")
