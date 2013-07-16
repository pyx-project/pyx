/*  t1code.c: Copyright 2005 Jörg Lehmann
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
#include <stdlib.h>
#include <stdint.h>

#define C1 52845
#define C2 22719

/* 
def decoder(code, r, n):
    c1 = 52845
    c2 = 22719
    data = array.array("B")
    for x in array.array("B", code):
        data.append(x ^ (r >> 8))
        r = ((x + r) * c1 + c2) & 0xffff
    return data.tobytes()[n:]

*/

static PyObject *py_decoder(PyObject *self, PyObject *args)
{
    unsigned char *code;
    int lcode, pr, n;

    if (PyArg_ParseTuple(args, "y#ii", (char **) &code, &lcode, &pr, &n)) {
      unsigned char *data;
      int i;
      unsigned char x;
      uint16_t r=pr;
      PyObject *result;

      if (! (data = (unsigned char *) malloc(lcode)) )
          return NULL;

      for (i=0; i<lcode; i++) {
        x = code[i];
        data[i] = x ^ ( r >> 8);
        r = (x + r) * C1 + C2;
      }

      /* convert result to string stripping first n chars */
      result = PyBytes_FromStringAndSize((const char *)data + n, lcode - n);
      free(data);
      return result;
    }
    else return NULL;

}

/*
def encoder(data, r, random):
    c1 = 52845
    c2 = 22719
    code = array.array("B")
    for x in array.array("B", random+data):
        code.append(x ^ (r >> 8))
        r = ((code[-1] + r) * c1 + c2) & 0xffff;
    return code.tobytes()
*/

static PyObject *py_encoder(PyObject *self, PyObject *args)
{
    unsigned char *data;
    unsigned char *random;
    int ldata, pr, lrandom;

    if (PyArg_ParseTuple(args, "y#iy#", (char **) &data, &ldata, &pr, (char **) &random, &lrandom)) {
      unsigned char *code;
      int i;
      uint16_t r=pr;
      PyObject *result;

      if (! (code = (unsigned char *) malloc(ldata + lrandom)) )
          return NULL;

      for (i=0; i<lrandom; i++) {
        code[i] = random[i] ^ ( r >> 8);
        r = (code[i] + r) * C1 + C2;
      }

      for (i=0; i<ldata; i++) {
        code[i+lrandom] = data[i] ^ ( r >> 8);
        r = (code[i+lrandom] + r) * C1 + C2;
      }

      result = PyBytes_FromStringAndSize((const char *)code, ldata + lrandom);
      free(code);
      return result;
    }
    else return NULL;

}



/* exported methods */

static PyMethodDef t1code_methods[] = {
    {"decoder", py_decoder,  METH_VARARGS, NULL},
    {"encoder", py_encoder,  METH_VARARGS, NULL},
    {NULL, NULL}
};

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "_t1code",
        NULL,
        -1,
        t1code_methods,
        NULL,
        NULL,
        NULL,
        NULL
};

PyMODINIT_FUNC
PyInit__t1code(void)
{
  PyObject *module = PyModule_Create(&moduledef);
  return module;
}

