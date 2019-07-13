PYTHON ?= python3
GS ?= gs

pngfiles = example.png bend.png pyxlogo.png

default: $(pngfiles)

clean:
	-rm $(pngfiles)

%.png: %.py
	$(PYTHON) $^
	$(GS) -r100 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=pngalpha -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -sOutputFile=$@ $*.eps
	rm $*.eps
