/*  pykpathsea.c: Copyright 2003 Jörg Lehmann, André Wobst
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
#include <kpathsea/tex-file.h>

static PyObject *py_kpse_find_file(PyObject *self, PyObject *args)
{
  char *filename;
  char *completefilename;
  PyObject *returnvalue;

  if (PyArg_ParseTuple(args, "s", &filename)) {
    completefilename = kpse_find_file(filename, kpse_type1_format, 1)

    returnvalue = PyBuildValue("s", completefilename);
    // XXX: free(completefilename);
    return returnvalue;
  }

  return NULL;

}

/* exported methods */

static PyMethodDef pykpathsea_methods[] = {
  {"find_file", py_kpse_find_file,  METH_VARARGS},
  {NULL, NULL}
};

void initpykpathsea(void)
{
  (void) Py_InitModule("_pykpathsea", pykpathsea_methods);
  kpse_set_program_name("dvips", "dvips");
}
