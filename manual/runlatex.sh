#!/bin/bash

if [ $# != 1 ] ; then
    echo "runs latex several times to get cross-references right"
    echo "usage: runlatex.sh <file>[.tex]"
    exit 1
fi

file=${1%.tex}
rerunstring=1
latexerror=0
while [[ "$rerunstring" != "" && "$latexerror" == "0" ]]
do
  latex $file.tex
  latexerror=$?
  rerunstring=$(tail -20 $file.log|grep "Rerun to get cross-references right.")
done
exit $latexerror
