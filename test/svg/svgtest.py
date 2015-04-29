import sys; sys.path.insert(0, "../..")
from glob import glob
from pyx import *
from PIL import Image

d = document.document()
for i, f in enumerate(glob('suite/svg/shapes-*.svg') +
                      glob('suite/svg/paths-data-*.svg')):
    #if i + 1 != 15: continue
    print(i+1, f)
    c = canvas.canvas()
    i = Image.open(f.replace('svg', 'png'))
    b = bitmap.bitmap(0, 0, i)
    c.insert(b)
    c.insert(svgfile.svgfile(b.bbox().width(), 0, f, parsed=True, resolution=i.info["dpi"][0]))
    d.append(document.page(c))
d.writePDFfile()
