#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2003 Jörg Lehmann <joergl@users.sourceforge.net>
#
# epstopng is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# epstopng is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with epstopng; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# TODO: - set dpi in png (don't know how to do this in PIL)
#       - this is much too slow --- consider a rewrite in C


import getopt, sys
from pyx import dvifile, canvas, trafo, unit


progname = "dvips v0.1: dvi to ps converter based on PyX"


def dvips(dviname, psname, vshift="-1 t cm"):
    fontmap = dvifile.readfontmap(["psfonts.map"])
    df = dvifile.dvifile(dviname, fontmap=fontmap)
    d = canvas.document()
    nr = 1
    while 1:
       c = df.readpage()
       if c is None: break
       print "[%d]" % nr,
       sys.stdout.flush()
       nr += 1
       p = canvas.page(paperformat="a4")
       p.insert(c, [trafo.translate(0, unit.length(vshift)+p.bbox().height())])
       d.append(p)
    d.writePSfile(psname)


def usage():
    print progname
    print "Copyright (C) 2004 Jörg Lehmann <joergl@users.sourceforge.net>"
    print "usage: dvips [options] <eps-file>"
    print "-h, --help: show this help"
    print "-o, --output <file>: output file name (optional)"


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:", ["help", "output"])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    output = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-o", "--output"):
            output = a
    if len(args) == 1:
        input = args[0]
    elif len(args):
        raise RuntimeError("can't handle several input files")
    else:
        raise RuntimeError("must specify an input file (reading from stdin is not yet supported)")
    if not input.endswith(".dvi"):
       input = input + ".dvi"
    if output is None:
       output = input[:-4] + ".ps"
    dvips(input, output)

def profilefunction(f):
    import hotshot, hotshot.stats
    prof = hotshot.Profile("test.prof")
    prof.runcall(f)
    prof.close()
    stats = hotshot.stats.load("test.prof")
    stats.strip_dirs()
    stats.sort_stats('time', 'calls')
    stats.print_stats(10)

if __name__ == "__main__":
    main()
    # profilefunction(main)

