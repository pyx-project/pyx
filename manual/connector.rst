
.. _connector:

***********************
Module :mod:`connector`
***********************

This module provides classes for connecting two :class:`box`\ -instances with
lines, arcs or curves. All constructors of the following connector-classes take
two :class:`box`\ -instances as the two first arguments. They return a
connecting path from the first to the second box. The overall geometry of the
path is such that is starts/ends at the boxes' centers. It is then cut by the
boxes' outlines. The resulting :class:`connector` will additionally be shortened
by lengths given in the :keyword:`boxdists`\ -keyword (a list of two lengths,
default ``[0,0]``).

Angle keywords can be either absolute or relative. The absolute angles refer to
the angle between x-axis and the running tangent of the connector, while the
relative angles are between the direct connecting line of the box-centers and
the running tangent (see figure. :ref:`fig:connector`).

The bulge-keywords parameterize the deviation of the connector from the
connecting line. It has different meanings for different connectors (see figure.
:ref:`fig:connector`).


Class :class:`line`
===================

The constructor of the :class:`line` class accepts only boxes and the
:keyword:`boxdists`\ -keyword.


Class :class:`arc`
==================

The constructor takes either the :keyword:`relangle`\ -keyword or a combination
of :keyword:`relbulge` and :keyword:`absbulge`. The "bulge" is meant to be a
hint for the greatest distance between the connecting arc and the straight
connection between the box-centers. (Default: ``relangle=45``,
``relbulge=None``, ``absbulge=None``)

Note that the bulge-keywords override the angle-keyword.

If both :keyword:`relbulge` and :keyword:`absbulge` are given, they will be
added.


Class :class:`curve`
====================

The constructor takes both angle- and bulge-keywords. Here, the bulges are used
as distances between the control points of the cubic Beziér-curve. For the signs
of the angle- and bulge-keywords refer to figure :ref:`fig:connector`.

:keyword:`absangle1` or :keyword:`relangle1` ---  :keyword:`absangle2` or
:keyword:`relangle2`, where the absolute angle overrides the relative if both
are given. (Default: ``relangle1=45``, ``relangle2=45``, ``absangle1=None``,
``absangle2=None``)

:keyword:`absbulge` and :keyword:`relbulge`, where they will be added if both
are given. ---  (Default: ``absbulge=None``, ``relbulge=0.39``; these default
values produce output similar to the defaults of :class:`arc`.)

.. % DUMMY
.. _fig_label:
.. figure:: connector.*
   :align:  center


.. centered:: The angle-parameters of the connector.arc (left panel) and the connector.curve (right panel) classes.


Class :class:`twolines`
=======================

This class returns two connected straight lines. There is a vast variety of
combinations for angle- and length-keywords. The user has to make sure to
provide a non-ambiguous set of keywords:

:keyword:`absangle1` or :keyword:`relangle1` for the first angle, ---
:keyword:`relangleM` for the middle angle and ---  :keyword:`absangle2` or
:keyword:`relangle2` for the ending angle. Again, the absolute angle overrides
the relative if both are given. (Default: all five angles are ``None``)

:keyword:`length1` and :keyword:`length2` for the lengths of the connecting
lines. (Default: ``None``)

