#!/usr/bin/env python

from distutils.core import setup, Extension

setup(name="PyX",
      author="Jörg Lehmann, André Wobst",
      author_email="pyx-devel@lists.sourceforge.net",
      url="http://pyx.sourceforge.net/",
      description="Python package for the generation of mixed PS and (La)TeX code",
      license="GPL",
      ext_modules=[Extension("t1strip", sources=["t1strip.c", "writet1.c", "search.c"],
                            libraries = ["kpathsea"])],
     )

