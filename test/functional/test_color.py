import sys; sys.path.insert(0, "../..")
from pyx import *

try:
    enumerate([])
except NameError:
    # fallback implementation for Python 2.2 and below
    def enumerate(list):
        return zip(xrange(len(list)), list)


c = canvas.canvas()

# color conversion tests
def UCRc(x): return x
def UCRm(x): return x
def UCRy(x): return x
def BG(x): return x
color.set(UCRc=UCRc, UCRm=UCRm, UCRy=UCRy, BG=BG)

def colrow(can, pos, acol):
  width, height = 1.0, 1.0
  colors = [acol.grey(), acol.rgb(), acol.hsb(), acol.cmyk()]
  for i, col in enumerate(colors):
      can.draw(path.rect(pos[0]+i*width, pos[1], width, height), [deco.filled([col]), deco.stroked()])
  return pos[0], pos[1] - height

pos = 0, -5
for col in [color.grey.black, color.grey(0.25), color.grey(0.5), color.grey(0.75), color.grey.white,
            color.rgb.red, color.rgb.green, color.rgb.blue, color.rgb.white, color.rgb.black,
            color.cmyk.GreenYellow, color.cmyk.Yellow, color.cmyk.Goldenrod, color.cmyk.Dandelion, color.cmyk.Apricot,
            color.cmyk.Peach, color.cmyk.Melon, color.cmyk.YellowOrange, color.cmyk.Orange, color.cmyk.BurntOrange,
            color.cmyk.Bittersweet, color.cmyk.RedOrange, color.cmyk.Mahogany, color.cmyk.Maroon, color.cmyk.BrickRed,
            color.cmyk.Red, color.cmyk.OrangeRed, color.cmyk.RubineRed, color.cmyk.WildStrawberry, color.cmyk.Salmon,
            color.cmyk.CarnationPink, color.cmyk.Magenta, color.cmyk.VioletRed, color.cmyk.Rhodamine, color.cmyk.Mulberry,
            color.cmyk.RedViolet, color.cmyk.Fuchsia, color.cmyk.Lavender, color.cmyk.Thistle, color.cmyk.Orchid,
            color.cmyk.DarkOrchid, color.cmyk.Purple, color.cmyk.Plum, color.cmyk.Violet, color.cmyk.RoyalPurple,
            color.cmyk.BlueViolet, color.cmyk.Periwinkle, color.cmyk.CadetBlue, color.cmyk.CornflowerBlue,
            color.cmyk.MidnightBlue, color.cmyk.NavyBlue, color.cmyk.RoyalBlue, color.cmyk.Blue, color.cmyk.Cerulean,
            color.cmyk.Cyan, color.cmyk.ProcessBlue, color.cmyk.SkyBlue, color.cmyk.Turquoise, color.cmyk.TealBlue,
            color.cmyk.Aquamarine, color.cmyk.BlueGreen, color.cmyk.Emerald, color.cmyk.JungleGreen, color.cmyk.SeaGreen,
            color.cmyk.Green, color.cmyk.ForestGreen, color.cmyk.PineGreen, color.cmyk.LimeGreen, color.cmyk.YellowGreen,
            color.cmyk.SpringGreen, color.cmyk.OliveGreen, color.cmyk.RawSienna, color.cmyk.Sepia, color.cmyk.Brown, color.cmyk.Tan,
            color.cmyk.Gray, color.cmyk.Black, color.cmyk.White, color.cmyk.white, color.cmyk.black]:
    pos = colrow(c, pos, col)


c.writeEPSfile("test_color", paperformat=document.paperformat.A4, fittosize=1)

# transparency tests
c.fill(path.rect(-1, -1, 2, 2), [color.rgb.red])
c.fill(path.circle(0, 0, 1.2), [color.transparency(0.5), color.rgb.green])
c.fill(path.rect(-2, -0.5, 4, 1), [color.transparency(0.9), color.rgb.blue])

c.writePDFfile("test_color", paperformat=document.paperformat.A4, fittosize=1)

