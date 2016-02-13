=============
TeX and LaTeX
=============

General aspects
===============

.. _what_is_tex:

What is TeX/LaTeX and why do I need it?
---------------------------------------

TeX is a high quality typesetting system developed by Donald E. Knuth which is
available for a wide variety of operating systems. LaTeX is a macro package
originally developed by Leslie Lamport which makes life with TeX easier, in
particular for complex typesetting tasks. The current version of LaTeX is
referred to as LaTeX2e and offers e.g. improved font selection as compared to
the long outdated LaTeX 2.09 which should no longer be used. 

All typesetting tasks in PyX are ultimately handed over to TeX (which is the
default) or LaTeX, so that PyX cannot do without it. On the other hand, the
capabilities of TeX and LaTeX can be used for complex tasks where both graphics
and typesetting are needed.

.. _intro_tex_latex:

I don't know anything about TeX and LaTeX. Where can I read something about it?
--------------------------------------------------------------------------------

Take a look at CTAN (cf. :ref:`ctan`) where in `CTAN:info
<http://www.ctan.org/tex-archive/info/>`_ you may be able to find some useful
information. There exists for example “A Gentle Introduction to TeX” by M. Doob
(`CTAN:gentle/gentle.pdf <http://www.ctan.org/tex-archive/gentle/gentle.pdf>`_)
and “The Not So Short Introduction to LaTeX2e”
(`CTAN:info/lshort/english/lshort.pdf
<http:www.ctan.org/tex-archive/info/lshort/english/lshort.pdf>`_) by T. Oetiker
et al. The latter has been translated into a variety of languages among them
korean (which you will not be able to read unless you have appropriate fonts
installed) and mongolian.

Of course, it is likely that these documents will go way beyond what you will
need for generating graphics with PyX so you don't have to read all of it
(unless you want to use TeX or LaTeX for typesetting which can be highly
recommended). 

There exists also a number of FAQs on TeX at `CTAN:help <http://www.ctan.org/tex-archive/help>`_.

.. _ctan:

What is CTAN?
-------------

CTAN is the *Comprehensive TeX Archive Network* where you will find almost
everything related to TeX and friends. The main CTAN server is `www.ctan.org
<http://www.ctan.org>`_ but there exists a large number of mirrors around the
world. You can help to reduce the load on the main server by using
`mirror.ctan.org <http://mirror.ctan.org>`_ which will redirect you to a mirror
nearby. A list of known mirrors is available at
`http://mirror.ctan.org/README.mirrors
<http://mirror.ctan.org/README.mirrors>`_.

In this FAQ, ``CTAN:`` refers to the root of the CTAN tree, e.g.
`http://www.ctan.org/tex-archive/ <http://www.ctan.org/tex-archive/>`_.  The
links to CTAN in this document point to the main server but you might consider
using a server closer to you in order to reduce traffic load.

Is there support for ConTeXt?
-----------------------------

No, and as far as I know there no plans to provide it in the near future.
Given the close ties between ConTeXt and MetaPost, ConTeXt users probably
prefer to stick with the latter anyway.

TeX and LaTeX commands useful for PyX
=====================================

How do I get a specific symbol with TeX or LaTeX?
-------------------------------------------------

A list of mathematical symbols together with the appropriate command name can
be found at `CTAN:info/symbols/math/symbols.pdf
<http://www.ctan.org/tex-archive/info/symbols/math/symbols.pdf>`_. A
comprehensive list containing almost 6000 symbols for use with LaTeX can be
obtained from `CTAN:info/symbols/comprehensive/symbols-a4.pdf
<http://www.ctan.org/tex-archive/info/symbols/comprehensive/symbols-a4.pdf>`_.
In some cases it might be necessary to install fonts or packages available from
CTAN (cf. :ref:`ctan`).

TeX and LaTeX errors
====================

.. _undefined_usepackage:

Undefined control sequence ``\usepackage``
------------------------------------------

The command ``\usepackage`` is specific to LaTeX. Since by default PyX
uses TeX, you have to specify the correct mode::

   text.set(mode="latex")

Undefined control sequence ``\frac``

The command ``\frac`` is only available in LaTeX. The equivalent to
``\frac{a}{b}`` in TeX is ``{a \over b}``.  As an alternative you may ask for
the LaTeX mode as explained in :ref:`undefined_usepackage`.

Missing ``$`` inserted
----------------------

You have specified TeX- or LaTeX-code which is only valid in math mode. 
Typical examples are greek symbols, sub- and superscripts or fractions. 

On the PyX level, you can specify math mode for the whole string by using
``text.mathmode`` as in ::

   c.text(0, 0, r"{\alpha}", text.mathmode)

Keep also in mind that the standard Python interpretation of the backslash as 
introducing escape sequences needs to be prevented.

On the TeX/LaTeX level you should enclose the commands requiring math mode in
``$``'s. As an example, ``$\alpha_i^j$`` will produce a greek letter alpha with
a subscript i and a superscript j.  The dollar sign thus allows you to specify
math mode also for substrings. There exist other ways to specify math mode in
TeX and LaTeX which are particularly useful for more complex typesetting tasks.
To learn more about it, you should consult the documentation
:ref:`intro_tex_latex`. 

Why do environments like ``itemize`` or ``eqnarray`` seem not to work?
----------------------------------------------------------------------

An itemize environment might result in a LaTeX error complaining about a
``missing \item`` or an eqnarray might lead to a LaTeX message ``missing
\endgroup inserted`` even though the syntax appears to be correct. The TeXnical
reason is that in PyX text is typeset in left-right mode (LR mode) which does
not allow linebreaks to occur. There are two ways out.

If the text material should go in a box of given width, a parbox can be used
like in the following example::

   text.set(mode="latex")
   c = canvas.canvas()
   w = 2
   c.text(0, 0, r"\begin{itemize}\item a\item b\end{itemize}", [text.parbox(w)])

Occasionally, one would like to have the box in which the text appears to be as
small as possible. Then the ``fancybox`` package developed by Timothy Van Zandt
is useful which provides several environments like ``Bitemize`` and
``Beqnarray`` which can be processed in LR mode. The relevant part of the code
could look like::

   text.set(mode="latex")
   text.preamble(r"\usepackage{fancybox}")
   c = canvas.canvas()
   c.text(0, 0, r"\begin{Bitemize}\item a\item b\end{Bitemize}")

Other environments provided by the ``fancybox`` package include ``Bcenter``,
``Bflushleft``, ``Bflushright``, ``Benumerate``, and ``Bdescription``. For more
details, the documentation of the package should be consulted.

.. _fontshape_undefined:

Font shape ``OT1/xyz/m/n`` undefined
------------------------------------

You have asked to use font ``xyz`` which is not available. Make sure that you
have this font available in Type1 format, i.e. there should be a file
``xyz.pfb`` somewhere. If your TeX system is TDS compliant (TDS=TeX directory
structure, cf. `CTAN:tds/draft-standard/tds/tds.pdf
<http://www.ctan.org/tex-archive/tds/draft-standard/tds/tds.pdf>`_) you should
take a look at the subdirectories of ``$TEXMF/fonts/type1``.

File ``…`` is not available or not readable
-------------------------------------------

Such an error message might already occur when running the example file
``hello.py`` included in the PyX distribution. Usually, the error occurs due to
an overly restrictive umask setting applied when unpacking the ``tar.gz``
sources. This may render the file mentioned in the error message unreadable
because the python distutil installation package doesn't change the file
permissions back to readable for everyone. 

If the file exists, the problem can be solved by changing the permissions to 
allow read access.

No information for font ``cmr10`` found in font mapping file
------------------------------------------------------------

Such an error message can already be encountered by simply running the example
file ``hello.py`` included in the PyX distribution. The likely reason is that
the TeX system does not find the cmr fonts in Type1 format.  PyX depends on
these fonts as it does not work with the traditional pk fonts which are stored
as bitmaps.

Therefore, the first thing to make sure is that the cmr Type1 fonts are
installed. In some TeX installations, the command ``kpsewhich cmr10.pfb`` will
return the appropriate path if the cmr fonts exist in the binary Type1 format
(extension ``pfb``) required by PyX. If the command does not work but the TeX
system is TDS compliant (:ref:`fontshape_undefined`), a look should be taken at
``$TEXMF/fonts/type1/bluesky/cm`` where ``$TEXMF`` is the root of the ``texmf``
tree.

If the Type1 fonts do not exist on the system, they may be obtained from the
CTAN (cf. :ref:`ctan`) at `CTAN:fonts/cm/ps-type1/bluesky
<http://www.ctan.org/tex-archive/fonts/cm/ps-type1/bluesky>`_). See the
``README`` for information about who produced these fonts and why they are
freely available.

If the Type1 fonts exist, the next step is to take a look at ``psfonts.map``.
There may be several files with this name on the system, so it is important to
find out which one TeX is actually using.  ``kpsewhich psfonts.map`` might give
this information.

The most likely problem is that this file does not contain a line telling TeX
what to do if it encounters a request for font ``cmr10``, i.e. the following
line may be missing ::

   cmr10           CMR10           <cmr10.pfb

It is probable that the required lines (in practice, you do not just need
``cmr10``) are found in a file named ``psfonts.cmz`` which resides in
``$TEXMF/dvips/bluesky``. 

One solution is to instruct PyX to read additional map files like
``psfonts.cmz`` or ``psfonts.amz``. This can be achieved by modifying the
appropriate ``pyxrc`` file which is either the systemwide ``/etc/pyxrc`` or
``.pyxrc`` in the user's home directory. Here, the names of the map files to be
read by PyX should be appended separated by whitespaces like in the following
example::

   [text]
   fontmaps = psfonts.map psfonts.cmz psfonts.amz

The same effect can be achieved by inserting the following line into the
PyX code::

   text.set(fontmaps="psfonts.map psfonts.cmz psfonts.amz")

Note that the default map (``psfonts.map``) has to be specified explicitly.

An alternative approach consists in modifying the TeX installation by inserting
the contents of the desired map files like ``psfonts.cmz`` into
``psfonts.map``. Probably, ``psfonts.map`` recommends not to do this by hand.
In this case the instructions given in the file should be followed.  Otherwise,
``psfonts.cmz`` should be copied into ``psfonts.map`` while keeping a backup of
the old ``psfonts.map`` just in case. After these changes, PyX most likely will
be happy. When inserting ``psfonts.cmz`` into ``psfonts.map`` it may be a good
idea to include ``psfonts.amz`` as well. ``psfonts.amz`` contains information
about some more fonts which might be needed at some point. Making these changes
to ``psfonts.map`` will imply that the TeX system will use the cmr fonts in
Type1 format instead of pk format which is actually not a bad thing, in
particular if ``latex / dvips / ps2pdf`` is used to generate PDF output. With
fonts in pk format this will look ugly and using Type1 fonts solves this
problem as well. When ``pdflatex`` is used to create PDF files, Type1 fonts
will be used anyway.

Fonts
=====

I have Type1 fonts in ``pfa`` format. How do I obtain the corresponding ``pfb`` files needed by PyX?
----------------------------------------------------------------------------------------------------

.. todo:

   still needs to be answered

.. _other_font:

I want to use a font other than computer modern roman
-----------------------------------------------------

As long as you have a font in Type1 format available, this should be no
problem (even though it may cost you some time to set up things properly).

In the simplest case, your LaTeX system contains everything needed. 
Including the following line into your code will probably work::

    text.set(mode="latex")
    text.preamble(r"\usepackage{mathptmx}")

and give you Times as roman font. 

If you own one of the more common commercial fonts, take a look at `CTAN:fonts
<http://www.ctan.org/tex-archive/fonts/>`_ and its subdirectories as well as at
the web page `http://home.vr-web.de/was/fonts.html
<http://home.vr-web.de/was/fonts.html>`_ of Walter Schmidt. It is not unlikely
that somebody has already done most of the work for you and created the files
needed for the font to work properly with LaTeX. But remember: we are talking
about commercial fonts here, so do not expect to find the fonts themselves for
free.

If none of these cases applies, you should spend some time reading manuals
about font installation, e.g. `CTAN:macros/latex/doc/fntguide.pdf
<http://www.ctan.org/tex-archive/macros/latex/doc/fntguide.pdf>`_ (of course, I
do not expect font wizards to read the last few lines).

Can I use a TrueType font with PyX?
-----------------------------------

Not directly as PyX only knows how to handle Type1 fonts (although it is
possible to get LaTeX to work with TrueType fonts). However, you may use
``ttf2pt1`` (from `ttf2pt1.sourceforge.net <http://ttf2pt1.sourceforge.net>`_)
to convert a TrueType font into a Type1 font which you then install in your TeX
system (cf. :ref:`other_font`). You will loose hinting information in the
conversion process but this should not really matter on output devices with not
too low resolution.
