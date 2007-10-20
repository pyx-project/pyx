class ENCfile:

    def __init__(self, filename):
        encfile = open(filename, "r")
        encdata = encfile.read()
        encfile.close()

        t = reader.PStokenizer(encdata, "")

        self.encname = t.gettoken()
        token = t.gettoken()
        if token != "[":
            raise RuntimeError("cannot parse encoding file '%s', expecting '[' got '%s'" % (filename, token))
        self.encvector = []
        for i in range(256):
            token = t.gettoken()
            if token == "]":
                raise RuntimeError("not enough charcodes in encoding file '%s'" % filename)
            self.encvector.append(token)
        if t.gettoken() != "]":
            raise RuntimeError("too many charcodes in encoding file '%s'" % filename)
        token = t.gettoken()
        if token != "def":
            raise RuntimeError("cannot parse encoding file '%s', expecting 'def' got '%s'" % (filename, token))

