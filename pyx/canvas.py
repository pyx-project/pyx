#!/usr/bin/env python

from globex import *

class Canvas(Globex):

  ExportMethods = [ "amove", "aline", "rmove", "rline" ]

  def __init__(self,x,y,unit,name):
    import regsub,sys
    if name==None:
      namepy=sys.argv[0]
      if namepy[-3:]==".py":
        #name=namepy
        #name[-3:]=".ps"  ### slice assignment not supported!
        name=regsub.sub("py$","ps",namepy)
      else:
        name=namepy+".ps"

    print "Canvas.__init__()",x,y,unit,name
    self.name=name

  def amove(self,x,y):
    print "Canvas.amove(",self.name,")",x,y

  def aline(self,x,y):
    print "Canvas.aline(",self.name,")",x,y

  def rmove(self,x,y):
    print "Canvas.rmove(",self.name,")",x,y

  def rline(self,x,y):
    print "Canvas.rline(",self.name,")",x,y

  def __del__(self):
    print "Canvas.__del__(",self.name,")"


def canvas(x,y,unit="1cm",name=None):
  DefaultCanvas=Canvas(x,y,unit,name)
  DefaultCanvas.AddNamespace("DefaultCanvas",GetCallerGlobalNamespace())

