# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2004-2011 André Wobst <wobsta@users.sourceforge.net>
# Copyright (C) 2011 Michael Schindler<m-schindler@users.sourceforge.net>
#
# This file is part of PyX (http://pyx.sourceforge.net/).
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

import struct, warnings, binascii
try:
    import zlib
    haszlib = 1
except:
    haszlib = 0

import bbox, canvasitem, pswriter, pdfwriter, trafo, unit

devicenames = {"L": "/DeviceGray",
               "RGB": "/DeviceRGB",
               "CMYK": "/DeviceCMYK"}
decodestrings = {"L": "[0 1]",
                 "RGB": "[0 1 0 1 0 1]",
                 "CMYK": "[0 1 0 1 0 1 0 1]",
                 "P": "[0 255]"}


def ascii85lines(datalen):
    if datalen < 4:
        return 1
    return (datalen + 56)/60

def ascii85stream(file, data):
    """Encodes the string data in ASCII85 and writes it to
    the stream file. The number of lines written to the stream
    is known just from the length of the data by means of the
    ascii85lines function. Note that the tailing newline character
    of the last line is not added by this function, but it is taken
    into account in the ascii85lines function."""
    i = 3 # go on smoothly in case of data length equals zero
    l = 0
    l = [None, None, None, None]
    for i in range(len(data)):
        c = data[i]
        l[i%4] = ord(c)
        if i%4 == 3:
            if i%60 == 3 and i != 3:
                file.write("\n")
            if l:
                # instead of
                # l[3], c5 = divmod(256*256*256*l[0]+256*256*l[1]+256*l[2]+l[3], 85)
                # l[2], c4 = divmod(l[3], 85)
                # we have to avoid number > 2**31 by
                l[3], c5 = divmod(256*256*l[0]+256*256*l[1]+256*l[2]+l[3], 85)
                l[2], c4 = divmod(256*256*3*l[0]+l[3], 85)
                l[1], c3 = divmod(l[2], 85)
                c1  , c2 = divmod(l[1], 85)
                file.write(struct.pack('BBBBB', c1+33, c2+33, c3+33, c4+33, c5+33))
            else:
                file.write("z")
    if i%4 != 3:
        for j in range((i%4) + 1, 4):
            l[j] = 0
        l[3], c5 = divmod(256*256*l[0]+256*256*l[1]+256*l[2]+l[3], 85)
        l[2], c4 = divmod(256*256*3*l[0]+l[3], 85)
        l[1], c3 = divmod(l[2], 85)
        c1  , c2 = divmod(l[1], 85)
        file.write(struct.pack('BBBB', c1+33, c2+33, c3+33, c4+33)[:(i%4)+2])

_asciihexlinelength = 64
def asciihexlines(datalen):
    return (datalen*2 + _asciihexlinelength - 1) / _asciihexlinelength

def asciihexstream(file, data):
    hexdata = binascii.b2a_hex(data)
    for i in range((len(hexdata)-1)/_asciihexlinelength + 1):
        file.write(hexdata[i*_asciihexlinelength: i*_asciihexlinelength+_asciihexlinelength])
        file.write("\n")


class image:

    def __init__(self, width, height, mode, data, compressed=None, palette=None):
        if width <= 0 or height <= 0:
            raise ValueError("valid image size")
        if mode not in ["L", "RGB", "CMYK", "LA", "RGBA", "CMYKA", "AL", "ARGB", "ACMYK"]:
            raise ValueError("invalid mode")
        if compressed is None and len(mode)*width*height != len(data):
            raise ValueError("wrong size of uncompressed data")
        self.size = width, height
        self.mode = mode
        self.data = data
        self.compressed = compressed
        self.palette = palette

    def split(self):
        if self.compressed is not None:
            raise RuntimeError("cannot extract bands from compressed image")
        bands = len(self.mode)
        width, height = self.size
        return [image(width, height, "L", "".join([self.data[i*bands+band]
                                                             for i in range(width*height)]))
                for band in range(bands)]

    def tostring(self, *args):
        if len(args):
            raise RuntimeError("encoding not supported in this implementation")
        return self.data

    def convert(self, model):
        raise RuntimeError("color model conversion not supported in this implementation")


class jpegimage(image):

    def __init__(self, file):
        try:
            data = file.read()
        except:
            data = open(file, "rb").read()
        pos = 0
        nestinglevel = 0
        try:
            while 1:
                if data[pos] == "\377" and data[pos+1] not in ["\0", "\377"]:
                    # print "marker: 0x%02x \\%03o" % (ord(data[pos+1]), ord(data[pos+1]))
                    if data[pos+1] == "\330":
                        if not nestinglevel:
                            begin = pos
                        nestinglevel += 1
                    elif not nestinglevel:
                        raise ValueError("begin marker expected")
                    elif data[pos+1] == "\331":
                        nestinglevel -= 1
                        if not nestinglevel:
                            end = pos + 2
                            break
                    elif data[pos+1] in ["\300", "\301"]:
                        l, bits, height, width, components = struct.unpack(">HBHHB", data[pos+2:pos+10])
                        if bits != 8:
                            raise ValueError("implementation limited to 8 bit per component only")
                        try:
                            mode = {1: "L", 3: "RGB", 4: "CMYK"}[components]
                        except KeyError:
                            raise ValueError("invalid number of components")
                        pos += l+1
                    elif data[pos+1] == "\340":
                        l, id, major, minor, dpikind, xdpi, ydpi = struct.unpack(">H5sBBBHH", data[pos+2:pos+16])
                        if dpikind == 1:
                            self.info = {"dpi": (xdpi, ydpi)}
                        elif dpikind == 2:
                            self.info = {"dpi": (xdpi*2.54, ydpi*2.45)}
                        # else do not provide dpi information
                        pos += l+1
                pos += 1
        except IndexError:
            raise ValueError("end marker expected")
        image.__init__(self, width, height, mode, data[begin:end], compressed="DCT")


class PSimagedata(pswriter.PSresource):

    def __init__(self, name, data, singlestring, maxstrlen):
        pswriter.PSresource.__init__(self, "imagedata", name)
        self.data = data
        self.singlestring = singlestring
        self.maxstrlen = maxstrlen

    def output(self, file, writer, registry):
        file.write("%%%%BeginRessource: %s\n" % self.id)
        if self.singlestring:
            file.write("%%%%BeginData: %i ASCII Lines\n"
                       "<~" % ascii85lines(len(self.data)))
            ascii85stream(file, self.data)
            file.write("~>\n"
                         "%%EndData\n")
        else:
            datalen = len(self.data)
            tailpos = datalen - datalen % self.maxstrlen
            file.write("%%%%BeginData: %i ASCII Lines\n" %
                       ((tailpos/self.maxstrlen) * ascii85lines(self.maxstrlen) +
                        ascii85lines(datalen-tailpos)))
            file.write("[ ")
            for i in xrange(0, tailpos, self.maxstrlen):
                file.write("<~")
                ascii85stream(file, self.data[i: i+self.maxstrlen])
                file.write("~>\n")
            if datalen != tailpos:
                file.write("<~")
                ascii85stream(file, self.data[tailpos:])
                file.write("~>")
            file.write("]\n"
                       "%%EndData\n")
        file.write("/%s exch def\n" % self.id)
        file.write("%%EndRessource\n")


class PDFimagepalettedata(pdfwriter.PDFobject):

    def __init__(self, name, data):
        pdfwriter.PDFobject.__init__(self, "imagepalettedata", name)
        self.data = data

    def write(self, file, writer, registry):
        file.write("<<\n"
                   "/Length %d\n" % len(self.data))
        file.write(">>\n"
                   "stream\n")
        file.write(self.data)
        file.write("\n"
                   "endstream\n")


class PDFimage(pdfwriter.PDFobject):

    def __init__(self, name, width, height, palettemode, palettedata, mode,
                       bitspercomponent, compressmode, data, smask, registry, addresource=True):
        pdfwriter.PDFobject.__init__(self, "image", name)

        if addresource:
            if palettedata is not None:
                procset = "ImageI"
            elif mode == "L":
                procset = "ImageB"
            else:
                procset = "ImageC"
            registry.addresource("XObject", name, self, procset=procset)
        if palettedata is not None:
            # note that acrobat wants a palette to be an object (which clearly is a bug)
            self.PDFpalettedata = PDFimagepalettedata(name, palettedata)
            registry.add(self.PDFpalettedata)

        self.name = name
        self.width = width
        self.height = height
        self.palettemode = palettemode
        self.palettedata = palettedata
        self.mode = mode
        self.bitspercomponent = bitspercomponent
        self.compressmode = compressmode
        self.data = data
        self.smask = smask

    def write(self, file, writer, registry):
        file.write("<<\n"
                   "/Type /XObject\n"
                   "/Subtype /Image\n"
                   "/Width %d\n" % self.width)
        file.write("/Height %d\n" % self.height)
        if self.palettedata is not None:
            file.write("/ColorSpace [ /Indexed %s %i\n" % (devicenames[self.palettemode], len(self.palettedata)/3-1))
            file.write("%d 0 R\n" % registry.getrefno(self.PDFpalettedata))
            file.write("]\n")
        else:
            file.write("/ColorSpace %s\n" % devicenames[self.mode])
        if self.smask:
            file.write("/SMask %d 0 R\n" % registry.getrefno(self.smask))
        file.write("/BitsPerComponent %d\n" % self.bitspercomponent)
        file.write("/Length %d\n" % len(self.data))
        if self.compressmode:
            file.write("/Filter /%sDecode\n" % self.compressmode)
        file.write(">>\n"
                   "stream\n")
        file.write(self.data)
        file.write("\n"
                   "endstream\n")


class bitmap_pt(canvasitem.canvasitem):

    def __init__(self, xpos_pt, ypos_pt, image, width_pt=None, height_pt=None, ratio=None,
                       PSstoreimage=0, PSmaxstrlen=4093, PSbinexpand=1,
                       compressmode="Flate", flatecompresslevel=6,
                       dctquality=75, dctoptimize=0, dctprogression=0):
        self.xpos_pt = xpos_pt
        self.ypos_pt = ypos_pt
        self.image = image

        self.imagewidth, self.imageheight = image.size

        if width_pt is not None or height_pt is not None:
            self.width_pt = width_pt
            self.height_pt = height_pt
            if self.width_pt is None:
                if ratio is None:
                    self.width_pt = self.height_pt * self.imagewidth / float(self.imageheight)
                else:
                    self.width_pt = ratio * self.height_pt
            elif self.height_pt is None:
                if ratio is None:
                    self.height_pt = self.width_pt * self.imageheight / float(self.imagewidth)
                else:
                    self.height_pt = (1.0/ratio) * self.width_pt
            elif ratio is not None:
                raise ValueError("can't specify a ratio when setting width_pt and height_pt")
        else:
            if ratio is not None:
                raise ValueError("must specify width_pt or height_pt to set a ratio")
            widthdpi, heightdpi = image.info["dpi"] # fails when no dpi information available
            self.width_pt = 72.0 * self.imagewidth / float(widthdpi)
            self.height_pt = 72.0 * self.imageheight / float(heightdpi)

        self.PSstoreimage = PSstoreimage
        self.PSmaxstrlen = PSmaxstrlen
        self.PSbinexpand = PSbinexpand
        self.compressmode = compressmode
        self.flatecompresslevel = flatecompresslevel
        self.dctquality = dctquality
        self.dctoptimize = dctoptimize
        self.dctprogression = dctprogression

        try:
            self.imagecompressed = image.compressed
        except:
            self.imagecompressed = None
        if self.compressmode not in [None, "Flate", "DCT"]:
            raise ValueError("invalid compressmode '%s'" % self.compressmode)
        if self.imagecompressed not in [None, "Flate", "DCT"]:
            raise ValueError("invalid compressed image '%s'" % self.imagecompressed)
        if self.compressmode is not None and self.imagecompressed is not None:
            raise ValueError("compression of a compressed image not supported")
        if not haszlib and self.compressmode == "Flate":
            warnings.warn("zlib module not available, disable compression")
            self.compressmode = None

    def imagedata(self, interleavealpha):
        """internal function

        returns a tuple (mode, data, alpha, palettemode, palettedata)
        where mode does not contain antialiasing anymore
        """

        alpha = palettemode = palettedata = None
        data = self.image
        mode = data.mode
        if mode.startswith("A"):
            mode = mode[1:]
            if interleavealpha:
                alpha = True
            else:
                bands = data.split()
                alpha = band[0]
                data = image(self.imagewidth, self.imageheight, mode,
                             "".join(["".join(values)
                                      for values in zip(*[band.tostring()
                                                          for band in bands[1:]])]), palette=data.palette)
        if mode.endswith("A"):
            bands = data.split()
            bands = list(bands[-1:]) + list(bands[:-1])
            mode = mode[:-1]
            if interleavealpha:
                alpha = True
                # TODO: this is slow, but we don't want to depend on PIL or anything ... still, its incredibly slow to do it with lists and joins
                data = image(self.imagewidth, self.imageheight, "A%s" % mode,
                             "".join(["".join(values)
                                      for values in zip(*[band.tostring()
                                                          for band in bands])]), palette=data.palette)
            else:
                alpha = bands[0]
                data = image(self.imagewidth, self.imageheight, mode,
                             "".join(["".join(values)
                                      for values in zip(*[band.tostring()
                                                          for band in bands[1:]])]), palette=data.palette)

        if mode == "P":
            palettemode, palettedata = data.palette.getdata()
            if palettemode not in ["L", "RGB", "CMYK"]:
                warnings.warn("image with unknown palette mode '%s' converted to rgb image" % palettemode)
                data = data.convert("RGB")
                mode = "RGB"
                palettemode = None
                palettedata = None
        elif len(mode) == 1:
            if mode != "L":
                warnings.warn("specific single channel image mode not natively supported, converted to regular grayscale")
                data = data.convert("L")
                mode = "L"
        elif mode not in ["CMYK", "RGB"]:
            warnings.warn("image with unknown mode converted to rgb")
            data = data.convert("RGB")
            mode = "RGB"

        if self.compressmode == "Flate":
            data = zlib.compress(data.tostring(), self.flatecompresslevel)
        elif self.compressmode == "DCT":
            data = data.tostring("jpeg", mode, self.dctquality, self.dctoptimize, self.dctprogression)
        else:
            data = data.tostring()
        if alpha and not interleavealpha:
            if self.compressmode == "Flate":
                alpha = zlib.compress(alpha.tostring(), self.flatecompresslevel)
            elif self.compressmode == "DCT":
                # well, this here is strange, we might want a alphacompressmode ...
                alpha = alpha.tostring("jpeg", mode, self.dctquality, self.dctoptimize, self.dctprogression)
            else:
                alpha = alpha.tostring()

        return mode, data, alpha, palettemode, palettedata

    def bbox(self):
        return bbox.bbox_pt(self.xpos_pt, self.ypos_pt,
                            self.xpos_pt+self.width_pt, self.ypos_pt+self.height_pt)

    def processPS(self, file, writer, context, registry, bbox):
        mode, data, alpha, palettemode, palettedata = self.imagedata(True)
        imagematrixPS = (trafo.mirror(0)
                         .translated_pt(-self.xpos_pt, self.ypos_pt+self.height_pt)
                         .scaled_pt(self.imagewidth/self.width_pt, self.imageheight/self.height_pt))


        PSsinglestring = self.PSstoreimage and len(data) < self.PSmaxstrlen
        if PSsinglestring:
            PSimagename = "image-%d-%s-singlestring" % (id(self.image), self.compressmode)
        else:
            PSimagename = "image-%d-%s-stringarray" % (id(self.image), self.compressmode)

        if self.PSstoreimage and not PSsinglestring:
            registry.add(pswriter.PSdefinition("imagedataaccess",
                                               "{ /imagedataindex load " # get list index
                                               "dup 1 add /imagedataindex exch store " # store increased index
                                               "/imagedataid load exch get }")) # select string from array
        if self.PSstoreimage:
            registry.add(PSimagedata(PSimagename, data, PSsinglestring, self.PSmaxstrlen))
        bbox += self.bbox()

        file.write("gsave\n")
        if palettedata is not None:
            file.write("[ /Indexed %s %i\n" % (devicenames[palettemode], len(palettedata)/3-1))
            file.write("%%%%BeginData: %i ASCII Lines\n" % ascii85lines(len(palettedata)))
            file.write("<~")
            ascii85stream(file, palettedata)
            file.write("~>\n"
                       "%%EndData\n")
            file.write("] setcolorspace\n")
        else:
            file.write("%s setcolorspace\n" % devicenames[mode])

        if self.PSstoreimage and not PSsinglestring:
            file.write("/imagedataindex 0 store\n" # not use the stack since interpreters differ in their stack usage
                       "/imagedataid %s store\n" % PSimagename)

        file.write("<<\n")
        if alpha:
            file.write("/ImageType 3\n"
                       "/DataDict\n"
                       "<<\n")
        file.write("/ImageType 1\n"
                   "/Width %i\n" % self.imagewidth)
        file.write("/Height %i\n" % self.imageheight)
        file.write("/BitsPerComponent 8\n"
                   "/ImageMatrix %s\n" % imagematrixPS)
        file.write("/Decode %s\n" % decodestrings[mode])

        file.write("/DataSource ")
        if self.PSstoreimage:
            if PSsinglestring:
                file.write("/%s load" % PSimagename)
            else:
                file.write("/imagedataaccess load") # some printers do not allow for inline code here -> we store it in a resource
        else:
            if self.PSbinexpand == 2:
                file.write("currentfile /ASCIIHexDecode filter")
            else:
                file.write("currentfile /ASCII85Decode filter")
        if self.compressmode or self.imagecompressed:
            file.write(" /%sDecode filter" % (self.compressmode or self.imagecompressed))
        file.write("\n")

        file.write(">>\n")

        if alpha:
            file.write("/MaskDict\n"
                       "<<\n"
                       "/ImageType 1\n"
                       "/Width %i\n" % self.imagewidth)
            file.write("/Height %i\n" % self.imageheight)
            file.write("/BitsPerComponent 8\n"
                       "/ImageMatrix %s\n" % imagematrixPS)
            file.write("/Decode [1 0]\n"
                       ">>\n"
                       "/InterleaveType 1\n"
                       ">>\n")

        if self.PSstoreimage:
            file.write("image\n")
        else:
            if self.PSbinexpand == 2:
                file.write("%%%%BeginData: %i ASCII Lines\n"
                           "image\n" % (asciihexlines(len(data)) + 1))
                asciihexstream(file, data)
            else:
                # the datasource is currentstream (plus some filters)
                file.write("%%%%BeginData: %i ASCII Lines\n"
                           "image\n" % (ascii85lines(len(data)) + 1))
                ascii85stream(file, data)
                file.write("~>\n")
            file.write("%%EndData\n")

        file.write("grestore\n")

    def processPDF(self, file, writer, context, registry, bbox):
        mode, data, alpha, palettemode, palettedata = self.imagedata(False)

        name = "image-%d-%s" % (id(self.image), self.compressmode or self.imagecompressed)
        if alpha:
            alpha = PDFimage("%s-smask" % name, self.imagewidth, self.imageheight,
                             None, None, "L", 8,
                             self.compressmode, alpha, None, registry, addresource=False)
            registry.add(alpha)
        registry.add(PDFimage(name, self.imagewidth, self.imageheight,
                              palettemode, palettedata, mode, 8,
                              self.compressmode or self.imagecompressed, data, alpha, registry))

        bbox += self.bbox()
        imagematrixPDF = (trafo.scale_pt(self.width_pt, self.height_pt)
                          .translated_pt(self.xpos_pt, self.ypos_pt))

        file.write("q\n")
        imagematrixPDF.processPDF(file, writer, context, registry, bbox)
        file.write("/%s Do\n" % name)
        file.write("Q\n")


class bitmap(bitmap_pt):

    def __init__(self, xpos, ypos, image, width=None, height=None, **kwargs):
        xpos_pt = unit.topt(xpos)
        ypos_pt = unit.topt(ypos)
        if width is not None:
            width_pt = unit.topt(width)
        else:
            width_pt = None
        if height is not None:
            height_pt = unit.topt(height)
        else:
            height_pt = None

        bitmap_pt.__init__(self, xpos_pt, ypos_pt, image, width_pt=width_pt, height_pt=height_pt, **kwargs)
