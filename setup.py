#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from setuptools import setup, Extension
import configparser

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

setup(ext_modules=ext_modules)
