#!/usr/bin/env python

from distutils.core import setup, Extension
import sys
import pyx

ext_modules = [Extension("pyx/t1strip/_t1strip",
                         sources=["pyx/t1strip/t1strip.c", "pyx/t1strip/writet1.c"]),
               Extension("pyx/pykpathsea/_pykpathsea", 
                         sources=["pyx/pykpathsea/pykpathsea.c"],
                         libraries=["kpathsea"])]

data_files = [('share/pyx', ['pyx/lfs/10pt.lfs',
                             'pyx/lfs/11pt.lfs',
                             'pyx/lfs/12pt.lfs',
                             'pyx/lfs/10ptex.lfs',
                             'pyx/lfs/11ptex.lfs',
                             'pyx/lfs/12ptex.lfs',
                             'pyx/lfs/foils17pt.lfs',
                             'pyx/lfs/foils20pt.lfs',
                             'pyx/lfs/foils25pt.lfs',
                             'pyx/lfs/foils30pt.lfs'])]

if sys.version_info >= (2, 3):
    addargs = { "classifiers":
                ["Development Status :: 3 - Alpha",
                 "Environment :: Console (Text Based)",
                 "Intended Audience :: Developers, End Users/Desktop",
                 "License :: OSI Approved :: GNU General Public License (GPL)",
                 "Operating System :: OS Independent",
                 "Programming Language :: Python",
                 "Topic :: Multimedia :: Graphics",
                 "Topic :: Scientific/Engineering :: Visualization",
                 "Topic :: Software Development :: Libraries :: Python Modules"]
              }
else:
    addargs = {}

setup(name="PyX",
      version=pyx.__version__,
      author="Jörg Lehmann, André Wobst",
      author_email="pyx-devel@lists.sourceforge.net",
      url="http://pyx.sourceforge.net/",
      description="Python package for the generation of encapsulated PostScript figures",
      license="GPL",
      packages=['pyx', 'pyx/t1strip', 'pyx/pykpathsea'],
      ext_modules=ext_modules,
      data_files=data_files,
      **addargs)
