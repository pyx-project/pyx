#!/usr/bin/env python

from t1strip import t1strip

glyphs = [0] * 256
for c in "Hello World":
    glyphs[ord(c)] = 1

outfile = open("cmr10.part.pfa", "w")
t1strip(outfile, "cmr10.pfb", glyphs)
outfile.close()
