default: pyxlogo.png

clean:
	-rm pyxlogo.png

%.eps: %.py
	export PYTHONPATH=$(PWD)/../.. ; cd $(dir $^) ; python $(notdir $^)

%.png: %.eps
	@# -dEPSCrop needs gs version >= 8.0
	gs8.0 -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=ppmraw -sOutputFile=- -r400 $^ > $@.large
	ppmcolormask white $@.large|pnmscale 0.25 2> /dev/null > $@.alpha
	pnmscale 0.25 $@.large|pnmtopng -alpha $@.alpha > $@
	rm $@.large $@.alpha
