#!/bin/bash
rerunstring=1
latexerror=0
while [[ "$rerunstring" != "" && "$latexerror" == "0" ]]
do
  latex manual.tex
  latexerror=$?
  rerunstring=$(tail -20 manual.log|grep "Rerun to get cross-references right.")
done
exit $latexerror
