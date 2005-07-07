# You can insert a jpeg image directly in PyX by the jpegimage
# class. It extracts the compressed jpeg data and makes the
# data available to a PyX bitmap without recompression (i.e.
# no loss of quality).

from pyx import *

i = bitmap.jpegimage("jpeg.jpg")
c = canvas.canvas()
c.insert(bitmap.bitmap(0, 0, i, compressmode=None))
c.writeEPSfile("jpeg")
