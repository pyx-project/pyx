#!/usr/bin/env python

# This file is obsolete (at least for the moment).
# Axis are part of graph.py and might be separated later ...

from globex import *

class Axis(Globex):
  # place for common axis methods ...
  pass

class LinAxis(Axis):
  
  ExportMethods = [ "ticks", "subticks", "labels", "sublabels" ]

  def __init__(self,**args):
    # args: title, from, to
    print "Axis.__init__()",args

  def ticks(self,**args):
    # args: from, to, steps
    print "Axis.ticks()",args

  def subticks(self,**args):
    # args: from, to, steps
    print "Axis.subticks()",args

  def labels(self,**args):
    # args: from, to, steps, formater, list
    print "Axis.labels()",args

  def sublabels(self,**args):
    # args: from, to, steps, formater, list
    print "Axis.sublabels()",args

  def __del__(self):
    print "Axis.__del__()"

def linaxis(**args):
  DefaultAxis=apply(LinAxis,(),args);
  DefaultAxis.AddNamespace("DefaultAxis",GetCallerGlobalNamespace())

