try:
    import _t1strip
    t1strip = _t1strip.t1strip
except:
    import fullfont
    def t1strip(file, pfbfilename, glyphs, encname=None):
        fullfont.fullfont(file, pfbfilename)
