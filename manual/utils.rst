.. module:: utils
   :synopsis: Internal keyword-splitting and parameter-merging utilities

.. only:: doctest

   .. autofunction:: kwsplit

.. _utils:

.. only:: html or latex

   *************************************
   Module :mod:`utils`: Helper utilities
   *************************************

   The :mod:`utils` module provides internal helper functions used by PyX's graph
   and axis classes to support hierarchical keyword argument forwarding (such as
   passing ``x_painter_gridattrs=...`` directly to :class:`graph.graphxy`) and
   cloning configurable component instances via ``__call__``.

   .. function:: kwsplit(kwargs, parts=None, allow_only_split=False)

      Splits a dictionary *kwargs* of keyword arguments at the first underscore
      ``"_"`` into nested dictionaries.

      * Any key of the form ``"<part>_<subkey>"`` (where ``<part>`` is in *parts*,
        or for any ``<part>`` if ``parts=None``) is placed into
        ``split[part][subkey]``.
      * All remaining keys are placed into ``rest[key]`` (unless
        ``allow_only_split=True``, in which case unsplit keys raise a
        :exc:`ValueError`).
      * Returns the tuple ``(split, rest)``.

   .. function:: merge_members_kwargs(obj, kwargs_updates, member_names)

      Builds a merged keyword dictionary starting from the attributes listed in
      *member_names* on *obj* and sequentially applying each dictionary in the
      sequence *kwargs_updates*. Used by axis, painter, and texter ``__call__``
      methods to return a modified clone of an existing component instance.
