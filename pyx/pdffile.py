# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2026 Jörg Lehmann <joerg@pyx-project.org>
# Copyright (C) 2026 André Wobst <wobsta@pyx-project.org>
#
# This file is part of PyX (https://pyx-project.org/).
#
# PyX is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# PyX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyX; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import hashlib, re, zlib
from . import baseclasses, bbox, config, pdfwriter, trafo, unit


_WHITESPACE = b"\x00\t\n\x0c\r "
_DELIMITERS = b"()<>[]{}/%"
_WHITESPACE_OR_DELIMITERS = _WHITESPACE + _DELIMITERS


class PDFname(str):
    pass


class PDFstring:

    def __init__(self, raw):
        self.raw = raw

    def __repr__(self):
        return f"PDFstring({self.raw!r})"

    def __eq__(self, other):
        return isinstance(other, PDFstring) and self.raw == other.raw


class PDFref:

    def __init__(self, num, gen=0):
        self.num = num
        self.gen = gen

    def __repr__(self):
        return f"PDFref({self.num}, {self.gen})"

    def __eq__(self, other):
        return isinstance(other, PDFref) and self.num == other.num and self.gen == other.gen

    def __hash__(self):
        return hash((self.num, self.gen))


class PDFstream:

    def __init__(self, d, data):
        self.dict = dict(d)
        self.dict["Length"] = len(data)
        self.data = data

    def decoded(self):
        fltr = self.dict.get("Filter")
        if not fltr:
            return self.data
        filters = fltr if isinstance(fltr, list) else [fltr]
        parms = self.dict.get("DecodeParms")
        parms_list = parms if isinstance(parms, list) else [parms] * len(filters)
        data = self.data
        for f, p in zip(filters, parms_list):
            if f == "FlateDecode":
                data = zlib.decompress(data)
                if isinstance(p, dict) and p.get("Predictor", 1) >= 10:
                    columns = p.get("Columns", 1)
                    rowlen = columns + 1
                    rows = len(data) // rowlen
                    out = bytearray(columns * rows)
                    prev = bytearray(columns)
                    for r in range(rows):
                        row = data[r * rowlen:(r + 1) * rowlen]
                        pred = row[0]
                        cur = bytearray(row[1:])
                        if pred == 2:
                            for i in range(columns):
                                cur[i] = (cur[i] + prev[i]) & 0xff
                        out[r * columns:(r + 1) * columns] = cur
                        prev = cur
                    data = bytes(out)
            else:
                raise ValueError(f"unsupported filter {f}")
        return data


class PDFparser:

    def __init__(self, data, pos=0):
        self.data = data
        self.pos = pos
        self.length = len(data)

    def skip_ws(self):
        data = self.data
        pos = self.pos
        length = self.length
        while pos < length:
            b = data[pos]
            if b in _WHITESPACE:
                pos += 1
            elif b == 37: # %
                while pos < length and data[pos] not in b"\r\n":
                    pos += 1
            else:
                break
        self.pos = pos

    def peek_token(self):
        saved = self.pos
        tok = self.next_token()
        self.pos = saved
        return tok

    def next_token(self):
        self.skip_ws()
        if self.pos >= self.length:
            return None
        data = self.data
        b = data[self.pos]
        if b in b"[]":
            self.pos += 1
            return bytes([b])
        if b == 47: # /
            start = self.pos + 1
            self.pos = start
            while self.pos < self.length and data[self.pos] not in _WHITESPACE_OR_DELIMITERS:
                self.pos += 1
            raw = data[start:self.pos].decode("latin1")
            name = re.sub(r"#([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), raw)
            return PDFname(name)
        if b == 40: # (
            start = self.pos
            self.pos += 1
            depth = 1
            while self.pos < self.length and depth > 0:
                c = data[self.pos]
                if c == 92: # \
                    self.pos += 2
                    continue
                if c == 40:
                    depth += 1
                elif c == 41:
                    depth -= 1
                self.pos += 1
            return PDFstring(data[start:self.pos])
        if b == 60: # <
            if self.pos + 1 < self.length and data[self.pos + 1] == 60:
                self.pos += 2
                return b"<<"
            start = self.pos
            self.pos += 1
            while self.pos < self.length and data[self.pos] != 62:
                self.pos += 1
            self.pos += 1
            return PDFstring(data[start:self.pos])
        if b == 62: # >
            if self.pos + 1 < self.length and data[self.pos + 1] == 62:
                self.pos += 2
                return b">>"
            self.pos += 1
            return b">"
        start = self.pos
        while self.pos < self.length and data[self.pos] not in _WHITESPACE_OR_DELIMITERS:
            self.pos += 1
        return data[start:self.pos]

    def read_object(self, pdfdoc=None):
        tok = self.next_token()
        if tok is None:
            return None
        if isinstance(tok, (PDFname, PDFstring)):
            return tok
        if tok == b"[":
            arr = []
            while True:
                if self.peek_token() == b"]":
                    self.next_token()
                    return arr
                arr.append(self.read_object(pdfdoc))
        if tok == b"<<":
            d = {}
            while True:
                if self.peek_token() == b">>":
                    self.next_token()
                    break
                key = self.read_object(pdfdoc)
                val = self.read_object(pdfdoc)
                d[key] = val
            saved = self.pos
            next_tok = self.next_token()
            if next_tok == b"stream":
                if self.pos < self.length and self.data[self.pos] == 13: # \r
                    self.pos += 1
                if self.pos < self.length and self.data[self.pos] == 10: # \n
                    self.pos += 1
                length = d["Length"]
                if isinstance(length, PDFref) and pdfdoc is not None:
                    length = pdfdoc.get_object(length)
                stream_data = self.data[self.pos:self.pos + length]
                self.pos += length
                end_tok = self.next_token()
                if end_tok != b"endstream":
                    raise ValueError("expected endstream")
                return PDFstream(d, stream_data)
            self.pos = saved
            return d
        if tok == b"true":
            return True
        if tok == b"false":
            return False
        if tok == b"null":
            return None
        try:
            num = int(tok)
        except ValueError:
            try:
                return float(tok)
            except ValueError:
                return tok
        saved = self.pos
        tok2 = self.next_token()
        if isinstance(tok2, bytes):
            try:
                gen = int(tok2)
                if self.next_token() == b"R":
                    return PDFref(num, gen)
            except ValueError:
                pass
        self.pos = saved
        return num


class PDFreader:

    """reads and parses a PDF file"""

    def __init__(self, file):
        """initializes PDFreader from a binary file-like object"""
        self.data = file.read()
        self.xref = {}
        self.cache = {}
        self.trailer = self._read_xref_and_trailer()

    def _read_xref_and_trailer(self):
        idx = self.data.rfind(b"startxref")
        if idx == -1:
            raise ValueError("startxref not found")
        parser = PDFparser(self.data, idx + len(b"startxref"))
        xref_pos = parser.read_object()
        trailer = {}
        visited = set()
        while xref_pos is not None and xref_pos not in visited:
            visited.add(xref_pos)
            t = self._parse_xref_at(xref_pos)
            for k, v in t.items():
                trailer.setdefault(k, v)
            xref_pos = t.get("Prev")
        return trailer

    def _parse_xref_at(self, pos):
        parser = PDFparser(self.data, pos)
        tok = parser.next_token()
        if tok == b"xref":
            while True:
                peek = parser.peek_token()
                if peek == b"trailer":
                    parser.next_token()
                    return parser.read_object(self)
                start_num = int(parser.next_token())
                count = int(parser.next_token())
                parser.skip_ws()
                for i in range(count):
                    line = self.data[parser.pos:parser.pos + 20]
                    parser.pos += 20
                    offset = int(line[:10])
                    gen = int(line[11:16])
                    flag = line[17:18]
                    if flag == b"n":
                        self.xref.setdefault((start_num + i, gen), ("offset", offset))
        else:
            gen = int(parser.next_token())
            if parser.next_token() != b"obj":
                raise ValueError("invalid xref stream")
            xref_stream = parser.read_object(self)
            d = xref_stream.dict
            w0, w1, w2 = d["W"]
            entry_len = w0 + w1 + w2
            size = d["Size"]
            index = d.get("Index", [0, size])
            raw = xref_stream.decoded()
            offset_in_raw = 0
            for i in range(0, len(index), 2):
                start_num, count = index[i], index[i + 1]
                for obj_num in range(start_num, start_num + count):
                    entry = raw[offset_in_raw:offset_in_raw + entry_len]
                    offset_in_raw += entry_len
                    t = int.from_bytes(entry[:w0], "big") if w0 else 1
                    f1 = int.from_bytes(entry[w0:w0 + w1], "big") if w1 else 0
                    f2 = int.from_bytes(entry[w0 + w1:], "big") if w2 else 0
                    if t == 1:
                        self.xref.setdefault((obj_num, f2), ("offset", f1))
                    elif t == 2:
                        self.xref.setdefault((obj_num, 0), ("objstm", f1, f2))
            return d

    def get_object(self, ref):
        """resolves and returns the PDF object for an indirect reference ref,
        or returns ref unchanged if it is already a direct object"""
        if not isinstance(ref, PDFref):
            return ref
        key = (ref.num, ref.gen)
        if key in self.cache:
            return self.cache[key]
        info = self.xref.get(key)
        if info is None:
            return None
        if info[0] == "offset":
            parser = PDFparser(self.data, info[1])
            parser.next_token() # objnum
            parser.next_token() # gennum
            if parser.next_token() != b"obj":
                raise ValueError(f"expected 'obj' at offset {info[1]}")
            obj = parser.read_object(self)
            self.cache[key] = obj
            return obj
        if info[0] == "objstm":
            stm = self.get_object(PDFref(info[1], 0))
            raw = stm.decoded()
            first = stm.dict["First"]
            n = stm.dict["N"]
            header_parser = PDFparser(raw[:first], 0)
            offsets = []
            for _ in range(n):
                onum = header_parser.read_object()
                ooff = header_parser.read_object()
                offsets.append((onum, first + ooff))
            obj_parser = PDFparser(raw, offsets[info[2]][1])
            obj = obj_parser.read_object(self)
            self.cache[key] = obj
            return obj

    def get_page(self, pageno=1):
        """returns the resolved page dictionary (including inherited attributes)
        for 1-based page number pageno"""
        root = self.get_object(self.trailer["Root"])
        pages_node = self.get_object(root["Pages"])
        pages = []

        def walk(node, inherited):
            cur = dict(inherited)
            for k in ("Resources", "MediaBox", "CropBox", "Rotate"):
                if k in node:
                    cur[k] = node[k]
            ntype = node.get("Type")
            if ntype == "Page":
                merged = dict(cur)
                merged.update(node)
                pages.append(merged)
            elif ntype == "Pages":
                for kid_ref in node.get("Kids", []):
                    kid = self.get_object(kid_ref)
                    walk(kid, cur)

        walk(pages_node, {})
        if not (1 <= pageno <= len(pages)):
            raise ValueError(f"page {pageno} out of range (1..{len(pages)})")
        return pages[pageno - 1]

    def get_page_bbox(self, pageno=1):
        """returns the bounding box (CropBox or MediaBox) of 1-based page pageno"""
        page = self.get_page(pageno)
        box = self.get_object(page.get("CropBox") or page.get("MediaBox"))
        llx, lly, urx, ury = [float(self.get_object(v)) for v in box]
        return bbox.bbox_pt(llx, lly, urx, ury)


def _format_pdfname(name):
    out = ["/"]
    for ch in name:
        code = ord(ch)
        if code < 33 or code > 126 or ch in "#()<>[]{}/%":
            out.append("#%02x" % code)
        else:
            out.append(ch)
    return "".join(out)


def _register_refs(obj, reader, file_id, registry):
    if isinstance(obj, PDFref):
        PDFcopiedobject(reader, file_id, obj).register(registry)
    elif isinstance(obj, list):
        for item in obj:
            _register_refs(item, reader, file_id, registry)
    elif isinstance(obj, dict):
        for val in obj.values():
            _register_refs(val, reader, file_id, registry)
    elif isinstance(obj, PDFstream):
        _register_refs(obj.dict, reader, file_id, registry)


def _write_pdfobject(file, obj, reader, file_id, registry):
    if obj is None:
        file.write("null")
    elif isinstance(obj, bool):
        file.write("true" if obj else "false")
    elif isinstance(obj, int):
        file.write("%i" % obj)
    elif isinstance(obj, float):
        s = ("%f" % obj).rstrip("0").rstrip(".")
        file.write(s or "0")
    elif isinstance(obj, PDFname):
        file.write(_format_pdfname(obj))
    elif isinstance(obj, PDFstring):
        file.write_bytes(obj.raw)
    elif isinstance(obj, PDFref):
        copied = PDFcopiedobject(reader, file_id, obj)
        file.write("%i 0 R" % registry.getrefno(copied))
    elif isinstance(obj, list):
        file.write("[")
        for i, item in enumerate(obj):
            if i:
                file.write(" ")
            _write_pdfobject(file, item, reader, file_id, registry)
        file.write("]")
    elif isinstance(obj, dict):
        file.write("<<\n")
        for k, v in obj.items():
            file.write("%s " % _format_pdfname(k))
            _write_pdfobject(file, v, reader, file_id, registry)
            file.write("\n")
        file.write(">>")
    elif isinstance(obj, PDFstream):
        _write_pdfobject(file, obj.dict, reader, file_id, registry)
        file.write("\nstream\n")
        file.write_bytes(obj.data)
        if not obj.data.endswith(b"\n"):
            file.write("\n")
        file.write("endstream")
    else:
        raise TypeError(f"unsupported PDF object {obj!r}")


class PDFcopiedobject(pdfwriter.PDFobject):

    def __init__(self, reader, file_id, ref):
        super().__init__("pdfcopiedobject", _id=(file_id, ref.num, ref.gen))
        self.reader = reader
        self.file_id = file_id
        self.ref = ref
        self.obj = None

    def register(self, registry):
        if self not in registry:
            self.obj = self.reader.get_object(self.ref)
            registry.add(self)
            _register_refs(self.obj, self.reader, self.file_id, registry)

    def write(self, file, writer, registry):
        if self.obj is None:
            self.obj = self.reader.get_object(self.ref)
        _write_pdfobject(file, self.obj, self.reader, self.file_id, registry)
        file.write("\n")


class PDFformxobject(pdfwriter.PDFobject):

    def __init__(self, name, reader, file_id, pageno, registry, bbox=None):
        super().__init__("pdfformxobject", _id=name)
        self.name = name
        self.reader = reader
        self.file_id = file_id
        self.pageno = pageno
        self.page = reader.get_page(pageno)
        self.bbox = bbox if bbox is not None else reader.get_page_bbox(pageno)
        self.resources = self.page.get("Resources", {})
        self.group = self.page.get("Group")
        self.contents = self._extract_contents()
        registry.addresource("XObject", name, self)
        _register_refs(self.resources, reader, file_id, registry)
        if self.group is not None:
            _register_refs(self.group, reader, file_id, registry)

    def _extract_contents(self):
        contents = self.reader.get_object(self.page.get("Contents"))
        if contents is None:
            return b""
        if isinstance(contents, PDFstream):
            return contents.decoded()
        if isinstance(contents, list):
            return b"\n".join(self.reader.get_object(c).decoded() for c in contents)
        raise ValueError("invalid page Contents")

    def write(self, file, writer, registry):
        if writer.compress:
            content = zlib.compress(self.contents)
        else:
            content = self.contents
        file.write("<<\n"
                   "/Type /XObject\n"
                   "/Subtype /Form\n"
                   "/BBox [%f %f %f %f]\n" % self.bbox.highrestuple_pt())
        if self.group is not None:
            file.write("/Group ")
            _write_pdfobject(file, self.group, self.reader, self.file_id, registry)
            file.write("\n")
        file.write("/Resources ")
        _write_pdfobject(file, self.resources, self.reader, self.file_id, registry)
        file.write("\n"
                   "/Length %i\n" % len(content))
        if writer.compress:
            file.write("/Filter /FlateDecode\n")
        file.write(">>\n"
                   "stream\n")
        file.write_bytes(content)
        if not content.endswith(b"\n"):
            file.write("\n")
        file.write("endstream\n")


class pdffile(baseclasses.canvasitem):

    """class for pdffiles"""

    def __init__(self,
                 x, y, filename,
                 width=None, height=None, scale=None, align="bl",
                 clip=1, translatebbox=True, bbox=None,
                 page=1, kpsearch=False):
        """inserts pdffile

        Object for a PDF file named filename at position (x,y). Width, height,
        scale and alignment can be adjusted by the corresponding parameters. If
        clip is set, the result gets clipped to the bbox of the PDF page. If
        translatebbox is not set, the PDF graphics is not translated to the
        corresponding origin. If bbox is not None, it overrides the bounding
        box in the pdffile itself. page selects the 1-based page number of the
        PDF file to include. If kpsearch is set then filename is searched using
        the kpathsea library.
        """

        self.x_pt = unit.topt(x)
        self.y_pt = unit.topt(y)
        self.filename = filename
        self.page = page
        self.kpsearch = kpsearch
        with self.open() as f:
            self.reader = PDFreader(f)
        self.filehash = hashlib.sha1(self.reader.data).hexdigest()[:15]
        if bbox:
            self.mybbox = bbox
        else:
            self.mybbox = self.reader.get_page_bbox(self.page)

        self.scalex = self.scaley = scale

        if width is not None or height is not None:
            if scale is not None:
                raise ValueError("cannot set both width and/or height and scale simultaneously")
            if height is not None:
                self.scaley = unit.topt(height) / (self.mybbox.ury_pt - self.mybbox.lly_pt)
            if width is not None:
                self.scalex = unit.topt(width) / (self.mybbox.urx_pt - self.mybbox.llx_pt)

            if self.scalex is None:
                self.scalex = self.scaley
            if self.scaley is None:
                self.scaley = self.scalex

        self.width_pt = self.mybbox.urx_pt - self.mybbox.llx_pt
        if self.scalex:
            self.width_pt *= self.scalex

        self.height_pt = self.mybbox.ury_pt - self.mybbox.lly_pt
        if self.scaley:
            self.height_pt *= self.scaley

        self.align = align
        if self.align[0] == "b":
            pass
        elif self.align[0] == "c":
            self.y_pt -= self.height_pt / 2.0
        elif self.align[0] == "t":
            self.y_pt -= self.height_pt
        else:
            raise ValueError("vertical alignment can only be b (bottom), c (center), or t (top)")

        if self.align[1] == "l":
            pass
        elif self.align[1] == "c":
            self.x_pt -= self.width_pt / 2.0
        elif self.align[1] == "r":
            self.x_pt -= self.width_pt
        else:
            raise ValueError("horizontal alignment can only be l (left), c (center), or r (right)")

        self.clip = clip
        self.translatebbox = translatebbox

        self.trafo = trafo.translate_pt(self.x_pt, self.y_pt)

        if self.scalex is not None:
            self.trafo = self.trafo * trafo.scale_pt(self.scalex, self.scaley)

        if translatebbox:
            self.trafo = self.trafo * trafo.translate_pt(-self.mybbox.llx_pt, -self.mybbox.lly_pt)

    def open(self):
        """opens the PDF file for binary reading"""
        if hasattr(self.filename, "read"):
            return self.filename
        if self.kpsearch:
            return config.open(self.filename, [config.format.pict])
        return open(self.filename, "rb")

    def bbox(self):
        """returns bounding box of the pdffile canvasitem"""
        return self.mybbox.transformed(self.trafo)

    def processPDF(self, file, writer, context, registry, bbox):
        """processes the pdffile for PDF output by registering its Form XObject
        and writing the placement operators to file"""
        name = "pdffile-%s-p%i" % (self.filehash, self.page)
        formbbox = self.mybbox if self.clip else (self.reader.get_page_bbox(self.page) + self.mybbox)
        registry.add(PDFformxobject(name, self.reader, self.filehash, self.page, registry, bbox=formbbox))
        bbox += self.bbox()

        file.write("q\n")
        if self.clip:
            llx_pt, lly_pt, urx_pt, ury_pt = self.mybbox.transformed(self.trafo).highrestuple_pt()
            file.write("%f %f %f %f re W n\n" % (llx_pt, lly_pt, urx_pt - llx_pt, ury_pt - lly_pt))
        self.trafo.processPDF(file, writer, context, registry)
        file.write("/%s Do\n" % name)
        file.write("Q\n")
