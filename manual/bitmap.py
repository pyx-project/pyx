from pyx import *

image_bw = bitmap.image(2, 2, "L", b"\0\377\377\0")
image_rgb = bitmap.image(3, 2, "RGB", b"\77\77\77\177\177\177\277\277\277"
                                      b"\377\0\0\0\377\0\0\0\377")
bitmap_bw = bitmap.bitmap(0, 1, image_bw, height=0.8)
bitmap_rgb = bitmap.bitmap(0, 0, image_rgb, height=0.8)

c = canvas.canvas()
c.insert(bitmap_bw)
c.insert(bitmap_rgb)
c.writePDFfile()

