# You can use image instances from the Python Image Library
# (http://www.pythonware.com/products/pil/) to create bitmaps.
# While you do not need the PIL to create an image pixel by
# pixel (and its slow to use putpixel for that), you do have
# an easy access to all the bitmap formats available in PIL,
# you may use PIL features to create/modify bitmaps etc.

from pyx import *
import Image

im = Image.new("RGB", (3, 1))
im.putpixel((0, 0), (255, 0, 0))
im.putpixel((1, 0), (0, 255, 0))
im.putpixel((2, 0), (0, 0, 255))

c = canvas.canvas()
c.insert(bitmap.bitmap(0, 0, im, height=0.8))
c.writeEPSfile("pil")
