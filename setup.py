#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

"""Python package for the generation of encapsulated PostScript figures

PyX is a Python package for the creation of encapsulated PostScript figures.
It provides both an abstraction of PostScript and a TeX/LaTeX interface.
Complex tasks like 2d and 3d plots in publication-ready quality are built out
of these primitives.
"""

from distutils.core import setup, Extension
from distutils.command.install import install
import ConfigParser
import sys, os
import pyx

#
# build list of extension modules
#

ext_modules = []
pykpathsea_ext_module = Extension("pyx.pykpathsea._pykpathsea",
                                  sources=["pyx/pykpathsea/pykpathsea.c"],
                                  libraries=["kpathsea"])
t1strip_ext_module = Extension("pyx.t1strip._t1strip",
                               sources=["pyx/t1strip/t1strip.c", "pyx/t1strip/writet1.c"])

# obtain information on which modules have to be built from setup.cfg file
cfg = ConfigParser.ConfigParser()
cfg.read("setup.cfg")
if cfg.has_section("PyX"):
    if cfg.has_option("PyX", "build_pykpathsea") and cfg.getboolean("PyX", "build_pykpathsea"):
        ext_modules.append(pykpathsea_ext_module)
    if cfg.has_option("PyX", "build_t1strip") and cfg.getboolean("PyX", "build_t1strip"):
        ext_modules.append(t1strip_ext_module)

#
# data files
#

data_files = [("share/pyx", ["pyx/lfs/10pt.lfs",
                             "pyx/lfs/11pt.lfs",
                             "pyx/lfs/12pt.lfs",
                             "pyx/lfs/10ptex.lfs",
                             "pyx/lfs/11ptex.lfs",
                             "pyx/lfs/12ptex.lfs",
                             "pyx/lfs/foils17pt.lfs",
                             "pyx/lfs/foils20pt.lfs",
                             "pyx/lfs/foils25pt.lfs",
                             "pyx/lfs/foils30pt.lfs",
                             "contrib/pyx.def"])]

#
# install enhanced by siteconfig
#

class pyxinstall(install):

    def run(self):
        # name of the siteconfig file
        siteconfigname = os.path.join("pyx", "siteconfig.py")

        # read existing siteconfig
        try:
            f = open(siteconfigname, "rb")
            oldsiteconfig = f.read()
            f.close()
        except:
            oldsiteconfig = None

        try:
            # fill siteconfig data
            sharedir = os.path.join(self.install_data, "share", "pyx")
            f = open(siteconfigname, "w")
            f.write("lfsdir = %r\n" % sharedir)
            f.write("sharedir = %r\n" % sharedir)
            f.close()

            # perform install
            install.run(self)
        finally:
            # restore existing siteconfig
            if oldsiteconfig is not None:
                f = open(siteconfigname, "wb")
                f.write(oldsiteconfig)
                f.close()
            else:
                os.unlink(siteconfigname)

#
# additional package metadata (only available in Python 2.3 and above)
#

if sys.version_info >= (2, 3):
    addargs = { "classifiers":
                    [ "Development Status :: 3 - Alpha",
                      "Intended Audience :: Developers",
                      "Intended Audience :: End Users/Desktop",
                      "License :: OSI Approved :: GNU General Public License (GPL)",
                      "Operating System :: OS Independent",
                      "Programming Language :: Python",
                      "Topic :: Multimedia :: Graphics",
                      "Topic :: Scientific/Engineering :: Visualization",
                      "Topic :: Software Development :: Libraries :: Python Modules" ],
                "download_url":
                    "http://sourceforge.net/project/showfiles.php?group_id=45430",
                "platforms":
                    "OS independent",
              }
else:
    addargs = {}

# We're using the module docstring as the distutils descriptions. (seen in Zope3 setup.py)
doclines = __doc__.split("\n")

setup(name="PyX",
      version=pyx.__version__,
      author="Jörg Lehmann, André Wobst",
      author_email="pyx-devel@lists.sourceforge.net",
      url="http://pyx.sourceforge.net/",
      description=doclines[0],
      long_description="\n".join(doclines[2:]),
      license="GPL",
      packages=["pyx", "pyx/graph", "pyx/graph/axis", "pyx/t1strip", "pyx/pykpathsea"],
      ext_modules=ext_modules,
      data_files=data_files,
      cmdclass = {"install": pyxinstall},
      **addargs)
