from pyx import *
from PIL import Image

im = Image.new("RGB", (3, 1))
im.putpixel((0, 0), (255, 0, 0))
im.putpixel((1, 0), (0, 255, 0))
im.putpixel((2, 0), (0, 0, 255))

c = canvas.canvas()
c.insert(bitmap.bitmap(0, 0, im, height=0.8))
c.writeEPSfile("pil")
c.writePDFfile("pil")
c.writeSVGfile("pil")
