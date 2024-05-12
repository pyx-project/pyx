
************************
Guideline for TikZ users
************************

The TikZ package is a powerful tool for creating graphics in TeX. It is
based on the pgf package and allows you to create graphics programmatically.

If you are familiar with TikZ, this document provides a translation for
common TikZ commands to the corresponding PyX commands.

The code below assumes you have executed the preparations listed in
:ref:`graphics`.

Simple path operations
======================

``\draw (0, 0)--(1, 1);``

   ::

      c.stroke(path.line(0, 0, 1, 1));

``\draw (0, 0)--(1, 1)--(2, 1);``

   ::

      c.stroke(path.path(path.moveto(0, 0), path.lineto(1, 1), path.lineto(2, 1)));

``\draw (0bp, 0bp)--(100bp, 100bp)--(200bp, 100bp);``

   ::

         c.stroke(path.path(path.moveto_pt(0, 0), path.lineto_pt(100, 100), path.lineto_pt(200, 100)));

   .. note ::
      The suffix ``_pt`` is used to specify the coordinates in PostScript.
      The unit in TeX is ``bp`` (big point), which is equivalent to 1/72 inch.
      TeX's ``pt`` is equivalent to 1/72.27 inch instead.

``\draw (0, 0)--++(1, 1) ++(1, 0)--++(1, 0);``

   ::

      c.stroke(path.path(path.moveto(0, 0), path.rlineto(1, 1),
                         path.rmoveto(1, 0), path.rlineto(1, 0)));

``\draw (0, 0)..controls (1, 0) and (3, 2)..(3, 3);``

   ::

      c.stroke(path.curve(0, 0, 1, 0, 3, 2, 3, 3));

   or equivalently::

      c.stroke(path.path(path.moveto(0, 0), path.curveto(1, 0, 3, 2, 3, 3)));

``\draw (0, 0) to [out=0, in=-45] (1, 1);``

   ::

      from pyx.metapost.path import beginknot, endknot, smoothknot, tensioncurve
      c.stroke(metapost.path.path([beginknot(0, 0, angle=0), tensioncurve(),
                                   endknot(1, 1, angle=135)]))

``\draw plot [smooth] coordinates{(0,0) (1,1) (2,0) (1,-1)};``

   ::

      from pyx.metapost.path import beginknot, endknot, smoothknot, tensioncurve
      c.stroke(metapost.path.path([
          beginknot(0, 0), tensioncurve(), smoothknot(1, 1), tensioncurve(),
          smoothknot(2, 0), tensioncurve(), endknot(1, -1)]))

   .. note ::
      The algorithm used by PyX is the Hobby algorithm, which produces
      much better results than the default algorithm used by TikZ.
   .. seealso ::
      `A question on TeX.StackExchange <https://tex.stackexchange.com/q/33607>`_.

``\draw plot [smooth cycle] coordinates{(0,0) (1,1) (2,0) (1,-1)};``

   ::

      from pyx.metapost.path import beginknot, endknot, smoothknot, tensioncurve
      c.stroke(metapost.path.path([
          smoothknot(0, 0), tensioncurve(), smoothknot(1, 1), tensioncurve(),
          smoothknot(2, 0), tensioncurve(), smoothknot(1, -1), tensioncurve()]))

``\draw (2, 3) rectangle (12, 33);``

   ::

      c.stroke(path.rect(2, 3, 10, 30));

``\draw (2, 3) circle (1);``

   ::

      c.stroke(path.circle(2, 3, 1));

``\draw (1, 0) arc [start angle=0, end angle=90, radius=1];``

   ::

      c.stroke(path.path(path.arc(0, 0, r=1, angle1=0, angle2=90)));

   .. note ::
      In PyX, the coordinate must be the center of the circle
      instead of the starting point of the arc.


``\draw (1, 0) arc [start angle=90, end angle=0, radius=1];``

   ::

      c.stroke(path.path(path.arcn(0, 0, r=1, angle1=90, angle2=0)));

``\draw [rounded corners=2] (0, 0) rectangle (1, 2);``

   ::

      c.stroke(path.rect(0, 0, 1, 2), [deformer.smoothed(radius=0.1)])

   or::

      c.stroke(deformer.smoothed(radius=0.1).deform(path.rect(0, 0, 1, 2)))

   .. note ::
      Unlike TikZ, the rounded corners are not exactly part of a circle
      with the specified radius, even if the turn angles are 90 degrees.

Filled paths and colors
=======================

``\fill (2, 3) circle (1);``

   ::

      c.fill(path.circle(2, 3, 1));

``\fill [yellow] (2, 3) circle (1);``

   ::

      c.fill(path.circle(2, 3, 1), [color.cmyk.Yellow]);

   .. seealso ::
      :ref:`colorname`

``\filldraw [fill=yellow, draw=red] (2, 3) circle (1);``

   ::

      c.draw(path.circle(2, 3, 1), [deco.filled([color.cmyk.Yellow]), deco.stroked([color.rgb.red])])

Nodes and text
==============

``\node at (0, 0) {content};``

   ::

      c.text(0, 0, "content", [text.halign.boxcenter, text.valign.middle])

``\node [text=red] at (0, 0) {content};``

   ::

      c.text(0, 0, "content",
             [text.halign.boxcenter, text.valign.middle, color.rgb.red])

``\node [above] at (0, 0) {content};``

   ::

      c.text(0, 0, "content", [text.halign.boxcenter, text.valign.bottom])

``\node [below] at (0, 0) {content};``

   ::

      c.text(0, 0, "content", [text.halign.boxcenter, text.valign.top])

``\node [base left] at (0, 0) {content};``

   ::

      c.text(0, 0, "content", [text.halign.right, text.valign.baseline])

``\node [base right] at (0, 0) {content};``

   ::

      c.text(0, 0, "content", [text.halign.left, text.valign.baseline])

``\node [left] at (0, 0) {content};``

   ::

      c.text(0, 0, "content", [text.halign.right, text.valign.middle])

``\node [right] at (0, 0) {content};``

   ::

      c.text(0, 0, "content", [text.halign.left, text.valign.middle])

``\node [anchor=base] at (0, 0) {content};``

   ::

      c.text(0, 0, "content", [text.halign.center, text.valign.baseline])

``\node [draw, fill=yellow, rectangle] at (0, 0) {Boxed text};``

   ::

      tbox = text.text(0, 0, r"Boxed text",
                       [text.halign.boxcenter, text.valign.middle])
      tpath = tbox.bbox().enlarged(3*unit.x_pt).path()
      c.draw(tpath, [deco.filled([color.cmyk.Yellow]), deco.stroked()])
      c.insert(tbox)

``\draw (0, 0) -- (10, 1) node [midway, right] {Hello};``

   ::

      c.stroke(path.line(0, 0, 10, 1),
               [deco.text("Hello",
                          [text.halign.left, text.valign.middle],
                          relarclenpos=0.5)])

Transformations
===============

``\begin{tikzpicture}[x=2cm,y=2cm] ... \end{tikzpicture}``

   ::

      unit.set(uscale=1)

``\begin{scope}[transform canvas={scale=2}] ... \end{scope}``

   ::

      d = canvas.canvas([trafo.scale(2)])
      ...
      c.insert(d)

   .. note ::
      This transformation changes the text size and the line width as well.

``\draw [scale=2] ...;``

   ::

      c.stroke(..., [trafo.scale(2)])

Arrows
======

``\draw [->] (0, 0) -- (1, 1);``

   ::

      c.stroke(path.line(0, 0, 1, 1), [deco.earrow])

   .. seealso ::
      :ref:`arrows`

``\draw [<-] (0, 0) -- (1, 1);``

   ::

      c.stroke(path.line(0, 0, 1, 1), [deco.barrow])

``\draw [<->] (0, 0) -- (1, 1);``

   ::

      c.stroke(path.line(0, 0, 1, 1), [deco.barrow, deco.earrow])

Arrows between text
===================

Assuming the following is already executed::

   A = text.text(0, 0, "A", [text.halign.center, text.vshift.middlezero]); c.insert(A)
   B = text.text(3, 3, "B", [text.halign.center, text.vshift.middlezero]); c.insert(B)

``\draw [->] (A) -- (B);``

   ::

      c.stroke(connector.line(A, B), [deco.earrow])

``\draw [->] (A) to [bend left=30] (B);``

   ::

      c.stroke(connector.arc(A, B, relangle=30), [deco.earrow])

``\draw [->] (A) to [out=45, in=-45] (B);``

   ::

      c.stroke(connector.curve(A, B, absangle1=45, absangle2=135), [deco.earrow])

``\draw [->] (A) -| (B);``

   ::

      c.stroke(connector.twolines(A, B, absangle1=0, absangle2=90), [deco.earrow])

Path intersections
==================

TikZ code::

   \draw [name path=a] (0, 0) circle (2);
   \draw [name path=b] (1, 0) circle (2);
   \draw [name intersections={of=a and b, by={e, f}}, red] (e) -- (f);

PyX code::

   a=path.circle(0, 0, 2)
   c.stroke(a)
   b=path.circle(1, 0, 2)
   c.stroke(b)
   [[a_t0, a_t1], [b_t0, b_t1]] = a.intersect(b)
   e, f=a.at(a_t0), a.at(a_t1)
   c.stroke(path.line(*e, *f), [color.rgb.red])


