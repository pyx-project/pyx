try:
    import _pykpathsea
    find_file = _pykpathsea.find_file
except:
    import os
    def find_file(filename):
        return os.popen("kpsewhich %s" % filename, "r").readline()[:-1]
