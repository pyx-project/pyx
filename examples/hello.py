from pyx import *

c = canvas.canvas()
c.text(0, 0, r"Hello, world!\xxx")
c.stroke(path.line(0, 0, 2, 0))
c.writetofile("hello")
