#!/usr/bin/env python

from globex import *

class Graph(Globex):

  ExportMethods = [ "addaxis" ]
  Axis = [ ]

  def __init__(self,x,y,canvas,**args):
    # args: title, background???
    print "Graph.__init__()",x,y,canvas,args
    self.canvas=canvas

  def addaxis(self,type,axis=None):
    # type is something like "x", "x1", "x2", "x3", ... or "y" and others
    if axis == None:
      exec "newaxis=DefaultAxis" in GetCallerGlobalNamespace(),locals()
      axis=newaxis
    print "Graph.addaxis()",axis
    axis.graphvar_type=type
    self.Axis = self.Axis + [ axis, ]

  def Draw(self):
    # that's the funny part ... ;-)
    # among others we're calling routines from axis here
    pass

  def __del__(self):
    self.Draw()
    print "Graph.__del__()"


def graph(x,y,**args):
  exec "canvas=DefaultCanvas" in GetCallerGlobalNamespace(),locals()
  DefaultGraph=apply(Graph,(x,y,canvas,),args);
  DefaultGraph.AddNamespace("DefaultGraph",GetCallerGlobalNamespace())

