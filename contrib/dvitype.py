# This is a dvitype clone based on the dvi reader of PyX.
# 
# Note that its absolutely minimalistic and it misses some
# features of dvitype. Its just a a gimmick ...

import sys
from pyx import dvifile

df = dvifile.dvifile(sys.argv[1], dvifile.readfontmap(["psfonts.map"]), 1)

while df.readpage():
    pass

