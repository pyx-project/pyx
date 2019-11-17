.. _text_without_tex:

=======================
Text output without TeX
=======================

General aspects
===============


.. _unicode_engine:

How can I typeset text in PyX without TeX?
------------------------------------------

Originally, TeX (or variants thereof, like LaTeX) were the only way to typeset
text in PyX. However, as PyX does all the post-typesetting itself based on the
dvi output of TeX, it has all the font infrastructure in place. Starting with
PyX 0.15, this functionality is made available for direct use.

The UnicodeEngine allows to typeset text on a canvas ``c`` using the font
directly::

    engine = text.UnicodeEngine()
    c.insert(engine.text(0, 0, "Hello, world!"))

The font name and size are parameters to the ``UnicodeEngine`` constructor::

    engine = text.UnicodeEngine(fontname='cmss10', size=20)

A text engine can be made the default typesetting engine by::

    text.set(text.UnicodeEngine)

Parameters to the engine are provided as additional parameters to the ``set``
command::

    text.set(text.UnicodeEngine, fontname='cmss10', size=20)


.. _font_configuration_for_the_unicode_engine:

But I still need a TeX installation?
------------------------------------

In fact, the answer of the previous question will not function out of the box
if you do not have a TeX installation in place. The reason is, that PyX still
requires and uses the Computer Modern fonts provided by the TeX installation.
In fact, PyX uses Type1 fonts, and needs the pfb and afm files of the font. You
can do so by placing the two files of the Type1 font in the current directory.
However, fonts can also be loaded from somewhere else in the file system.

Suppose you want to use the standard TeX fonts, you can get them in Type1
format at `https://www.ams.org/publications/authors/tex/amsfonts <https://www.ams.org/publications/authors/tex/amsfonts>`_.
Extract the zip file somewhere on your file system and generate an index file
(ls-R) in the directory you just created by extracting the zip file by
``ls -R > ls-R``. Finally create a ``.pyxrc`` file in your home directory. with the
following content::

    [filelocator]
    methods = local internal ls-R
    ls-R = /<the full path of the diretory you extracted the amsfonts zip file>/ls-R

You can skip the generation of the index file, and use the ``recursivedir``
locator instead::

    [filelocator]
    methods = local internal recursivedir
    recursivedir = /<the full path of the diretory you extracted the amsfonts zip file>

However, using an index file is faster, as PyX does not need to crawl the
directory structure to locate the actual files.
