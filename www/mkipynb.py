import base64, os, re, sys
import nbformat.v4 as nbf

filename = os.path.splitext(sys.argv[1])[0]

try:
    title, description = open("{}.txt".format(filename), encoding="utf-8").read().split('\n\n', 1)
except IOError:
    title, description = filename, ""
description = description.replace("...", "").replace("'''", "**").replace("''", "*")
bendpattern = re.compile("^!+", re.MULTILINE)
bendcode = '<img src="http://pyx.sourceforge.net/bend.png" align="left">'
description = re.sub(bendpattern, lambda m: bendcode*(m.end()-m.start()), description)
code = open("{}.py".format(filename), encoding="utf-8").read()
code = re.sub('\.writeEPSfile\(("[a-z]+")?\)\n.*writePDFfile\(("[a-z]+")?\)\n.*writeSVGfile\(("[a-z]+")?\)\n', "", code)

nb = nbf.new_notebook()
cells = []
cells.append(nbf.new_markdown_cell(source="# " + title))
cells.append(nbf.new_code_cell(source=code, execution_count=1,
                               outputs=[nbf.new_output(output_type=u'execute_result', execution_count=1,
                                                       data={'image/png': base64.encodebytes(open("{}.png".format(filename), "rb").read()).decode("ascii"),
                                                             'image/svg+xml': open("{}.svg".format(filename), "r", encoding="utf-8").read()})]))
cells.append(nbf.new_markdown_cell(source=description))
nb = nbf.new_notebook(cells=cells, metadata={'language': 'python'})
open("{}.ipynb".format(filename), "w").write(nbf.writes(nb))
