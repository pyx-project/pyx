try:
    import _t1strip
    t1strip = _t1strip.t1strip
except:
    import os, tempfile
    def t1strip(file, pfbfilename, glyphs, encname=None):
        tmpfilename = tempfile.mktemp(suffix=".pfa")
        os.system("pfb2pfa %s %s" % (pfbfilename, tmpfilename))
        pfa = open(tmpfilename, "r")
        file.write(pfa.read())
        pfa.close()
        os.unlink(tmpfilename)
