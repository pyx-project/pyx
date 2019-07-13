#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""Python package for the generation of PostScript, PDF, and SVG files

PyX is a Python package for the creation of PostScript, PDF, and SVG files. It
combines an abstraction of the PostScript drawing model with a TeX/LaTeX
interface. Complex tasks like 2d and 3d plots in publication-ready quality are
built out of these primitives."""

import sys

if sys.version_info[0] == 2:
    print("""*** Sorry, this version of PyX runs on Python 3 only. ***
If you want to use PyX on Python 2, please use one of our
old releases up to PyX 0.12.x, i.e. execute something like:

   pip install pyx==0.12.1
""")
    exit()


from distutils.core import setup, Extension
import configparser
import pyx.version

cfg = configparser.ConfigParser()
cfg.read("setup.cfg")

# build list of extension modules

ext_modules = []
pykpathsea_ext_module = Extension("pyx.pykpathsea",
                                  sources=["pyx/pykpathsea.c"],
                                  libraries=["kpathsea"])
t1code_ext_module = Extension("pyx.font._t1code",
                              sources=["pyx/font/_t1code.c"])
if cfg.has_option("PyX", "build_pykpathsea") and cfg.getboolean("PyX", "build_pykpathsea"):
    ext_modules.append(pykpathsea_ext_module)
if cfg.has_option("PyX", "build_t1code") and cfg.getboolean("PyX", "build_t1code"):
    ext_modules.append(t1code_ext_module)


description, long_description = __doc__.split("\n\n", 1)

setup(name="PyX",
      version=pyx.version.version,
      author="Jörg Lehmann, André Wobst",
      author_email="pyx-devel@lists.sourceforge.net",
      url="https://pyx-project.org/",
      description=description,
      long_description=long_description,
      license="GPL",
      packages=["pyx", "pyx/graph", "pyx/graph/axis", "pyx/font", "pyx/dvi", "pyx/metapost"],
      package_data={"pyx": ["data/afm/*", "data/lfs/*", "data/def/*", "data/pyxrc"]},
      ext_modules=ext_modules,
      python_requires='>=3',
      classifiers=["Development Status :: 3 - Alpha",
                   "Intended Audience :: Developers",
                   "Intended Audience :: End Users/Desktop",
                   "License :: OSI Approved :: GNU General Public License (GPL)",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python :: 3",
                   "Topic :: Multimedia :: Graphics",
                   "Topic :: Scientific/Engineering :: Visualization",
                   "Topic :: Software Development :: Libraries :: Python Modules"],
      platforms="OS independent",
      extras_require = {"dev": ["zope.pagetemplate",
                                "sphinx",
                                "sphinx_selective_exclude",
                                "pillow",
                                "IPython",
                                "nbformat",
                                "testfixtures"]})
