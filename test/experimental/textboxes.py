import sys; sys.path[:0] = ["../.."]
import random, string
from pyx import *

text.set(texipc=1)
text.set(texdebug="debug.tex", usefiles=["debug.dvi"])

def randpar():
    return " ".join(["".join([random.choice(string.lowercase)
                              for j in range(random.randint(1, 3))])
                     for i in range(random.randint(100, 300))])

def randparwithdisplay():
    #par = ""
    par = randpar()
    for i in range(random.randint(0, 3)):
        par += r"\display{}xxx\enddisplay{}"
        for j in range(random.randint(0, 1)):
            par += randpar()
    #return par
    return par + randpar()

def randtext():
    return r"\par{}".join([randparwithdisplay() for i in range(random.randint(1, 10))])

def output(boxes):
    c = canvas.canvas()
    c.stroke(path.rect(0, y, shape[0], -shape[1]))
    c.stroke(boxes[i].bbox().path(), [trafo.translate(0, y), color.rgb.red])
    c.insert(boxes[i], [trafo.translate(0, y)])
    c.writeEPSfile("textboxes")

random.seed(0)
for n in range(1):
    print n
    shapes = [(10,7), (8,5)]*50
    thistext = randtext()
    boxes = text.defaulttexrunner.textboxes(thistext, shapes)
    thistextfile = open("debug.thistext", "w")
    thistextfile.write(thistext)
    thistextfile.close()
    y = 0
    c = canvas.canvas()
    for i in range(len(boxes)):
        if i < len(shapes):
            shape = shapes[i]
        #if abs(unit.topt(boxes[i].bbox().right()) - unit.topt(shape[0])) > 1:
            #print "right boundary differs!"
            #print unit.topt(boxes[i].bbox().right()), unit.topt(shape[0]), i, len(boxes)
        c.stroke(path.rect(0, y, shape[0], -shape[1]))
        c.stroke(boxes[i].bbox().path(), [trafo.translate(0, y), color.rgb.blue])
        c.insert(boxes[i], [trafo.translate(0, y)])
        for mark in boxes[i].markers.keys():
            mx, my = boxes[i].markers[mark]
            if mark[:5] == "start":
                c.fill(path.circle(mx, my+y, 0.05), [color.rgb.red])
            elif mark[:3] == "end":
                c.fill(path.circle(mx, my+y, 0.05), [color.rgb.green])
            else:
                raise "other marks in there!"
        y -= shape[1] + 3
    c.writeEPSfile("textboxes")

