#!/usr/bin/python 
from pyx import *

c=canvas.canvas()
t=c.insert(tex.tex())

t.text(0, 0, "Hello, world!")
print "width of 'Hello, world!': ", t.textwd("Hello, world!")
print "height of 'Hello, world!': ", t.textht("Hello, world!")
print "depth of 'Hello, world!': ", t.textdp("Hello, world!")

c.writetofile("test_tex")

