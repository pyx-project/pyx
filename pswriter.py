# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2005-2006 J�rg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2005-2006 Andr� Wobst <wobsta@users.sourceforge.net>
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

import cStringIO, copy, time, math
import bbox, config, style, version, unit, trafo


class PSregistry:

    def __init__(self):
        # in order to keep a consistent order of the registered resources we
        # not only store them in a hash but also keep an ordered list (up to a
        # possible merging of resources, in which case the first instance is
        # kept)
        self.resourceshash = {}
        self.resourceslist = []

    def add(self, resource):
        rkey = (resource.type, resource.id)
        if self.resourceshash.has_key(rkey):
           self.resourceshash[rkey].merge(resource)
        else:
           self.resourceshash[rkey] = resource
           self.resourceslist.append(resource)

    def mergeregistry(self, registry):
        for resource in registry.resources:
            self.add(resource)

    def output(self, file, writer):
        """ write all PostScript code of the prolog resources """
        for resource in self.resourceslist:
            resource.output(file, writer, self)

#
# Abstract base class
#

class PSresource:

    """ a PostScript resource """

    def __init__(self, type, id):
        # Every PSresource has to have a type and a unique id.
        # Resources with the same type and id will be merged
        # when they are registered in the PSregistry
        self.type = type
        self.id = id

    def merge(self, other):
        """ merge self with other, which has to be a resource of the same type and with
        the same id"""
        pass

    def output(self, file, writer, registry):
        raise NotImplementedError("output not implemented for %s" % repr(self))

class PSdefinition(PSresource):

    """ PostScript function definition included in the prolog """

    def __init__(self, id, body):
        self.type = "definition"
        self.id = id
        self.body = body

    def output(self, file, writer, registry):
        file.write("%%%%BeginRessource: %s\n" % self.id)
        file.write("%(body)s /%(id)s exch def\n" % self.__dict__)
        file.write("%%EndRessource\n")

#
# Writers
#

class _PSwriter:

    def __init__(self, title=None, strip_fonts=1, text_as_path=0, mesh_as_bitmap=0, mesh_as_bitmap_resolution=300):
        self._fontmap = None
        self.title = title
        self.strip_fonts = strip_fonts
        self.text_as_path = text_as_path
        self.mesh_as_bitmap = mesh_as_bitmap
        self.mesh_as_bitmap_resolution = mesh_as_bitmap_resolution

        # dictionary mapping font names to dictionaries mapping encoding names to encodings
        # encodings themselves are mappings from glyphnames to codepoints
        self.encodings = {}

    def writeinfo(self, file):
        file.write("%%%%Creator: PyX %s\n" % version.version)
        if self.title is not None:
            file.write("%%%%Title: %s\n" % self.title)
        file.write("%%%%CreationDate: %s\n" %
                   time.asctime(time.localtime(time.time())))

    def getfontmap(self):
        if self._fontmap is None:
            # late import due to cyclic dependency
            from pyx.dvi import mapfile
            fontmapfiles = config.getlist("text", "psfontmaps", ["psfonts.map"])
            self._fontmap = mapfile.readfontmap(fontmapfiles)
        return self._fontmap


class EPSwriter(_PSwriter):

    def __init__(self, document, file, **kwargs):
        _PSwriter.__init__(self, **kwargs)

        if len(document.pages) != 1:
            raise ValueError("EPS file can be constructed out of a single page document only")
        page = document.pages[0]
        canvas = page.canvas

        pagefile = cStringIO.StringIO()
        registry = PSregistry()
        acontext = context()
        pagebbox = bbox.empty()

        page.processPS(pagefile, self, acontext, registry, pagebbox)

        file.write("%!PS-Adobe-3.0 EPSF-3.0\n")
        if pagebbox:
            file.write("%%%%BoundingBox: %d %d %d %d\n" % pagebbox.lowrestuple_pt())
            file.write("%%%%HiResBoundingBox: %g %g %g %g\n" % pagebbox.highrestuple_pt())
        self.writeinfo(file)
        file.write("%%EndComments\n")

        file.write("%%BeginProlog\n")
        registry.output(file, self)
        file.write("%%EndProlog\n")

        file.write(pagefile.getvalue())
        pagefile.close()

        file.write("showpage\n")
        file.write("%%Trailer\n")
        file.write("%%EOF\n")


class PSwriter(_PSwriter):

    def __init__(self, document, file, writebbox=0, **kwargs):
        _PSwriter.__init__(self, **kwargs)

        # We first have to process the content of the pages, writing them into the stream pagesfile
        # Doing so, we fill the registry and also calculate the page bounding boxes, which are
        # stored in page._bbox for every page
        pagesfile = cStringIO.StringIO()
        registry = PSregistry()

        # calculated bounding boxes of the whole document
        documentbbox = bbox.empty()

        for nr, page in enumerate(document.pages):
            # process contents of page
            pagefile = cStringIO.StringIO()
            acontext = context()
            pagebbox = bbox.empty()
            page.processPS(pagefile, self, acontext, registry, pagebbox)

            documentbbox += pagebbox

            pagesfile.write("%%%%Page: %s %d\n" % (page.pagename is None and str(nr+1) or page.pagename, nr+1))
            if page.paperformat:
                pagesfile.write("%%%%PageMedia: %s\n" % page.paperformat.name)
            pagesfile.write("%%%%PageOrientation: %s\n" % (page.rotated and "Landscape" or "Portrait"))
            if pagebbox and writebbox:
                pagesfile.write("%%%%PageBoundingBox: %d %d %d %d\n" % pagebbox.lowrestuple_pt())

            # page setup section
            pagesfile.write("%%BeginPageSetup\n")
            pagesfile.write("/pgsave save def\n")

            pagesfile.write("%%EndPageSetup\n")
            pagesfile.write(pagefile.getvalue())
            pagefile.close()
            pagesfile.write("pgsave restore\n")
            pagesfile.write("showpage\n")
            pagesfile.write("%%PageTrailer\n")

        file.write("%!PS-Adobe-3.0\n")
        if documentbbox and writebbox:
            file.write("%%%%BoundingBox: %d %d %d %d\n" % documentbbox.lowrestuple_pt())
            file.write("%%%%HiResBoundingBox: %g %g %g %g\n" % documentbbox.highrestuple_pt())
        self.writeinfo(file)

        # required paper formats
        paperformats = {}
        for page in document.pages:
            if page.paperformat:
                paperformats[page.paperformat] = page.paperformat

        first = 1
        for paperformat in paperformats.values():
            if first:
                file.write("%%DocumentMedia: ")
                first = 0
            else:
                file.write("%%+ ")
            file.write("%s %d %d 75 white ()\n" % (paperformat.name,
                                                   unit.topt(paperformat.width),
                                                   unit.topt(paperformat.height)))

        # file.write(%%DocumentNeededResources: ") # register not downloaded fonts here

        file.write("%%%%Pages: %d\n" % len(document.pages))
        file.write("%%PageOrder: Ascend\n")
        file.write("%%EndComments\n")

        # document defaults section
        #file.write("%%BeginDefaults\n")
        #file.write("%%EndDefaults\n")

        # document prolog section
        file.write("%%BeginProlog\n")
        registry.output(file, self)
        file.write("%%EndProlog\n")

        # document setup section
        #file.write("%%BeginSetup\n")
        #file.write("%%EndSetup\n")

        file.write(pagesfile.getvalue())
        pagesfile.close()

        file.write("%%Trailer\n")
        file.write("%%EOF\n")


class context:

    def __init__(self):
        self.linewidth_pt = None
        self.colorspace = None
        self.selectedfont = None

    def __call__(self, **kwargs):
        newcontext = copy.copy(self)
        for key, value in kwargs.items():
            setattr(newcontext, key, value)
        return newcontext
