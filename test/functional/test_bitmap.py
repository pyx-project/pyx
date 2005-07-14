import sys; sys.path.insert(0, "../..")
from pyx import *
try:
    from Image import open
except:
    print "PIL not available, skipping palette test"
    paletteimage = None
else:
    paletteimage = open("../../www/vcss.png")

image_bw = bitmap.image(2, 2, "L", "\0\377\377\0")
image_rgb = bitmap.image(3, 2, "RGB", "\77\77\77\177\177\177\277\277\277"
                                      "\377\0\0\0\377\0\0\0\377")

bitmap_bw_stream = bitmap.bitmap(0, 1, image_bw, height=0.8)
bitmap_rgb_stream = bitmap.bitmap(0, 0, image_rgb, height=0.8)

bitmap_bw_storestring = bitmap.bitmap(2, 1, image_bw, height=0.8, PSstoreimage=1)
bitmap_rgb_storestring = bitmap.bitmap(2, 0, image_rgb, height=0.8, PSstoreimage=1)

bitmap_bw_storearray = bitmap.bitmap(4, 1, image_bw, height=0.8, PSstoreimage=1, PSmaxstrlen=2)
bitmap_rgb_storearray = bitmap.bitmap(4, 0, image_rgb, height=0.8, PSstoreimage=1, PSmaxstrlen=2)

c = canvas.canvas()
c.insert(bitmap_bw_stream)
c.insert(bitmap_rgb_stream)
c.insert(bitmap_bw_storestring)
c.insert(bitmap_rgb_storestring)
c.insert(bitmap_bw_storearray)
c.insert(bitmap_rgb_storearray)
if paletteimage:
    c.insert(bitmap.bitmap(6, 0, paletteimage, height=1.8))
c.writeEPSfile("test_bitmap", paperformat=document.paperformat.A4)
c.writePDFfile("test_bitmap", paperformat=document.paperformat.A4)

