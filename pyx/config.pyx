% teTeX's config.ps. Thomas Esser, 1998, public domain.

% Memory available. Download the three-line PostScript file:
%   %! Hey, we're PostScript
%   /Times-Roman findfont 30 scalefont setfont 144 432 moveto
%   vmstatus exch sub 40 string cvs show pop showpage
% to determine this number. (It will be the only thing printed.)
m 3500000

% How to print, maybe with lp instead lpr, etc. If commented-out, output
% will go into a file by default.
o

% Default resolution of this device, in dots per inch.
D 600
X 600
Y 600

% Metafont mode.  (This is completely different from the -M command-line
% option, which controls whether MakeTeXPK is invoked.)  Get
% @url{ftp://ftp.tug.org/tex/modes.mf} for a list of mode names.  This mode
% and the D number above must agree, or MakeTeXPK will get confused.
M ljfour

% Also look for this list of resolutions.
R 300 600

% Correct printer offset. You can use testpage.tex from the LaTeX
% distribution to find these numbers.
O 0pt,0pt

% With a high resolution and a RISC cpu, better to compress the bitmaps.
% PS files are much more compact, but can sometimes cause trouble.
Z

% Partially download Type 1 fonts by default.  Only reason not to do
% this is if you encounter bugs.  (Please report them to
% @email{tex-k@@mail.tug.org} if you do.)
% j

% Configuration of postscript type 1 fonts:
p psfonts.map

% This shows how to add your own map file.
% Remove the comment and adjust the name:
% p +myfonts.map

@ a4 210mm 297mm
@+ %%Nothing

@ A4size 210mm 297mm
@+ %%Nothing

@ letterSize 8.5in 11in
@+ %%Nothing

@ letter 8.5in 11in
@+ %%Nothing

@ legal 8.5in 14in
@+ %%Nothing

@ ledger 17in 11in
@+ %%Nothing

@ tabloid 11in 17in
@+ %%Nothing

@ a3 297mm 420mm
@+ %%Nothing

@ unknown 0in 0in
@+ %%Nothing
