
.. module:: pattern

*********************
Module :mod:`pattern`
*********************

.. sectionauthor:: Jörg Lehmann <joerg@pyx-project.org>


This module contains the :class:`pattern.pattern` class, whichs allows the definition of
PostScript Tiling patterns (cf. Sect. 4.9 of the PostScript Language Reference
Manual) which may then be used to fill paths. In addition, a number of
predefined hatch patterns are included.


Class :class:`pattern`
======================

The classes :class:`pattern.pattern` and :class:`canvas.canvas` differ only in their
constructor and in the absence of a :meth:`writeEPSfile` method in the former.
The :class:`pattern` constructor accepts the following keyword arguments:

+-----------------+-----------------------------------------------+
| keyword         | description                                   |
+=================+===============================================+
| ``painttype``   | ``1`` (default) for coloured patterns or      |
|                 | ``2`` for uncoloured patterns                 |
+-----------------+-----------------------------------------------+
| ``tilingtype``  | ``1`` (default) for constant spacing tilings  |
|                 | (patterns are spaced constantly by a multiple |
|                 | of a device pixel), ``2`` for undistorted     |
|                 | pattern cell, whereby the spacing may vary by |
|                 | as much as one device pixel, or ``3`` for     |
|                 | constant spacing and faster tiling which      |
|                 | behaves as tiling type ``1`` but with         |
|                 | additional distortion allowed to permit a     |
|                 | more efficient implementation.                |
+-----------------+-----------------------------------------------+
| ``xstep``       | desired horizontal spacing between pattern    |
|                 | cells, use ``None`` (default) for automatic   |
|                 | calculation from pattern bounding box.        |
+-----------------+-----------------------------------------------+
| ``ystep``       | desired vertical spacing between pattern      |
|                 | cells, use ``None`` (default) for automatic   |
|                 | calculation from pattern bounding box.        |
+-----------------+-----------------------------------------------+
| ``bbox``        | bounding box of pattern. Use ``None`` for an  |
|                 | automatic determination of the bounding box   |
|                 | (including an enlargement by ``bboxenlarge``  |
|                 | pts on each side.)                            |
+-----------------+-----------------------------------------------+
| ``trafo``       | additional transformation applied to pattern  |
|                 | or ``None`` (default). This may be used to    |
|                 | rotate the pattern or to shift its phase (by  |
|                 | a translation).                               |
+-----------------+-----------------------------------------------+
| ``bboxenlarge`` | enlargement when using the automatic bounding |
|                 | box determination; default is 5 pts.          |
+-----------------+-----------------------------------------------+

After you have created a pattern instance, you define the pattern shape by
drawing in it like in an ordinary canvas. To use the pattern, you simply pass
the pattern instance to a :meth:`stroke`, :meth:`fill`, :meth:`draw` or
:meth:`set` method of the canvas, just like you would do with a colour, etc.

