from canvas import *
from path import *

c1=canvas()
c2=canvas()
c3=canvas()
c4=canvas()

c1.draw(rect(5,5,5,5))
c1.write("test1", 21, 29.7)

c2.draw(rect(5,5,5,5))
c2.inserteps(5,5,"small.eps")
c2.write("test2", 21, 29.7)

c3.draw(rect(5,5,5,5))
t3=c3.tex()
t3.text(5,5,"hello world!")
c3.draw(rect(str(141)+" t pt",str(141)+" t pt",str(193-141)+" t pt",str(150-141)+" t pt"))
c3.write("test3", 21, 29.7)

c4.draw(rect(5,5,5,5))
c4.inserteps(5,6,"small.eps")
c4.draw(rect(5.5,5.5,5,5))
t4=c4.tex()
c4.draw(rect(6,6,5,5))
t4.text(5,5,"hello world!")
c4.inserteps(5,5,"small.eps")
c4.draw(rect(7,7,5,5))
c4.write("test4", 21, 29.7)
