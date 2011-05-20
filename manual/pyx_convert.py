# -*- encoding: utf-8 -*-

# convert PyX documents to rst using http://svn.python.org/projects/doctools/converter/converter

import glob, os
from converter import latexparser, docnodes, convert_file

latexparser.DocParser.handle_PyX = lambda(self): docnodes.TextNode('PyX')
latexparser.DocParser.handle_LaTeX = lambda(self): docnodes.TextNode('LaTeX')
latexparser.DocParser.handle_TeX = lambda(self): docnodes.TextNode('TeX')
latexparser.DocParser.handle_medskip = lambda(self): docnodes.EmptyNode()
latexparser.DocParser.handle_cleardoublepage = lambda(self): docnodes.EmptyNode()
latexparser.DocParser.handle_textquotedbl = lambda(self): docnodes.TextNode('"')
latexparser.DocParser.handle_dots = lambda(self): docnodes.TextNode(u'…')
latexparser.DocParser.handle_smallskip = lambda(self): docnodes.EmptyNode()
latexparser.DocParser.handle_includegraphics = lambda(self): docnodes.CommentNode('DUMMY\n.. _fig_label:\n.. figure:: %s.*\n   :align:  center' % self.parse_args('\\includegraphics', 'M')[0].text)

for filename in glob.glob('*.tex'):
    infile = filename
    outfile = filename.replace('.tex', '.rst')
    convert_file(infile, outfile)
