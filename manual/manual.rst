.. include:: <isonum.txt>

##########
PyX Manual
##########

:Author: Jörg Lehmann <joerg@pyx-project.org>,
         Michael Schindler <m-schindler@users.sourceforge.net>,
         André Wobst <wobsta@pyx-project.org>
:Date: |today|

.. topic:: Abstract

   PyX is a Python package for the creation of PostScript, PDF, and SVG files. It
   combines an abstraction of the PostScript drawing model with a TeX/LaTeX
   interface and direct Type 1 / OpenType font support. Complex tasks such as
   2D and 3D publication-quality data plots in cartesian or curvilinear
   coordinates, path deformations, and box-and-connector diagrams are built on
   top of these primitives in a modular, extensible architecture.

.. toctree::
   :maxdepth: 2

   intro

.. only:: html

   **************
   Basic graphics
   **************

.. toctree::
   :maxdepth: 2

   graphics
   path
   metapost
   deformer
   canvas
   document

.. only:: html

   ****
   Text
   ****

.. toctree::
   :maxdepth: 2

   text

.. only:: html

   ********
   Plotting
   ********

.. toctree::
   :maxdepth: 2

   graph
   axis

.. only:: html

   ********************
   Boxes and Connectors
   ********************

.. toctree::
   :maxdepth: 2

   box
   connector

.. only:: html

   *********************************
   PostScript, PDF, SVG, and Bitmaps
   *********************************

.. toctree::
   :maxdepth: 2

   epsfile
   pdffile
   svgfile
   bitmap

.. only:: html

   *************************
   Basic classes and modules
   *************************

.. toctree::
   :maxdepth: 2

   bbox
   color
   pattern
   unit
   trafo

.. only:: html

   ********
   Appendix
   ********

.. toctree::
   :maxdepth: 2

   colorname
   gradientname
   pathstyles
   arrows
   utils
