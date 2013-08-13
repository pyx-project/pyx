import base64, os, re, sys
from IPython.nbformat.current import reads, write, new_output

filename = os.path.splitext(sys.argv[1])[0]

try:
    title, description = open("{}.txt".format(filename), encoding="utf-8").read().split('\n\n', 1)
except IOError:
    title, description = filename, ""
description = description.replace("...", "").replace("'''", "**").replace("''", "*")
bendpattern = re.compile("^!+", re.MULTILINE)
bendcode = "![bend](http://pyx.sourceforge.net/bend.png)"
description = re.sub(bendpattern, lambda m: "![bend](http://pyx.sourceforge.net/bend.png)"*(m.end()-m.start()), description)
code = open("{}.py".format(filename), encoding="utf-8").read()
code = re.sub('\.writeEPSfile\(("[a-z]+")?\)\n.*writePDFfile\(("[a-z]+")?\)', "", code)
input = """# <headingcell level=1>
{title}
# <codecell>
{code}
# <markdowncell>
{description}
# <codecell>
""".format(title=title, code=code, description=description)

nb = reads(input, "py")
codecell, = [cell for ws in nb.worksheets for cell in ws.cells if cell.cell_type == "code"]
codecell.outputs.append(new_output(output_type="pyout",
                                   output_png=base64.encodebytes(open("{}.png".format(filename), "rb").read())))
write(nb, open("{}.ipynb".format(filename), "w"), "ipynb")
