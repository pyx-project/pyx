/*  t1strip.c: Copyright 2003 Jörg Lehmann, André Wobst
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
 *  USA.
 */


#include <Python.h>
#include <stdio.h>

FILE *bitfile;
int t1_subset(char*, char *, unsigned char *g);

static PyObject *py_t1strip(PyObject *self, PyObject *args)
{
  PyObject *py_glyphs;
  PyObject *py_file;
  char *fontname;
  unsigned char glyphs[256];

  if (PyArg_ParseTuple(args, "O!sO!", &PyFile_Type, &py_file, &fontname, &PyList_Type, &py_glyphs)) {
      int i;
      int size = PyList_Size(py_glyphs);
      if (size>256) 
         return NULL;

      for (i=0; i<size; i++) {
          PyObject *py_int = PyList_GetItem(py_glyphs, i);
          if (!PyInt_Check(py_int))
              return NULL;
          glyphs[i] = PyInt_AsLong(py_int) ? 1 : 0;
      }
      for (i=size; i<256; i++)
          glyphs[i] = 0;

      bitfile = PyFile_AsFile(py_file);

      t1_subset(fontname, "ad.enc", glyphs);
  }
  else return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

/* exported methods */

static PyMethodDef t1strip_methods[] = {
  {"t1strip", py_t1strip,  METH_VARARGS},
  {NULL, NULL}
};

void initt1strip(void) {
  (void) Py_InitModule("t1strip", t1strip_methods);
}
