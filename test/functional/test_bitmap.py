import sys; sys.path.insert(0, "../..")
from pyx import *

image_bw = bitmap.image(2, 2, "L", "\0\377\377\0")
image_rgb = bitmap.image(3, 2, "RGB", "\77\77\77\177\177\177\277\277\277"
                                      "\377\0\0\0\377\0\0\0\377")
bitmap_bw_stream = bitmap.bitmap(0, 1, image_bw, height=0.8)
bitmap_rgb_stream = bitmap.bitmap(0, 0, image_rgb, height=0.8)

bitmap_bw_storestring = bitmap.bitmap(2, 1, image_bw, height=0.8, storedata=1)
bitmap_rgb_storestring = bitmap.bitmap(2, 0, image_rgb, height=0.8, storedata=1)

bitmap_bw_storearray = bitmap.bitmap(4, 1, image_bw, height=0.8, storedata=1, maxstrlen=2)
bitmap_rgb_storearray = bitmap.bitmap(4, 0, image_rgb, height=0.8, storedata=1, maxstrlen=2)

c = canvas.canvas()
c.insert(bitmap_bw_stream)
c.insert(bitmap_rgb_stream)
c.insert(bitmap_bw_stream)
c.insert(bitmap_rgb_stream)
c.insert(bitmap_bw_storestring)
c.insert(bitmap_rgb_storestring)
c.insert(bitmap_bw_storestring)
c.insert(bitmap_rgb_storestring)
c.insert(bitmap_bw_storearray)
c.insert(bitmap_rgb_storearray)
c.insert(bitmap_bw_storearray)
c.insert(bitmap_rgb_storearray)
c.writeEPSfile("test_bitmap", paperformat="a4")

