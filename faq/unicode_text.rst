.. _text_without_tex:

=======================
Text output without TeX
=======================

General aspects
===============


.. _unicode_engine:

How can I typeset text in PyX without TeX?
------------------------------------------

Starting with PyX 0.15, an additional typesetting engine besides the TeX and
LaTeX engine is available: the Unicode engine. It can be made the default
typesetting engine by::

    text.set(text.UnicodeEngine)

The font and its size can be specified through additional parameters like in
this example::

    text.set(text.UnicodeEngine, fontname='cmss10', size=20)


.. _font_configuration_for_the_unicode_engine:

Do I still need a TeX installation?
-----------------------------------

Not necessarily. However, PyX needs to have access to the Type1 fonts it is
supposed to use in the typesetting. Specifically, it needs the corresponding
``pfb`` and ``afm`` files. There are different ways to provide them.

The first possibility is indeed a TeX installation. This approach makes
particularly sense if the fonts to be used are made available by a TeX
distribution. For example, the Computer Modern fonts used by PyX as default
fonts are provided by all TeX installations.

If, on the other hand, a font is to be used for which no TeX support is readily
available, its ``pfb`` and ``afm`` files can be put in the directory where
the Python script is placed. The font will then be found by PyX if the parameter
``fontname`` corresponds to the basename of the ``pfb`` and ``afm`` files.

The latter approach is not optimal if the font is used in different PyX scripts
scattered over several directories or if a larger number of fonts is needed.
Then it is better to store the Type1 font files in a central place and to tell
PyX about the files as explained in the following example.

Suppose the standard TeX fonts should be used without a TeX installation. The
fonts can be obtained in Type1 format from
`https://www.ams.org/publications/authors/tex/amsfonts <https://www.ams.org/publications/authors/tex/amsfonts>`_.
Extract the zip file somewhere on your file system and generate an index file
(ls-R) by running ``ls -R > ls-R`` in the directory to which the fonts were
extracted. Finally create a ``.pyxrc`` file in your home directory with the
following content::

    [filelocator]
    methods = local internal ls-R
    ls-R = /<the full path of the directory you extracted the amsfonts zip file>/ls-R

The generation of the index file can be skipped by using the ``recursivedir``
locator instead::

    [filelocator]
    methods = local internal recursivedir
    recursivedir = /<the full path of the directory you extracted the amsfonts zip file>

However, the use of an index file increases performance, as PyX does not need to crawl the
directory structure to locate the actual files.


.. _tex_and_unicode:

Is it possible to use the Unicode engine in addition to the TeX engine?
-----------------------------------------------------------------------

Yes, it is possible to use different typesetting engines in the same script.
The following example uses the Unicode engine and the TeX engine to typeset
text on a canvas ``c``::

    unicode_engine = text.UnicodeEngine()
    c.insert(unicode_engine.text(0, 0, "Hello, world!"))
    tex_engine = text.TexEngine()
    c.insert(tex_engine.text(0, 1, "Hello, world!"))

If needed, the font name and size can be passed as parameters to the
``UnicodeEngine`` constructor::

    engine = text.UnicodeEngine(fontname='cmss10', size=20)
