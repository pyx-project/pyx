from pyx import *

c = canvas.canvas()
c.stroke(path.curve(0, 0, 0, 4, 2, 4, 3, 3),
         [style.linewidth.THICK, style.linestyle.dashed, color.rgb.blue,
          deco.earrow([deco.stroked([color.rgb.red, style.linejoin.round]),
                       deco.filled([color.rgb.green])], size=1)])
c.writeEPSfile("arrow")
c.writePDFfile("arrow")
c.writeSVGfile("arrow")
