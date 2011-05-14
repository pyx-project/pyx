from pyx import reader

class ENFfileError(Exception):
    pass

class ENCfile:

    def __init__(self, bytes):
        c = reader.PStokenizer(bytes, "")

        # name of encoding
        self.name = c.gettoken()
        token = c.gettoken()
        if token != "[":
            raise ENCfileError("cannot parse encoding file '%s', expecting '[' got '%s'" % (filename, token))
        self.vector = []
        for i in range(256):
            token = c.gettoken()
            if token == "]":
                raise ENCfileError("not enough charcodes in encoding file '%s'" % filename)
            if not token[0] == "/":
                raise ENCfileError("token does not start with / in encoding file '%s'" % filename)
            self.vector.append(token[1:])
        if c.gettoken() != "]":
            raise ENCfileError("too many charcodes in encoding file '%s'" % filename)
        token = c.gettoken()
        if token != "def":
            raise ENCfileError("cannot parse encoding file '%s', expecting 'def' got '%s'" % (filename, token))

