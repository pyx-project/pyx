#!/usr/bin/env python

# global export class

class GlobexSaveStruc:
  def __init__(self, DefaultName, Namespace):
    self.DefaultName = DefaultName
    self.Namespace = Namespace

class Globex:

  ExportMethods = [ ]
  Names = [ ]

  def AddNamespace(self, DefaultName, Namespace):
    Name = GlobexSaveStruc(DefaultName, Namespace)
    self.Names = self.Names + [ Name, ]
    exec "global "+DefaultName+";"\
         +DefaultName+"=self" in Namespace,locals()
    for ExportMethod in self.ExportMethods:
      exec "global "+ExportMethod+";"\
           +ExportMethod+"="+DefaultName+"."+ExportMethod in Namespace
      
  def DelNamespace(self,DefaultName,Namespace):
    exec "global "+DefaultName+";"\
         +"del "+DefaultName in Namespace
    for ExportMethod in self.ExportMethods:
      exec "global "+ExportMethod+";del "+ExportMethod in Namespace
 
  def DelNamespaces(self):
    for Name in self.Names:
      self.DelNamespace(Name.DefaultName,Name.Namespace)
 
def GetCallerGlobalNamespace():
  import sys
  try:
    raise ZeroDivisionError
  except ZeroDivisionError:
    return sys.exc_info()[2].tb_frame.f_back.f_back.f_globals

