====================
Other plotting tasks
====================

How can I rotate text?
======================

Text can be written at an arbitrary angle by specifying the appropriate
transformation as an attribute. The command ::

   c.text(0, 0, "Text", [trafo.rotate(60)])

will write at an angle of 60 degrees relative to the horizontal axis. If no
pivot is specified (like in this example), the text is rotated around the
reference point given in the first two arguments of ``text``. In the
following example, the pivot coincides with the center of the text::

   c.text(0, 0, "Text", [text.halign.center,text.valign.middle,trafo.rotate(60)])

How can I clip a canvas?
========================

In order to use only a part of a larger canvas, one may want to clip it. This
can be done by creating a clipping object which is used when creating a canvas
instance::

   clippath = path.circle(0.,0.,1.)
   clipobject = canvas.clip(clippath)
   c = canvas.canvas([clipobject])

In this example, the clipping path used to define the clipping object is a 
circle.
