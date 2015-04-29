from pyx import *

i = bitmap.jpegimage("jpeg.jpg")
c = canvas.canvas()
c.insert(bitmap.bitmap(0, 0, i, compressmode=None))
c.writeEPSfile("jpeg")
c.writePDFfile("jpeg")
c.writeSVGfile("jpeg")
