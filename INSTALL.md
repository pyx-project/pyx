Installation
============


Prerequisites
-------------

PyX requires Python 3.2 or newer and a TeX installation (including Type1 fonts).
Try to start 'python', 'tex' and 'kpsewhich cmr10.pfb' (the latter should issue
a full path of the requested Type1 font).


Installation procedure
----------------------

PyX can be installed via pip straightforwardly. It can be run as an zipped egg.
As PyX is hosted on PyPI, it can be directly downloaded and installed by pip:

    pip install pyx

For debugging, you can call the pyxinfo() method immediately after the import to
get some details written to stderr.


Local usage without C extension modules
---------------------------------------

PyX can be run without any installation. To test your environment copy the file
hello.py from the examples directory to the main pyx directory (where the
subdirectory pyx containing the modules is located) and type 'python hello.py'.


Installation procedure
----------------------

The installation of PyX is pretty straightforward if you have installed the
Python distutils package.

First, you have to decide which C extension modules you want to build. This can
be done by setting the respective flags in the setup.cfg config file. By default
no C extension modules are built and appropriate fallbacks will be used instead.

The build_t1code option enables building of an extension module, which enables
faster coding/decoding of Type 1 fonts. The only requisites for building this
module are the Python header files and a C compiler. Note that the C compiler
has to suit the Python distribution you are using.

The second extension module pykpathsea provides Python binding for the kpathsea
library, which enables fast searching for files in the TeX/LaTeX directory
hierarchy. You will need the header files of this library, which unfortunately
are not included in many standard TeX distributions. Note that the fallback,
which uses the kpsewhich program, works equally well, although it is not as
efficient as using the library directly. If you want to build the C extension
module, you may also have to specify the location of the kpathsea header files
and of the library itself in the setup.cfg file.

After you have adapted the setup.cfg file to your needs, you can either build
the extension modules locally by running

    python setup.py build_ext -i

or install PyX system wide by using

    python setup.py install

or an appropriate variant thereof.


Development version
-------------------

For development checkout the PyX repo from github:

    git clone https://github.com/pyx-project/pyx

To prepare the develpment environment create a virtual env and run

    pip install -e .[dev]

