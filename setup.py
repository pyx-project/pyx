#!/usr/bin/env python

from distutils.core import setup

setup(name="PyX",
      version="0.1",
      author="Jörg Lehmann, André Wobst",
      author_email="pyx-devel@lists.sourceforge.net",
      url="http://pyx.sourceforge.net/",
      description="Python package for the generation of mixed PS and (La)TeX code",
      license="GPL",
      packages=['pyx'],
      data_files=[('share/pyx', ['pyx/lfs/10pt.lfs',
                                 'pyx/lfs/11pt.lfs',
                                 'pyx/lfs/12pt.lfs',
                                 'pyx/lfs/10ptex.lfs',
                                 'pyx/lfs/11ptex.lfs',
                                 'pyx/lfs/12ptex.lfs',
                                 'pyx/lfs/foils17pt.lfs',
                                 'pyx/lfs/foils20pt.lfs',
                                 'pyx/lfs/foils25pt.lfs',
                                 'pyx/lfs/foils30pt.lfs'])]
     )

