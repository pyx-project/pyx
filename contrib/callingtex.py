#!/usr/bin/env python
# This file should help users tracking problems with their TeX installation
# It spits out a lot of information about the Python installation, the PyX
# installation and the environment in which PyX will try to use TeX/LaTeX.
#
import sys, os, subprocess
#sys.path.insert(0, "..")
#sys.path.insert(0, "../build/lib.linux-x86_64-2.5")
import pyx

#pyx.text.set(fontmaps="psfonts.map psfonts.cmz")

def test_installation():
    try:
        from pyx.pykpathsea import _pykpathsea
        compiled_pykpathsea = True
    except ImportError:
        compiled_pykpathsea = False

    print "Platform is %s" % sys.platform
    print "Python installation prefix is %s" % sys.prefix
    print "Python executable is %s" % sys.executable
    print "PyX comes from %s" % pyx.__file__
    print "PyX version %s" % pyx.__version__
    if compiled_pykpathsea:
        print "PyX pykpathsea compiled from C module"
    else:
        print "PyX pykpathsea python module used"
    print

def test_commands():
    for command in [r"echo $0 \"$*\"",
                    r"echo $SHELL",
                    r"echo $BASH_SUBSHELL",
                    r"echo $-",
                    r"echo $ENV",
                    r"echo $BASH_ENV",
                    r"echo $TEXMFCNF",
                    r"echo $_",
                    r"echo $PATH",
                    r"which kpsewhich",
                    r"which tex",
                    r"which latex",
                    r"file `which kpsewhich`",
                    r"file `which tex`",
                    r"file `which latex`",
                    ]:
        stdin, stdout, stderr = os.popen3(command)
        print "\"%22s\" -->" % (command),
        for line in stdout:
            print " %s" % line,
        for x in [stdin, stdout, stderr]:
            x.close()
    print

def test_fontmaps():
    allformats = []
    allnames = {}
    for formatstr in [
      "pyx.pykpathsea.kpse_gf_format",
      "pyx.pykpathsea.kpse_pk_format",
#     "pyx.pykpathsea.kpse_any_glyph_format", # gives segmentation fault
      "pyx.pykpathsea.kpse_tfm_format",
      "pyx.pykpathsea.kpse_afm_format",
      "pyx.pykpathsea.kpse_base_format",
      "pyx.pykpathsea.kpse_bib_format",
      "pyx.pykpathsea.kpse_bst_format",
      "pyx.pykpathsea.kpse_cnf_format",
      "pyx.pykpathsea.kpse_db_format",
      "pyx.pykpathsea.kpse_fmt_format",
      "pyx.pykpathsea.kpse_fontmap_format",
      "pyx.pykpathsea.kpse_mem_format",
      "pyx.pykpathsea.kpse_mf_format",
      "pyx.pykpathsea.kpse_mfpool_format",
      "pyx.pykpathsea.kpse_mft_format",
      "pyx.pykpathsea.kpse_mp_format",
      "pyx.pykpathsea.kpse_mppool_format",
      "pyx.pykpathsea.kpse_mpsupport_format",
      "pyx.pykpathsea.kpse_ocp_format",
      "pyx.pykpathsea.kpse_ofm_format",
      "pyx.pykpathsea.kpse_opl_format",
      "pyx.pykpathsea.kpse_otp_format",
      "pyx.pykpathsea.kpse_ovf_format",
      "pyx.pykpathsea.kpse_ovp_format",
#     "pyx.pykpathsea.kpse_pict_format", # unknown in python module
      "pyx.pykpathsea.kpse_tex_format",
      "pyx.pykpathsea.kpse_texdoc_format",
      "pyx.pykpathsea.kpse_texpool_format",
      "pyx.pykpathsea.kpse_texsource_format",
      "pyx.pykpathsea.kpse_tex_ps_header_format",
#     "pyx.pykpathsea.kpse_troff_font_format", (takes too long)
      "pyx.pykpathsea.kpse_type1_format",
      "pyx.pykpathsea.kpse_vf_format",
      "pyx.pykpathsea.kpse_dvips_config_format",
      "pyx.pykpathsea.kpse_ist_format",
      "pyx.pykpathsea.kpse_truetype_format",
      "pyx.pykpathsea.kpse_type42_format",
      "pyx.pykpathsea.kpse_web2c_format",
      "pyx.pykpathsea.kpse_program_text_format",
      "pyx.pykpathsea.kpse_program_binary_format",
      "pyx.pykpathsea.kpse_miscfonts_format",
      "pyx.pykpathsea.kpse_web_format",
      "pyx.pykpathsea.kpse_cweb_format",
      "pyx.pykpathsea.kpse_enc_format",
      "pyx.pykpathsea.kpse_cmap_format",
      "pyx.pykpathsea.kpse_subfont_definition_format",
      "pyx.pykpathsea.kpse_opentype_format",
      "pyx.pykpathsea.kpse_pdftex_config_format",
      "pyx.pykpathsea.kpse_lig_format",
      "pyx.pykpathsea.kpse_texmfscripts_format",
      "pyx.pykpathsea.kpse_lua_format",
      "pyx.pykpathsea.kpse_font_feature_format",
      "pyx.pykpathsea.kpse_cid_maps_format",
      "pyx.pykpathsea.kpse_mlbib_format",
      "pyx.pykpathsea.kpse_mlbst_format"]:
        try:
            allformats.append(eval(formatstr))
            allnames[eval(formatstr)] = formatstr
        except AttributeError:
            continue

    if pyx.__version__ in ["0.10"]:
        fontmaps = pyx.text.defaulttexrunner.fontmaps.split()
    else:
        fontmaps = []
        fontmaps += pyx.config.getlist("text", "pdffontmaps", ["pdftex.map"])
        fontmaps += pyx.config.getlist("text", "psfontmaps", ["psfonts.map"])
    for fontmap in fontmaps:
        found = 0
        for form in allformats:
            mappath = pyx.pykpathsea.find_file(fontmap, form)
            if mappath:
                found = 1
                print "\"%s\" found at \"%s\" as format \"%s\"" % (fontmap, mappath, allnames[form])
        if not found:
            print "\"%s\" not found" % fontmap
    print

test_installation()
test_commands()
test_fontmaps()

