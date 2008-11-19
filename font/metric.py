class metric:

    def width_ds(self, glyphname):
        raise NotImplementedError()

    def width_pt(self, glyphnames, size):
        raise NotImplementedError()

    def height_pt(self, glyphnames, size):
        raise NotImplementedError()

    def depth_pt(self, glyphnames, size):
        raise NotImplementedError()

    def resolveligatures(self, glyphnames):
        return glyphnames

    def resolvekernings(self, glyphnames, size=None):
        result = [None]*(2*len(glyphnames)-1)
        for i, glyphname in enumerate(glyphnames):
            result[2*i] = glyphname
        return result
