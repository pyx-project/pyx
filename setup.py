#!/usr/bin/env python

from distutils.core import setup, Extension
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

setup(name="PyX",
      version=pyx.__version__,
      author="Jörg Lehmann, André Wobst",
      author_email="pyx-devel@lists.sourceforge.net",
      url="http://pyx.sourceforge.net/",
      description="Python package for the generation of mixed PS and (La)TeX code",
      license="GPL",
      packages=['pyx'],
      ext_modules=ext_modules,
      data_files=data_files)
