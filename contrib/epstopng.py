#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
#
# Copyright (C) 2003 André Wobst <wobsta@users.sourceforge.net>
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


import getopt, sys, os, StringIO, re, math
import Image # we use the python image library (PIL)


progname = "epstopng v0.1: eps to transparent antialiased png converter"


def epstopng(epsname, pngname, resolution, scale, transparent, gsname, quiet):
    sys.stderr.write("run ghostscript to create a %i times larger non-antialiased image ... " % scale)
    gsout = os.popen("%s -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=ppmraw -sOutputFile=- -r%i %s" % (gsname, resolution*scale, epsname))
    input = Image.open(StringIO.StringIO(gsout.read())).convert("RGB") # ensure rgb here
    output = Image.new("RGBA", [(x+scale-1)/scale for x in input.size])
    sys.stderr.write("done\n")
    sys.stderr.write("image size is %ix%i\n" % output.size)

    inputdata = input.getdata() # getdata instead of getpixel leads to about a factor of 2 in running time
                                # similar effect with putdata possible??? (didn't got that running)
    inputsizex, inputsizey = input.size
    # loop over the small image
    for x in range(output.size[0]):
        sys.stderr.write("transparent antialias conversion ... %5.2f %%\r" % (x*100.0/output.size[0]))
        for y in range(output.size[1]):
            # r, g, b: sum of the rgb-values; u: number of non-transparent pixels
            r = g = b = u = 0
            # loop over the pixels of the large image to be used for pixel (x, y)
            for xo in range(x*scale, min((x+1)*scale, inputsizex-1)):
                for yo in range(y*scale, min((y+1)*scale, inputsizey-1)):
                    ro, go, bo = inputdata[xo+inputsizex*yo]
                    if (ro, go, bo) != transparent:
                        r += ro
                        g += go
                        b += bo
                        u += 1
            if u:
                output.putpixel((x, y), (r/u, g/u, b/u, (u*255)/(scale*scale)))
            else:
                output.putpixel((x, y), (255, 255, 255, 0))
    sys.stderr.write("transparent antialias conversion ... done     \n")

    output.save(pngname)


def usage():
    print progname
    print "Copyright (C) 2003 André Wobst <wobsta@users.sourceforge.net>"
    print "usage: epstopng [options] <eps-file>"
    print "-h, --help: show this help"
    print "-q, --quiet: be quiet"
    print "-o, --output <file>: output file name; must be set"
    print "-r, --resolution <dpi>: resolution; default: 100"
    print "-s, --scale <scale>: input scale for antialias; default: 4"
    print "-t, --transparent (<r>, <g>, <b>): transparent color; default: (255, 255, 255)"
    print "-g, --gsname <name>: name of the gs interpreter (gs version >= 8.0 needed!); default: \"gs\""


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hqo:r:s:t:g:", ["help", "quiet", "output", "resolution", "scale", "transparent", "gsname"])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    output = None
    resolution = 100
    scale = 4
    transparent = (255, 255, 255)
    gsname = "gs"
    quiet = 0
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-o", "--output"):
            output = a
        if o in ("-r", "--resolution"):
            resolution = int(a)
        if o in ("-s", "--scale"):
            scale = int(a)
        if o in ("-t", "--transparent"):
            m = re.compile(r"\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\s*$").match(a)
            if not m:
                raise RuntimeError("transparent argument does not match")
            transparent = [int(x) for x in m.groups()]
        if o in ("-g", "--gsname"):
            gsname = a
    if len(args) == 1:
        input = args[0]
    elif len(args):
        raise RuntimeError("can't handle several input files")
    else:
        raise RuntimeError("must specify an input file (reading from stdin is not yet supported)")
    if output is None:
        raise RuntimeError("you must specify an output file name")
    if not quiet:
        sys.stderr.write(progname + "\n")
    epstopng(input, output, resolution, scale, transparent, gsname, quiet)


if __name__ == "__main__":
    main()

