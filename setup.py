#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""Python package for the generation of PostScript and PDF files

PyX is a Python package for the creation of PostScript and PDF files. It
combines an abstraction of the PostScript drawing model with a TeX/LaTeX
interface. Complex tasks like 2d and 3d plots in publication-ready quality are
built out of these primitives."""

import ConfigParser
import pyx.version

setuptools_args={}

# obtain information on which modules have to be built and whether to use setuptools
# instead of distutils from setup.cfg file
cfg = ConfigParser.ConfigParser()
cfg.read("setup.cfg")
if cfg.has_section("PyX"):
    if cfg.has_option("PyX", "build_pykpathsea") and cfg.getboolean("PyX", "build_pykpathsea"):
        ext_modules.append(pykpathsea_ext_module)
    if cfg.has_option("PyX", "build_t1code") and cfg.getboolean("PyX", "build_t1code"):
        ext_modules.append(t1code_ext_module)
    if cfg.has_option("PyX", "use_setuptools") and cfg.getboolean("PyX", "use_setuptools"):
        from setuptools import setup, Extension
        setuptools_args={"zip_safe": True}
    else:
        from distutils.core import setup, Extension


#
# build list of extension modules
#

ext_modules = []
pykpathsea_ext_module = Extension("pyx.pykpathsea",
                                  sources=["pyx/pykpathsea.c"],
                                  libraries=["kpathsea"])
t1code_ext_module = Extension("pyx.font._t1code",
                              sources=["pyx/font/_t1code.c"])


description, long_description = __doc__.split("\n\n", 1)

setup(name="PyX",
      version=pyx.version.version,
      author="Jörg Lehmann, André Wobst",
      author_email="pyx-devel@lists.sourceforge.net",
      url="http://pyx.sourceforge.net/",
      description=description,
      long_description=long_description,
      license="GPL",
      packages=["pyx", "pyx/graph", "pyx/graph/axis", "pyx/font", "pyx/dvi"],
      package_data={"pyx": ["data/afm/*", "data/lfs/*", "data/def/*", "data/pyxrc"]},
      ext_modules=ext_modules,
      classifiers=["Development Status :: 3 - Alpha",
                   "Intended Audience :: Developers",
                   "Intended Audience :: End Users/Desktop",
                   "License :: OSI Approved :: GNU General Public License (GPL)",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Topic :: Multimedia :: Graphics",
                   "Topic :: Scientific/Engineering :: Visualization",
                   "Topic :: Software Development :: Libraries :: Python Modules"],
      download_url="http://sourceforge.net/project/showfiles.php?group_id=45430",
      platforms="OS independent",
      **setuptools_args)
