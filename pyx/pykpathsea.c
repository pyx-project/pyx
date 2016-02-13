/*  pykpathsea.c: Copyright 2003-2011 Jörg Lehmann, André Wobst
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

#include <string.h>
#include <Python.h>
#include <kpathsea/tex-file.h>
#include <kpathsea/progname.h>

static PyObject *py_kpse_find_file(PyObject *self, PyObject *args)
{
  char *filename;
  char *format;
  char *completefilename;
  PyObject *returnvalue;
  kpse_file_format_type kpse_file_format;

  if (PyArg_ParseTuple(args, "ss", &filename, &format)) {

    /* if (!strcmp(format, "gf")) kpse_file_format = kpse_gf_format; else */
    /* if (!strcmp(format, "pk")) kpse_file_format = kpse_pk_format; else */
    /* if (!strcmp(format, "bitmap font")) kpse_file_format = kpse_any_glyph_format; else */
    if (!strcmp(format, "tfm")) kpse_file_format = kpse_tfm_format; else
    if (!strcmp(format, "afm")) kpse_file_format = kpse_afm_format; else
    /* if (!strcmp(format, "base")) kpse_file_format = kpse_base_format; else */
    /* if (!strcmp(format, "bib")) kpse_file_format = kpse_bib_format; else */
    /* if (!strcmp(format, "bst")) kpse_file_format = kpse_bst_format; else */
    /* if (!strcmp(format, "cnf")) kpse_file_format = kpse_cnf_format; else */
    /* if (!strcmp(format, "ls-R")) kpse_file_format = kpse_db_format; else */
    /* if (!strcmp(format, "fmt")) kpse_file_format = kpse_fmt_format; else */
    if (!strcmp(format, "map")) kpse_file_format = kpse_fontmap_format; else
    /* if (!strcmp(format, "mem")) kpse_file_format = kpse_mem_format; else */
    /* if (!strcmp(format, "mf")) kpse_file_format = kpse_mf_format; else */
    /* if (!strcmp(format, "mfpool")) kpse_file_format = kpse_mfpool_format; else */
    /* if (!strcmp(format, "mft")) kpse_file_format = kpse_mft_format; else */
    /* if (!strcmp(format, "mp")) kpse_file_format = kpse_mp_format; else */
    /* if (!strcmp(format, "mppool")) kpse_file_format = kpse_mppool_format; else */
    /* if (!strcmp(format, "MetaPost support")) kpse_file_format = kpse_mpsupport_format; else */
    /* if (!strcmp(format, "ocp")) kpse_file_format = kpse_ocp_format; else */
    /* if (!strcmp(format, "ofm")) kpse_file_format = kpse_ofm_format; else */
    /* if (!strcmp(format, "opl")) kpse_file_format = kpse_opl_format; else */
    /* if (!strcmp(format, "otp")) kpse_file_format = kpse_otp_format; else */
    /* if (!strcmp(format, "ovf")) kpse_file_format = kpse_ovf_format; else */
    /* if (!strcmp(format, "ovp")) kpse_file_format = kpse_ovp_format; else */
    if (!strcmp(format, "graphic/figure")) kpse_file_format = kpse_pict_format; else
    /* if (!strcmp(format, "tex")) kpse_file_format = kpse_tex_format; else */
    /* if (!strcmp(format, "TeX system documentation")) kpse_file_format = kpse_texdoc_format; else */
    /* if (!strcmp(format, "texpool")) kpse_file_format = kpse_texpool_format; else */
    /* if (!strcmp(format, "TeX system sources")) kpse_file_format = kpse_texsource_format; else */
    if (!strcmp(format, "PostScript header")) kpse_file_format = kpse_tex_ps_header_format; else
    /* if (!strcmp(format, "Troff fonts")) kpse_file_format = kpse_troff_font_format; else */
    if (!strcmp(format, "type1 fonts")) kpse_file_format = kpse_type1_format; else
    if (!strcmp(format, "vf")) kpse_file_format = kpse_vf_format; else
    if (!strcmp(format, "dvips config")) kpse_file_format = kpse_dvips_config_format; else
    /* if (!strcmp(format, "ist")) kpse_file_format = kpse_ist_format; else */
    /* if (!strcmp(format, "truetype fonts")) kpse_file_format = kpse_truetype_format; else */
    /* if (!strcmp(format, "type42 fonts")) kpse_file_format = kpse_type42_format; else */
    /* if (!strcmp(format, "web2c files")) kpse_file_format = kpse_web2c_format; else */
    /* if (!strcmp(format, "other text files")) kpse_file_format = kpse_program_text_format; else */
    /* if (!strcmp(format, "other binary files")) kpse_file_format = kpse_program_binary_format; else */
    /* if (!strcmp(format, "misc fonts")) kpse_file_format = kpse_miscfonts_format; else */
    return NULL;

    completefilename = kpse_find_file(filename, kpse_file_format, 1);
    returnvalue = Py_BuildValue("s", completefilename);
    /* XXX: free(completefilename); */
    return returnvalue;
  }

  return NULL;

}

/* exported methods */

static PyMethodDef pykpathsea_methods[] = {
  {"find_file", (PyCFunction) py_kpse_find_file,  METH_VARARGS, NULL},
  {NULL, NULL}
};

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "pykpathsea",
        NULL,
        -1,
        pykpathsea_methods,
        NULL,
        NULL,
        NULL,
        NULL
};

PyMODINIT_FUNC
PyInit_pykpathsea(void)
{
  PyObject *module = PyModule_Create(&moduledef);
  if (module == NULL)
    return NULL;
  kpse_set_program_name("dvips", "dvips");
  return module;
}
