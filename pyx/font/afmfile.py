# -*- encoding: utf-8 -*-
#
#
# Copyright (C) 2006-2011 Jörg Lehmann <joergl@users.sourceforge.net>
# Copyright (C) 2007-2011 André Wobst <wobsta@users.sourceforge.net>
#
# This file is part of PyX (http://pyx.sourceforge.net/).
#
# PyX is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# PyX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyX; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import string
import metric

unicodestring = {u" ": "space",
                 u"!": "exclam",
                 u"\"": "quotedbl",
                 u"#": "numbersign",
                 u"$": "dollar",
                 u"%": "percent",
                 u"&": "ampersand",
                 u"'": "quotesingle",
                 u"(": "parenleft",
                 u")": "parenright",
                 u"*": "asterisk",
                 u"+": "plus",
                 u",": "comma",
                 u"-": "hyphen",
                 u".": "period",
                 u"/": "slash",
                 u"0": "zero",
                 u"1": "one",
                 u"2": "two",
                 u"3": "three",
                 u"4": "four",
                 u"5": "five",
                 u"6": "six",
                 u"7": "seven",
                 u"8": "eight",
                 u"9": "nine",
                 u":": "colon",
                 u";": "semicolon",
                 u"<": "less",
                 u"=": "equal",
                 u">": "greater",
                 u"?": "question",
                 u"@": "at",
                 u"A": "A",
                 u"B": "B",
                 u"C": "C",
                 u"D": "D",
                 u"E": "E",
                 u"F": "F",
                 u"G": "G",
                 u"H": "H",
                 u"I": "I",
                 u"J": "J",
                 u"K": "K",
                 u"L": "L",
                 u"M": "M",
                 u"N": "N",
                 u"O": "O",
                 u"P": "P",
                 u"Q": "Q",
                 u"R": "R",
                 u"S": "S",
                 u"T": "T",
                 u"U": "U",
                 u"V": "V",
                 u"W": "W",
                 u"X": "X",
                 u"Y": "Y",
                 u"Z": "Z",
                 u"[": "bracketleft",
                 u"\\": "backslash",
                 u"]": "bracketright",
                 u"^": "asciicircum",
                 u"_": "underscore",
                 u"`": "grave",
                 u"a": "a",
                 u"b": "b",
                 u"c": "c",
                 u"d": "d",
                 u"e": "e",
                 u"f": "f",
                 u"g": "g",
                 u"h": "h",
                 u"i": "i",
                 u"j": "j",
                 u"k": "k",
                 u"l": "l",
                 u"m": "m",
                 u"n": "n",
                 u"o": "o",
                 u"p": "p",
                 u"q": "q",
                 u"r": "r",
                 u"s": "s",
                 u"t": "t",
                 u"u": "u",
                 u"v": "v",
                 u"w": "w",
                 u"x": "x",
                 u"y": "y",
                 u"z": "z",
                 u"{": "braceleft",
                 u"|": "bar",
                 u"}": "braceright",
                 u"~": "asciitilde",
                 u"\xa0": "space",
                 u"\xa1": "exclamdown",
                 u"\xa2": "cent",
                 u"\xa3": "sterling",
                 u"\xa4": "currency",
                 u"\xa5": "yen",
                 u"\xa6": "brokenbar",
                 u"\xa7": "section",
                 u"\xa8": "dieresis",
                 u"\xa9": "copyright",
                 u"\xaa": "ordfeminine",
                 u"\xab": "guillemotleft",
                 u"\xac": "logicalnot",
                 u"\xad": "hyphen",
                 u"\xae": "registered",
                 u"\xaf": "macron",
                 u"\xb0": "degree",
                 u"\xb1": "plusminus",
                 u"\xb4": "acute",
                 u"\xb6": "paragraph",
                 u"\xb7": "periodcentered",
                 u"\xb8": "cedilla",
                 u"\xba": "ordmasculine",
                 u"\xbb": "guillemotright",
                 u"\xbc": "onequarter",
                 u"\xbd": "onehalf",
                 u"\xbe": "threequarters",
                 u"\xbf": "questiondown",
                 u"\xc0": "Agrave",
                 u"\xc1": "Aacute",
                 u"\xc2": "Acircumflex",
                 u"\xc3": "Atilde",
                 u"\xc4": "Adieresis",
                 u"\xc5": "Aring",
                 u"\xc6": "AE",
                 u"\xc7": "Ccedilla",
                 u"\xc8": "Egrave",
                 u"\xc9": "Eacute",
                 u"\xca": "Ecircumflex",
                 u"\xcb": "Edieresis",
                 u"\xcc": "Igrave",
                 u"\xcd": "Iacute",
                 u"\xce": "Icircumflex",
                 u"\xcf": "Idieresis",
                 u"\xd0": "Eth",
                 u"\xd1": "Ntilde",
                 u"\xd2": "Ograve",
                 u"\xd3": "Oacute",
                 u"\xd4": "Ocircumflex",
                 u"\xd5": "Otilde",
                 u"\xd6": "Odieresis",
                 u"\xd7": "multiply",
                 u"\xd8": "Oslash",
                 u"\xd9": "Ugrave",
                 u"\xda": "Uacute",
                 u"\xdb": "Ucircumflex",
                 u"\xdc": "Udieresis",
                 u"\xdd": "Yacute",
                 u"\xde": "Thorn",
                 u"\xdf": "germandbls",
                 u"\xe0": "agrave",
                 u"\xe1": "aacute",
                 u"\xe2": "acircumflex",
                 u"\xe3": "atilde",
                 u"\xe4": "adieresis",
                 u"\xe5": "aring",
                 u"\xe6": "ae",
                 u"\xe7": "ccedilla",
                 u"\xe8": "egrave",
                 u"\xe9": "eacute",
                 u"\xea": "ecircumflex",
                 u"\xeb": "edieresis",
                 u"\xec": "igrave",
                 u"\xed": "iacute",
                 u"\xee": "icircumflex",
                 u"\xef": "idieresis",
                 u"\xf0": "eth",
                 u"\xf1": "ntilde",
                 u"\xf2": "ograve",
                 u"\xf3": "oacute",
                 u"\xf4": "ocircumflex",
                 u"\xf5": "otilde",
                 u"\xf6": "odieresis",
                 u"\xf7": "divide",
                 u"\xf8": "oslash",
                 u"\xf9": "ugrave",
                 u"\xfa": "uacute",
                 u"\xfb": "ucircumflex",
                 u"\xfc": "udieresis",
                 u"\xfd": "yacute",
                 u"\xfe": "thorn",
                 u"\xff": "ydieresis",
                 u"\u0100": "Amacron",
                 u"\u0101": "amacron",
                 u"\u0102": "Abreve",
                 u"\u0103": "abreve",
                 u"\u0104": "Aogonek",
                 u"\u0105": "aogonek",
                 u"\u0106": "Cacute",
                 u"\u0107": "cacute",
                 u"\u0108": "Ccircumflex",
                 u"\u0109": "ccircumflex",
                 u"\u010a": "Cdotaccent",
                 u"\u010b": "cdotaccent",
                 u"\u010c": "Ccaron",
                 u"\u010d": "ccaron",
                 u"\u010e": "Dcaron",
                 u"\u010f": "dcaron",
                 u"\u0110": "Dcroat",
                 u"\u0111": "dcroat",
                 u"\u0112": "Emacron",
                 u"\u0113": "emacron",
                 u"\u0114": "Ebreve",
                 u"\u0115": "ebreve",
                 u"\u0116": "Edotaccent",
                 u"\u0117": "edotaccent",
                 u"\u0118": "Eogonek",
                 u"\u0119": "eogonek",
                 u"\u011a": "Ecaron",
                 u"\u011b": "ecaron",
                 u"\u011c": "Gcircumflex",
                 u"\u011d": "gcircumflex",
                 u"\u011e": "Gbreve",
                 u"\u011f": "gbreve",
                 u"\u0120": "Gdotaccent",
                 u"\u0121": "gdotaccent",
                 u"\u0122": "Gcommaaccent",
                 u"\u0123": "gcommaaccent",
                 u"\u0124": "Hcircumflex",
                 u"\u0125": "hcircumflex",
                 u"\u0126": "Hbar",
                 u"\u0127": "hbar",
                 u"\u0128": "Itilde",
                 u"\u0129": "itilde",
                 u"\u012a": "Imacron",
                 u"\u012b": "imacron",
                 u"\u012c": "Ibreve",
                 u"\u012d": "ibreve",
                 u"\u012e": "Iogonek",
                 u"\u012f": "iogonek",
                 u"\u0130": "Idotaccent",
                 u"\u0131": "dotlessi",
                 u"\u0132": "IJ",
                 u"\u0133": "ij",
                 u"\u0134": "Jcircumflex",
                 u"\u0135": "jcircumflex",
                 u"\u0136": "Kcommaaccent",
                 u"\u0137": "kcommaaccent",
                 u"\u0138": "kgreenlandic",
                 u"\u0139": "Lacute",
                 u"\u013a": "lacute",
                 u"\u013b": "Lcommaaccent",
                 u"\u013c": "lcommaaccent",
                 u"\u013d": "Lcaron",
                 u"\u013e": "lcaron",
                 u"\u013f": "Ldot",
                 u"\u0140": "ldot",
                 u"\u0141": "Lslash",
                 u"\u0142": "lslash",
                 u"\u0143": "Nacute",
                 u"\u0144": "nacute",
                 u"\u0145": "Ncommaaccent",
                 u"\u0146": "ncommaaccent",
                 u"\u0147": "Ncaron",
                 u"\u0148": "ncaron",
                 u"\u0149": "napostrophe",
                 u"\u014a": "Eng",
                 u"\u014b": "eng",
                 u"\u014c": "Omacron",
                 u"\u014d": "omacron",
                 u"\u014e": "Obreve",
                 u"\u014f": "obreve",
                 u"\u0150": "Ohungarumlaut",
                 u"\u0151": "ohungarumlaut",
                 u"\u0152": "OE",
                 u"\u0153": "oe",
                 u"\u0154": "Racute",
                 u"\u0155": "racute",
                 u"\u0156": "Rcommaaccent",
                 u"\u0157": "rcommaaccent",
                 u"\u0158": "Rcaron",
                 u"\u0159": "rcaron",
                 u"\u015a": "Sacute",
                 u"\u015b": "sacute",
                 u"\u015c": "Scircumflex",
                 u"\u015d": "scircumflex",
                 u"\u015e": "Scedilla",
                 u"\u015f": "scedilla",
                 u"\u0160": "Scaron",
                 u"\u0161": "scaron",
                 u"\u0162": "Tcommaaccent",
                 u"\u0163": "tcommaaccent",
                 u"\u0164": "Tcaron",
                 u"\u0165": "tcaron",
                 u"\u0166": "Tbar",
                 u"\u0167": "tbar",
                 u"\u0168": "Utilde",
                 u"\u0169": "utilde",
                 u"\u016a": "Umacron",
                 u"\u016b": "umacron",
                 u"\u016c": "Ubreve",
                 u"\u016d": "ubreve",
                 u"\u016e": "Uring",
                 u"\u016f": "uring",
                 u"\u0170": "Uhungarumlaut",
                 u"\u0171": "uhungarumlaut",
                 u"\u0172": "Uogonek",
                 u"\u0173": "uogonek",
                 u"\u0174": "Wcircumflex",
                 u"\u0175": "wcircumflex",
                 u"\u0176": "Ycircumflex",
                 u"\u0177": "ycircumflex",
                 u"\u0178": "Ydieresis",
                 u"\u0179": "Zacute",
                 u"\u017a": "zacute",
                 u"\u017b": "Zdotaccent",
                 u"\u017c": "zdotaccent",
                 u"\u017d": "Zcaron",
                 u"\u017e": "zcaron",
                 u"\u017f": "longs",
                 u"\u0192": "florin",
                 u"\u01a0": "Ohorn",
                 u"\u01a1": "ohorn",
                 u"\u01af": "Uhorn",
                 u"\u01b0": "uhorn",
                 u"\u01e6": "Gcaron",
                 u"\u01e7": "gcaron",
                 u"\u01fa": "Aringacute",
                 u"\u01fb": "aringacute",
                 u"\u01fc": "AEacute",
                 u"\u01fd": "aeacute",
                 u"\u01fe": "Oslashacute",
                 u"\u01ff": "oslashacute",
                 u"\u0218": "Scommaaccent",
                 u"\u0219": "scommaaccent",
                 u"\u02bc": "afii57929",
                 u"\u02bd": "afii64937",
                 u"\u02c6": "circumflex",
                 u"\u02c7": "caron",
                 u"\u02c9": "macron",
                 u"\u02d8": "breve",
                 u"\u02d9": "dotaccent",
                 u"\u02da": "ring",
                 u"\u02db": "ogonek",
                 u"\u02dc": "tilde",
                 u"\u02dd": "hungarumlaut",
                 u"\u0300": "gravecomb",
                 u"\u0301": "acutecomb",
                 u"\u0303": "tildecomb",
                 u"\u0309": "hookabovecomb",
                 u"\u0323": "dotbelowcomb",
                 u"\u0384": "tonos",
                 u"\u0385": "dieresistonos",
                 u"\u0386": "Alphatonos",
                 u"\u0387": "anoteleia",
                 u"\u0388": "Epsilontonos",
                 u"\u0389": "Etatonos",
                 u"\u038a": "Iotatonos",
                 u"\u038c": "Omicrontonos",
                 u"\u038e": "Upsilontonos",
                 u"\u038f": "Omegatonos",
                 u"\u0390": "iotadieresistonos",
                 u"\u0391": "Alpha",
                 u"\u0392": "Beta",
                 u"\u0393": "Gamma",
                 u"\u0394": "Delta",
                 u"\u0395": "Epsilon",
                 u"\u0396": "Zeta",
                 u"\u0397": "Eta",
                 u"\u0398": "Theta",
                 u"\u0399": "Iota",
                 u"\u039a": "Kappa",
                 u"\u039b": "Lambda",
                 u"\u039c": "Mu",
                 u"\u039d": "Nu",
                 u"\u039e": "Xi",
                 u"\u039f": "Omicron",
                 u"\u03a0": "Pi",
                 u"\u03a1": "Rho",
                 u"\u03a3": "Sigma",
                 u"\u03a4": "Tau",
                 u"\u03a5": "Upsilon",
                 u"\u03a6": "Phi",
                 u"\u03a7": "Chi",
                 u"\u03a8": "Psi",
                 u"\u03a9": "Omega",
                 u"\u03aa": "Iotadieresis",
                 u"\u03ab": "Upsilondieresis",
                 u"\u03ac": "alphatonos",
                 u"\u03ad": "epsilontonos",
                 u"\u03ae": "etatonos",
                 u"\u03af": "iotatonos",
                 u"\u03b0": "upsilondieresistonos",
                 u"\u03b1": "alpha",
                 u"\u03b2": "beta",
                 u"\u03b3": "gamma",
                 u"\u03b4": "delta",
                 u"\u03b5": "epsilon",
                 u"\u03b6": "zeta",
                 u"\u03b7": "eta",
                 u"\u03b8": "theta",
                 u"\u03b9": "iota",
                 u"\u03ba": "kappa",
                 u"\u03bb": "lambda",
                 u"\u03bc": "mu",
                 u"\u03bd": "nu",
                 u"\u03be": "xi",
                 u"\u03bf": "omicron",
                 u"\u03c0": "pi",
                 u"\u03c1": "rho",
                 u"\u03c2": "sigma1",
                 u"\u03c3": "sigma",
                 u"\u03c4": "tau",
                 u"\u03c5": "upsilon",
                 u"\u03c6": "phi",
                 u"\u03c7": "chi",
                 u"\u03c8": "psi",
                 u"\u03c9": "omega",
                 u"\u03ca": "iotadieresis",
                 u"\u03cb": "upsilondieresis",
                 u"\u03cc": "omicrontonos",
                 u"\u03cd": "upsilontonos",
                 u"\u03ce": "omegatonos",
                 u"\u03d1": "theta1",
                 u"\u03d2": "Upsilon1",
                 u"\u03d5": "phi1",
                 u"\u03d6": "omega1",
                 u"\u0401": "afii10023",
                 u"\u0402": "afii10051",
                 u"\u0403": "afii10052",
                 u"\u0404": "afii10053",
                 u"\u0405": "afii10054",
                 u"\u0406": "afii10055",
                 u"\u0407": "afii10056",
                 u"\u0408": "afii10057",
                 u"\u0409": "afii10058",
                 u"\u040a": "afii10059",
                 u"\u040b": "afii10060",
                 u"\u040c": "afii10061",
                 u"\u040e": "afii10062",
                 u"\u040f": "afii10145",
                 u"\u0410": "afii10017",
                 u"\u0411": "afii10018",
                 u"\u0412": "afii10019",
                 u"\u0413": "afii10020",
                 u"\u0414": "afii10021",
                 u"\u0415": "afii10022",
                 u"\u0416": "afii10024",
                 u"\u0417": "afii10025",
                 u"\u0418": "afii10026",
                 u"\u0419": "afii10027",
                 u"\u041a": "afii10028",
                 u"\u041b": "afii10029",
                 u"\u041c": "afii10030",
                 u"\u041d": "afii10031",
                 u"\u041e": "afii10032",
                 u"\u041f": "afii10033",
                 u"\u0420": "afii10034",
                 u"\u0421": "afii10035",
                 u"\u0422": "afii10036",
                 u"\u0423": "afii10037",
                 u"\u0424": "afii10038",
                 u"\u0425": "afii10039",
                 u"\u0426": "afii10040",
                 u"\u0427": "afii10041",
                 u"\u0428": "afii10042",
                 u"\u0429": "afii10043",
                 u"\u042a": "afii10044",
                 u"\u042b": "afii10045",
                 u"\u042c": "afii10046",
                 u"\u042d": "afii10047",
                 u"\u042e": "afii10048",
                 u"\u042f": "afii10049",
                 u"\u0430": "afii10065",
                 u"\u0431": "afii10066",
                 u"\u0432": "afii10067",
                 u"\u0433": "afii10068",
                 u"\u0434": "afii10069",
                 u"\u0435": "afii10070",
                 u"\u0436": "afii10072",
                 u"\u0437": "afii10073",
                 u"\u0438": "afii10074",
                 u"\u0439": "afii10075",
                 u"\u043a": "afii10076",
                 u"\u043b": "afii10077",
                 u"\u043c": "afii10078",
                 u"\u043d": "afii10079",
                 u"\u043e": "afii10080",
                 u"\u043f": "afii10081",
                 u"\u0440": "afii10082",
                 u"\u0441": "afii10083",
                 u"\u0442": "afii10084",
                 u"\u0443": "afii10085",
                 u"\u0444": "afii10086",
                 u"\u0445": "afii10087",
                 u"\u0446": "afii10088",
                 u"\u0447": "afii10089",
                 u"\u0448": "afii10090",
                 u"\u0449": "afii10091",
                 u"\u044a": "afii10092",
                 u"\u044b": "afii10093",
                 u"\u044c": "afii10094",
                 u"\u044d": "afii10095",
                 u"\u044e": "afii10096",
                 u"\u044f": "afii10097",
                 u"\u0451": "afii10071",
                 u"\u0452": "afii10099",
                 u"\u0453": "afii10100",
                 u"\u0454": "afii10101",
                 u"\u0455": "afii10102",
                 u"\u0456": "afii10103",
                 u"\u0457": "afii10104",
                 u"\u0458": "afii10105",
                 u"\u0459": "afii10106",
                 u"\u045a": "afii10107",
                 u"\u045b": "afii10108",
                 u"\u045c": "afii10109",
                 u"\u045e": "afii10110",
                 u"\u045f": "afii10193",
                 u"\u0462": "afii10146",
                 u"\u0463": "afii10194",
                 u"\u0472": "afii10147",
                 u"\u0473": "afii10195",
                 u"\u0474": "afii10148",
                 u"\u0475": "afii10196",
                 u"\u0490": "afii10050",
                 u"\u0491": "afii10098",
                 u"\u04d9": "afii10846",
                 u"\u05b0": "afii57799",
                 u"\u05b1": "afii57801",
                 u"\u05b2": "afii57800",
                 u"\u05b3": "afii57802",
                 u"\u05b4": "afii57793",
                 u"\u05b5": "afii57794",
                 u"\u05b6": "afii57795",
                 u"\u05b7": "afii57798",
                 u"\u05b8": "afii57797",
                 u"\u05b9": "afii57806",
                 u"\u05bb": "afii57796",
                 u"\u05bc": "afii57807",
                 u"\u05bd": "afii57839",
                 u"\u05be": "afii57645",
                 u"\u05bf": "afii57841",
                 u"\u05c0": "afii57842",
                 u"\u05c1": "afii57804",
                 u"\u05c2": "afii57803",
                 u"\u05c3": "afii57658",
                 u"\u05d0": "afii57664",
                 u"\u05d1": "afii57665",
                 u"\u05d2": "afii57666",
                 u"\u05d3": "afii57667",
                 u"\u05d4": "afii57668",
                 u"\u05d5": "afii57669",
                 u"\u05d6": "afii57670",
                 u"\u05d7": "afii57671",
                 u"\u05d8": "afii57672",
                 u"\u05d9": "afii57673",
                 u"\u05da": "afii57674",
                 u"\u05db": "afii57675",
                 u"\u05dc": "afii57676",
                 u"\u05dd": "afii57677",
                 u"\u05de": "afii57678",
                 u"\u05df": "afii57679",
                 u"\u05e0": "afii57680",
                 u"\u05e1": "afii57681",
                 u"\u05e2": "afii57682",
                 u"\u05e3": "afii57683",
                 u"\u05e4": "afii57684",
                 u"\u05e5": "afii57685",
                 u"\u05e6": "afii57686",
                 u"\u05e7": "afii57687",
                 u"\u05e8": "afii57688",
                 u"\u05e9": "afii57689",
                 u"\u05ea": "afii57690",
                 u"\u05f0": "afii57716",
                 u"\u05f1": "afii57717",
                 u"\u05f2": "afii57718",
                 u"\u060c": "afii57388",
                 u"\u061b": "afii57403",
                 u"\u061f": "afii57407",
                 u"\u0621": "afii57409",
                 u"\u0622": "afii57410",
                 u"\u0623": "afii57411",
                 u"\u0624": "afii57412",
                 u"\u0625": "afii57413",
                 u"\u0626": "afii57414",
                 u"\u0627": "afii57415",
                 u"\u0628": "afii57416",
                 u"\u0629": "afii57417",
                 u"\u062a": "afii57418",
                 u"\u062b": "afii57419",
                 u"\u062c": "afii57420",
                 u"\u062d": "afii57421",
                 u"\u062e": "afii57422",
                 u"\u062f": "afii57423",
                 u"\u0630": "afii57424",
                 u"\u0631": "afii57425",
                 u"\u0632": "afii57426",
                 u"\u0633": "afii57427",
                 u"\u0634": "afii57428",
                 u"\u0635": "afii57429",
                 u"\u0636": "afii57430",
                 u"\u0637": "afii57431",
                 u"\u0638": "afii57432",
                 u"\u0639": "afii57433",
                 u"\u063a": "afii57434",
                 u"\u0640": "afii57440",
                 u"\u0641": "afii57441",
                 u"\u0642": "afii57442",
                 u"\u0643": "afii57443",
                 u"\u0644": "afii57444",
                 u"\u0645": "afii57445",
                 u"\u0646": "afii57446",
                 u"\u0647": "afii57470",
                 u"\u0648": "afii57448",
                 u"\u0649": "afii57449",
                 u"\u064a": "afii57450",
                 u"\u064b": "afii57451",
                 u"\u064c": "afii57452",
                 u"\u064d": "afii57453",
                 u"\u064e": "afii57454",
                 u"\u064f": "afii57455",
                 u"\u0650": "afii57456",
                 u"\u0651": "afii57457",
                 u"\u0652": "afii57458",
                 u"\u0660": "afii57392",
                 u"\u0661": "afii57393",
                 u"\u0662": "afii57394",
                 u"\u0663": "afii57395",
                 u"\u0664": "afii57396",
                 u"\u0665": "afii57397",
                 u"\u0666": "afii57398",
                 u"\u0667": "afii57399",
                 u"\u0668": "afii57400",
                 u"\u0669": "afii57401",
                 u"\u066a": "afii57381",
                 u"\u066d": "afii63167",
                 u"\u0679": "afii57511",
                 u"\u067e": "afii57506",
                 u"\u0686": "afii57507",
                 u"\u0688": "afii57512",
                 u"\u0691": "afii57513",
                 u"\u0698": "afii57508",
                 u"\u06a4": "afii57505",
                 u"\u06af": "afii57509",
                 u"\u06ba": "afii57514",
                 u"\u06d2": "afii57519",
                 u"\u06d5": "afii57534",
                 u"\u1e80": "Wgrave",
                 u"\u1e81": "wgrave",
                 u"\u1e82": "Wacute",
                 u"\u1e83": "wacute",
                 u"\u1e84": "Wdieresis",
                 u"\u1e85": "wdieresis",
                 u"\u1ef2": "Ygrave",
                 u"\u1ef3": "ygrave",
                 u"\u200c": "afii61664",
                 u"\u200d": "afii301",
                 u"\u200e": "afii299",
                 u"\u200f": "afii300",
                 u"\u2012": "figuredash",
                 u"\u2013": "endash",
                 u"\u2014": "emdash",
                 u"\u2015": "afii00208",
                 u"\u2017": "underscoredbl",
                 u"\u2018": "quoteleft",
                 u"\u2019": "quoteright",
                 u"\u201a": "quotesinglbase",
                 u"\u201b": "quotereversed",
                 u"\u201c": "quotedblleft",
                 u"\u201d": "quotedblright",
                 u"\u201e": "quotedblbase",
                 u"\u2020": "dagger",
                 u"\u2021": "daggerdbl",
                 u"\u2022": "bullet",
                 u"\u2024": "onedotenleader",
                 u"\u2025": "twodotenleader",
                 u"\u2026": "ellipsis",
                 u"\u202c": "afii61573",
                 u"\u202d": "afii61574",
                 u"\u202e": "afii61575",
                 u"\u2030": "perthousand",
                 u"\u2032": "minute",
                 u"\u2033": "second",
                 u"\u2039": "guilsinglleft",
                 u"\u203a": "guilsinglright",
                 u"\u203c": "exclamdbl",
                 u"\u2044": "fraction",
                 u"\u20a1": "colonmonetary",
                 u"\u20a3": "franc",
                 u"\u20a4": "lira",
                 u"\u20a7": "peseta",
                 u"\u20aa": "afii57636",
                 u"\u20ab": "dong",
                 u"\u20ac": "Euro",
                 u"\u2105": "afii61248",
                 u"\u2111": "Ifraktur",
                 u"\u2113": "afii61289",
                 u"\u2116": "afii61352",
                 u"\u2118": "weierstrass",
                 u"\u211c": "Rfraktur",
                 u"\u211e": "prescription",
                 u"\u2122": "trademark",
                 u"\u212e": "estimated",
                 u"\u2135": "aleph",
                 u"\u2153": "onethird",
                 u"\u2154": "twothirds",
                 u"\u215b": "oneeighth",
                 u"\u215c": "threeeighths",
                 u"\u215d": "fiveeighths",
                 u"\u215e": "seveneighths",
                 u"\u2190": "arrowleft",
                 u"\u2191": "arrowup",
                 u"\u2192": "arrowright",
                 u"\u2193": "arrowdown",
                 u"\u2194": "arrowboth",
                 u"\u2195": "arrowupdn",
                 u"\u21a8": "arrowupdnbse",
                 u"\u21b5": "carriagereturn",
                 u"\u21d0": "arrowdblleft",
                 u"\u21d1": "arrowdblup",
                 u"\u21d2": "arrowdblright",
                 u"\u21d3": "arrowdbldown",
                 u"\u21d4": "arrowdblboth",
                 u"\u2200": "universal",
                 u"\u2202": "partialdiff",
                 u"\u2203": "existential",
                 u"\u2205": "emptyset",
                 u"\u2207": "gradient",
                 u"\u2208": "element",
                 u"\u2209": "notelement",
                 u"\u220b": "suchthat",
                 u"\u220f": "product",
                 u"\u2211": "summation",
                 u"\u2212": "minus",
                 u"\u2215": "fraction",
                 u"\u2217": "asteriskmath",
                 u"\u2219": "periodcentered",
                 u"\u221a": "radical",
                 u"\u221d": "proportional",
                 u"\u221e": "infinity",
                 u"\u221f": "orthogonal",
                 u"\u2220": "angle",
                 u"\u2227": "logicaland",
                 u"\u2228": "logicalor",
                 u"\u2229": "intersection",
                 u"\u222a": "union",
                 u"\u222b": "integral",
                 u"\u2234": "therefore",
                 u"\u223c": "similar",
                 u"\u2245": "congruent",
                 u"\u2248": "approxequal",
                 u"\u2260": "notequal",
                 u"\u2261": "equivalence",
                 u"\u2264": "lessequal",
                 u"\u2265": "greaterequal",
                 u"\u2282": "propersubset",
                 u"\u2283": "propersuperset",
                 u"\u2284": "notsubset",
                 u"\u2286": "reflexsubset",
                 u"\u2287": "reflexsuperset",
                 u"\u2295": "circleplus",
                 u"\u2297": "circlemultiply",
                 u"\u22a5": "perpendicular",
                 u"\u22c5": "dotmath",
                 u"\u2302": "house",
                 u"\u2310": "revlogicalnot",
                 u"\u2320": "integraltp",
                 u"\u2321": "integralbt",
                 u"\u2329": "angleleft",
                 u"\u232a": "angleright",
                 u"\u2500": "SF100000",
                 u"\u2502": "SF110000",
                 u"\u250c": "SF010000",
                 u"\u2510": "SF030000",
                 u"\u2514": "SF020000",
                 u"\u2518": "SF040000",
                 u"\u251c": "SF080000",
                 u"\u2524": "SF090000",
                 u"\u252c": "SF060000",
                 u"\u2534": "SF070000",
                 u"\u253c": "SF050000",
                 u"\u2550": "SF430000",
                 u"\u2551": "SF240000",
                 u"\u2552": "SF510000",
                 u"\u2553": "SF520000",
                 u"\u2554": "SF390000",
                 u"\u2555": "SF220000",
                 u"\u2556": "SF210000",
                 u"\u2557": "SF250000",
                 u"\u2558": "SF500000",
                 u"\u2559": "SF490000",
                 u"\u255a": "SF380000",
                 u"\u255b": "SF280000",
                 u"\u255c": "SF270000",
                 u"\u255d": "SF260000",
                 u"\u255e": "SF360000",
                 u"\u255f": "SF370000",
                 u"\u2560": "SF420000",
                 u"\u2561": "SF190000",
                 u"\u2562": "SF200000",
                 u"\u2563": "SF230000",
                 u"\u2564": "SF470000",
                 u"\u2565": "SF480000",
                 u"\u2566": "SF410000",
                 u"\u2567": "SF450000",
                 u"\u2568": "SF460000",
                 u"\u2569": "SF400000",
                 u"\u256a": "SF540000",
                 u"\u256b": "SF530000",
                 u"\u256c": "SF440000",
                 u"\u2580": "upblock",
                 u"\u2584": "dnblock",
                 u"\u2588": "block",
                 u"\u258c": "lfblock",
                 u"\u2590": "rtblock",
                 u"\u2591": "ltshade",
                 u"\u2592": "shade",
                 u"\u2593": "dkshade",
                 u"\u25a0": "filledbox",
                 u"\u25a1": "H22073",
                 u"\u25aa": "H18543",
                 u"\u25ab": "H18551",
                 u"\u25ac": "filledrect",
                 u"\u25b2": "triagup",
                 u"\u25ba": "triagrt",
                 u"\u25bc": "triagdn",
                 u"\u25c4": "triaglf",
                 u"\u25ca": "lozenge",
                 u"\u25cb": "circle",
                 u"\u25cf": "H18533",
                 u"\u25d8": "invbullet",
                 u"\u25d9": "invcircle",
                 u"\u25e6": "openbullet",
                 u"\u263a": "smileface",
                 u"\u263b": "invsmileface",
                 u"\u263c": "sun",
                 u"\u2640": "female",
                 u"\u2642": "male",
                 u"\u2660": "spade",
                 u"\u2663": "club",
                 u"\u2665": "heart",
                 u"\u2666": "diamond",
                 u"\u266a": "musicalnote",
                 u"\u266b": "musicalnotedbl",
                 u"\ufb01": "fi",
                 u"\ufb02": "fl"}

class AFMError(Exception):
    pass

# reader states
_READ_START       = 0
_READ_MAIN        = 1
_READ_DIRECTION   = 2
_READ_CHARMETRICS = 3
_READ_KERNDATA    = 4
_READ_TRACKKERN   = 5
_READ_KERNPAIRS   = 6
_READ_COMPOSITES  = 7
_READ_END         = 8

# various parsing functions
def _parseint(s):
    try:
        return int(s)
    except:
        raise AFMError("Expecting int, got '%s'" % s)

def _parsehex(s):
    try:
        if s[0] != "<" or s[-1] != ">":
            raise AFMError()
        return int(s[1:-1], 16)
    except:
        raise AFMError("Expecting hexadecimal int, got '%s'" % s)

def _parsefloat(s):
    try:
        return float(s)
    except:
        raise AFMError("Expecting float, got '%s'" % s)

def _parsefloats(s, nos):
    try:
        numbers = s.split()
        result = map(float, numbers)
        if len(result) != nos:
            raise AFMError()
    except:
        raise AFMError("Expecting list of %d numbers, got '%s'" % (s, nos))
    return result

def _parsestr(s):
    # XXX: check for invalid characters in s
    return s

def _parsebool(s):
    s = s.rstrip()
    if s == "true":
       return 1
    elif s == "false":
       return 0
    else:
        raise AFMError("Expecting boolean, got '%s'" % s)


class AFMcharmetrics:
    def __init__(self, code, widths=None, vvector=None, name=None, bbox=None, ligatures=None):
        self.code = code
        if widths is None:
            self.widths = [None] * 2
        else:
            self.widths = widths
        self.vvector = vvector
        self.name = name
        self.bbox = bbox
        if ligatures is None:
            self.ligatures = []
        else:
            self.ligatures = ligatures


class AFMtrackkern:
    def __init__(self, degree, min_ptsize, min_kern, max_ptsize, max_kern):
        self.degree = degree
        self.min_ptsize = min_ptsize
        self.min_kern = min_kern
        self.max_ptsize = max_ptsize
        self.max_kern = max_kern


class AFMkernpair:
    def __init__(self, name1, name2, x, y):
        self.name1 = name1
        self.name2 = name2
        self.x = x
        self.y = y


class AFMcomposite:
    def __init__(self, name, parts):
        self.name = name
        self.parts = parts


class AFMfile(metric.metric):

    def __init__(self, file):
       self.metricssets = 0                     # int, optional
       self.fontname = None                     # str, required
       self.fullname = None                     # str, optional
       self.familyname = None                   # str, optional
       self.weight = None                       # str, optional
       self.fontbbox = None                     # 4 floats, required
       self.version = None                      # str, optional
       self.notice = None                       # str, optional
       self.encodingscheme = None               # str, optional
       self.mappingscheme = None                # int, optional (not present in base font programs)
       self.escchar = None                      # int, required if mappingscheme == 3
       self.characterset = None                 # str, optional
       self.characters = None                   # int, optional
       self.isbasefont = 1                      # bool, optional
       self.vvector = None                      # 2 floats, required if metricssets == 2
       self.isfixedv = None                     # bool, default: true if vvector present, false otherwise
       self.capheight = None                    # float, optional
       self.xheight = None                      # float, optional
       self.ascender = None                     # float, optional
       self.descender = None                    # float, optional
       self.stdhw = None                        # float, optional
       self.stdvw = None                        # float, optional
       self.underlinepositions = [None] * 2     # int, optional (for each direction)
       self.underlinethicknesses = [None] * 2   # float, optional (for each direction)
       self.italicangles = [None] * 2           # float, optional (for each direction)
       self.charwidths = [None] * 2             # 2 floats, optional (for each direction)
       self.isfixedpitchs = [None] * 2          # bool, optional (for each direction)
       self.charmetrics = None                  # list of character metrics information, optional
       self.charmetricsdict = {}                # helper dictionary mapping glyph names to character metrics information
       self.trackkerns = None                   # list of track kernings, optional
       self.kernpairs = [None] * 2              # list of list of kerning pairs (for each direction), optional
       self.kernpairsdict = {}                  # helper dictionary mapping glyph names to kerning pairs, first direction
       self.kernpairsdict1 = {}                 # helper dictionary mapping glyph names to kerning pairs, second direction
       self.composites = None                   # list of composite character data sets, optional
       self.parse(file)
       if self.isfixedv is None:
           self.isfixedv = self.vvector is not None
       # XXX we should check the constraints on some parameters

    # the following methods process a line when the reader is in the corresponding
    # state and return the new state
    def _processline_start(self, line):
        key, args = line.split(None, 1)
        if key != "StartFontMetrics":
            raise AFMError("Expecting StartFontMetrics, no found")
        return _READ_MAIN, None

    def _processline_main(self, line):
        try:
            key, args = line.split(None, 1)
        except ValueError:
            key = line.rstrip()
        if key == "Comment":
            return _READ_MAIN, None
        elif key == "MetricsSets":
            self.metricssets = _parseint(args)
            if direction is not None:
                raise AFMError("MetricsSets not allowed after first (implicit) StartDirection")
        elif key == "FontName":
            self.fontname = _parsestr(args)
        elif key == "FullName":
            self.fullname = _parsestr(args)
        elif key == "FamilyName":
            self.familyname = _parsestr(args)
        elif key == "Weight":
            self.weight = _parsestr(args)
        elif key == "FontBBox":
            self.fontbbox = _parsefloats(args, 4)
        elif key == "Version":
            self.version = _parsestr(args)
        elif key == "Notice":
            self.notice = _parsestr(args)
        elif key == "EncodingScheme":
            self.encodingscheme = _parsestr(args)
        elif key == "MappingScheme":
            self.mappingscheme = _parseint(args)
        elif key == "EscChar":
            self.escchar = _parseint(args)
        elif key == "CharacterSet":
            self.characterset = _parsestr(args)
        elif key == "Characters":
            self.characters = _parseint(args)
        elif key == "IsBaseFont":
            self.isbasefont = _parsebool(args)
        elif key == "VVector":
            self.vvector = _parsefloats(args, 2)
        elif key == "IsFixedV":
            self.isfixedv = _parsebool(args)
        elif key == "CapHeight":
            self.capheight = _parsefloat(args)
        elif key == "XHeight":
            self.xheight = _parsefloat(args)
        elif key == "Ascender":
            self.ascender = _parsefloat(args)
        elif key == "Descender":
            self.descender = _parsefloat(args)
        elif key == "StdHW":
            self.stdhw = _parsefloat(args)
        elif key == "StdVW":
            self.stdvw = _parsefloat(args)
        elif key == "StartDirection":
            direction = _parseint(args)
            if 0 <= direction <= 2:
                return _READ_DIRECTION, direction
            else:
                raise AFMError("Wrong direction number %d" % direction)
        elif (key == "UnderLinePosition" or key == "UnderlineThickness" or key == "ItalicAngle" or
              key == "Charwidth" or key == "IsFixedPitch"):
            # we implicitly entered a direction section, so we should process the line again
            return self._processline_direction(line, 0)
        elif key == "StartCharMetrics":
            if self.charmetrics is not None:
                raise AFMError("Multiple character metrics sections")
            self.charmetrics = [None] * _parseint(args)
            return _READ_CHARMETRICS, 0
        elif key == "StartKernData":
            return _READ_KERNDATA, None
        elif key == "StartComposites":
            if self.composites is not None:
                raise AFMError("Multiple composite character data sections")
            self.composites = [None] * _parseint(args)
            return _READ_COMPOSITES, 0
        elif key == "EndFontMetrics":
            return _READ_END, None
        elif key[0] in string.lowercase:
            # ignoring private commands
            pass
        return _READ_MAIN, None

    def _processline_direction(self, line, direction):
        try:
            key, args = line.split(None, 1)
        except ValueError:
            key = line.rstrip()
        if key == "UnderLinePosition":
            self.underlinepositions[direction] = _parseint(args)
        elif key == "UnderlineThickness":
            self.underlinethicknesses[direction] = _parsefloat(args)
        elif key == "ItalicAngle":
            self.italicangles[direction] = _parsefloat(args)
        elif key == "Charwidth":
            self.charwidths[direction] = _parsefloats(args, 2)
        elif key == "IsFixedPitch":
            self.isfixedpitchs[direction] = _parsebool(args)
        elif key == "EndDirection":
            return _READ_MAIN, None
        else:
            # we assume that we are implicitly leaving the direction section again,
            # so try to reprocess the line in the header reader state
            return self._processline_main(line)
        return _READ_DIRECTION, direction

    def _processline_charmetrics(self, line, charno):
        if line.rstrip() == "EndCharMetrics":
            if charno != len(self.charmetrics):
                raise AFMError("Fewer character metrics than expected")
            return _READ_MAIN, None
        if charno >= len(self.charmetrics):
            raise AFMError("More character metrics than expected")

        has_name = False
        char = None
        for s in line.split(";"):
            s = s.strip()
            if not s:
               continue
            key, args = s.split(None, 1)
            if key == "C":
                if char is not None:
                    raise AFMError("Cannot define char code twice")
                char = AFMcharmetrics(_parseint(args))
            elif key == "CH":
                if char is not None:
                    raise AFMError("Cannot define char code twice")
                char = AFMcharmetrics(_parsehex(args))
            elif key == "WX" or key == "W0X":
                char.widths[0] = _parsefloat(args), 0
            elif key == "W1X":
                char.widths[1] = _parsefloat(args), 0
            elif key == "WY" or key == "W0Y":
                char.widths[0] = 0, _parsefloat(args)
            elif key == "W1Y":
                char.widths[1] = 0, _parsefloat(args)
            elif key == "W" or key == "W0":
                char.widths[0] = _parsefloats(args, 2)
            elif key == "W1":
                char.widths[1] = _parsefloats(args, 2)
            elif key == "VV":
                char.vvector = _parsefloats(args, 2)
            elif key == "N":
                # XXX: we should check that name is valid (no whitespace, etc.)
                has_name = True
                char.name = _parsestr(args)
            elif key == "B":
                char.bbox = _parsefloats(args, 4)
            elif key == "L":
                successor, ligature = args.split(None, 1)
                char.ligatures.append((_parsestr(successor), ligature))
            else:
                raise AFMError("Undefined command in character widths specification: '%s'", s)
        if char is None:
            raise AFMError("Character metrics not defined")

        self.charmetrics[charno] = char
        if has_name:
            self.charmetricsdict[char.name] = char
        return _READ_CHARMETRICS, charno+1

    def _processline_kerndata(self, line):
        try:
            key, args = line.split(None, 1)
        except ValueError:
            key = line.rstrip()
        if key == "Comment":
            return _READ_KERNDATA, None
        if key == "StartTrackKern":
            if self.trackkerns is not None:
                raise AFMError("Multiple track kernings data sections")
            self.trackkerns = [None] * _parseint(args)
            return _READ_TRACKKERN, 0
        elif key == "StartKernPairs" or key == "StartKernPairs0":
            if self.kernpairs[0] is not None:
                raise AFMError("Multiple kerning pairs data sections for direction 0")
            self.kernpairs[0] = [None] * _parseint(args)
            return _READ_KERNPAIRS, (0, 0)
        elif key == "StartKernPairs1":
            if self.kernpairs[1] is not None:
                raise AFMError("Multiple kerning pairs data sections for direction 1")
            self.kernpairs[1] = [None] * _parseint(args)
            return _READ_KERNPAIRS, (1, 0)
        elif key == "EndKernData":
            return _READ_MAIN, None
        else:
            raise AFMError("Unsupported key %s in kerning data section" % key)

    def _processline_trackkern(self, line, i):
        try:
            key, args = line.split(None, 1)
        except ValueError:
            key = line.rstrip()
        if key == "Comment":
            return _READ_TRACKKERN, i
        elif key == "TrackKern":
            if i >= len(self.trackkerns):
                raise AFMError("More track kerning data sets than expected")
            degrees, args = args.split(None, 1)
            self.trackkerns[i] = AFMtrackkern(int(degrees), *_parsefloats(args, 4))
            return _READ_TRACKKERN, i+1
        elif key == "EndTrackKern":
            if i < len(self.trackkerns):
                raise AFMError("Fewer track kerning data sets than expected")
            return _READ_KERNDATA, None
        else:
            raise AFMError("Unsupported key %s in kerning data section" % key)

    def _processline_kernpairs(self, line, (direction, i)):
        try:
            key, args = line.split(None, 1)
        except ValueError:
            key = line.rstrip()
        if key == "Comment":
            return _READ_KERNPAIRS, (direction, i)
        elif key == "EndKernPairs":
            if i < len(self.kernpairs[direction]):
                raise AFMError("Fewer kerning pairs than expected")
            return _READ_KERNDATA, None
        else:
            if i >= len(self.kernpairs[direction]):
                raise AFMError("More kerning pairs than expected")
            if key == "KP":
                try:
                    name1, name2, x, y = args.split()
                except:
                    raise AFMError("Expecting name1, name2, x, y, got '%s'" % args)
                x = _parsefloat(x)
                y = _parsefloat(y)
            elif key == "KPH":
                try:
                    hex1, hex2, x, y = args.split()
                except:
                    raise AFMError("Expecting <hex1>, <hex2>, x, y, got '%s'" % args)
                name1 = _parsehex(hex1)
                name2 = _parsehex(hex2)
                x = _parsefloat(x)
                y = _parsefloat(y)
            elif key == "KPX":
                try:
                    name1, name2, x = args.split()
                except:
                    raise AFMError("Expecting name1, name2, x, got '%s'" % args)
                x = _parsefloat(x)
                y = 0
                self.kernpairs[direction][i] = AFMkernpair(name1, name2, _parsefloat(x), 0)
            elif key == "KPY":
                try:
                    name1, name2, y = args.split()
                except:
                    raise AFMError("Expecting name1, name2, y, got '%s'" % args)
                x = 0
                y = _parsefloat(y)
                self.kernpairs[direction][i] = AFMkernpair(name1, name2, 0, _parsefloat(y))
            else:
                raise AFMError("Unknown key '%s' in kern pair section" % key)
            kernpair = AFMkernpair(name1, name2, x, y)
            self.kernpairs[direction][i] = kernpair
            if direction:
                self.kernpairsdict1[name1, name2] = kernpair
            else:
                self.kernpairsdict[name1, name2] = kernpair
            return _READ_KERNPAIRS, (direction, i+1)

    def _processline_composites(self, line, i):
        if line.rstrip() == "EndComposites":
            if i < len(self.composites):
                raise AFMError("Fewer composite character data sets than expected")
            return _READ_MAIN, None
        if i >= len(self.composites):
            raise AFMError("More composite character data sets than expected")

        name = None
        no = None
        parts = []
        for s in line.split(";"):
            s = s.strip()
            if not s:
               continue
            key, args = s.split(None, 1)
            if key == "CC":
                try:
                    name, no = args.split()
                except:
                    raise AFMError("Expecting name number, got '%s'" % args)
                no = _parseint(no)
            elif key == "PCC":
                try:
                    name1, x, y = args.split()
                except:
                    raise AFMError("Expecting name x y, got '%s'" % args)
                parts.append((name1, _parsefloat(x), _parsefloat(y)))
            else:
                raise AFMError("Unknown key '%s' in composite character data section" % key)
        if len(parts) != no:
            raise AFMError("Wrong number of composite characters")
        return _READ_COMPOSITES, i+1

    def parse(self, f):
         # state of the reader, consisting of 
         #  - the main state, i.e. the type of the section
         #  - a parameter sstate
         state = _READ_START, None
         # Note that we do a line by line processing here, since one
         # of the states (_READ_DIRECTION) can be entered implicitly, i.e.
         # without a corresponding StartDirection section and we thus
         # may need to reprocess a line in the context of the new state
         for line in f:
            line = line[:-1]
            mstate, sstate = state
            if mstate == _READ_START:
                state = self._processline_start(line)
            else: 
                # except for the first line, any empty will be ignored
                if not line.strip():
                   continue
                if mstate == _READ_MAIN:
                    state = self._processline_main(line)
                elif mstate == _READ_DIRECTION:
                    state = self._processline_direction(line, sstate)
                elif mstate == _READ_CHARMETRICS:
                    state = self._processline_charmetrics(line, sstate)
                elif mstate == _READ_KERNDATA:
                    state = self._processline_kerndata(line)
                elif mstate == _READ_TRACKKERN:
                    state = self._processline_trackkern(line, sstate)
                elif mstate == _READ_KERNPAIRS:
                    state = self._processline_kernpairs(line, sstate)
                elif mstate == _READ_COMPOSITES:
                    state = self._processline_composites(line, sstate)
                else:
                    raise AFMError("Undefined state in AFM reader")

    def fucking_scale(self):
        # XXX XXX XXX
        return 1000.0

    def width_ds(self, glyphname):
        return self.charmetricsdict[glyphname].widths[0][0]

    def width_pt(self, glyphnames, size):
        return sum([self.charmetricsdict[glyphname].widths[0][0] for glyphname in glyphnames])*size/self.fucking_scale()

    def height_pt(self, glyphnames, size):
        return max([self.charmetricsdict[glyphname].bbox[3] for glyphname in glyphnames])*size/self.fucking_scale()

    def depth_pt(self, glyphnames, size):
        return min([self.charmetricsdict[glyphname].bbox[1] for glyphname in glyphnames])*size/self.fucking_scale()

    def resolveligatures(self, glyphnames):
        i = 1
        while i < len(glyphnames):
            for glyphname, replacement in self.charmetricsdict[glyphnames[i-1]].ligatures:
                if glyphname == glyphnames[i]:
                    glyphnames[i-1] = replacement
                    del glyphnames[i]
                    break
            else:
                i += 1
        return glyphnames

    def resolvekernings(self, glyphnames, size=None):
        result = [None]*(2*len(glyphnames)-1)
        for i, glyphname in enumerate(glyphnames):
            result[2*i] = glyphname
            if i:
                kernpair = self.kernpairsdict.get((glyphnames[i-1], glyphname))
                if kernpair:
                    if size is not None:
                        result[2*i-1] = kernpair.x*size/self.fucking_scale()
                    else:
                        result[2*i-1] = kernpair.x
        return result

    def writePDFfontinfo(self, file, seriffont=False, symbolfont=True):
        flags = 0
        if self.isfixedpitchs[0]:
            flags += 1<<0
        if seriffont:
            flags += 1<<1
        if symbolfont:
            flags += 1<<2
        else:
            flags += 1<<5
        if self.italicangles[0]:
            flags += 1<<6
        file.write("/Flags %d\n" % flags)
        if self.italicangles[0] is not None:
            file.write("/ItalicAngles %d\n" % self.italicangles[0])
        if self.ascender is not None:
            ascent = self.ascender
        elif self.fontbbox is not None:
            ascent = self.fontbbox[3]
        else:
            ascent = 1000 # guessed default
        file.write("/Ascent %d\n" % ascent)
        if self.descender is not None:
            descent = self.descender
        elif self.fontbbox is not None:
            descent = self.fontbbox[3]
        else:
            descent = -200 # guessed default
        file.write("/Descent %d\n" % descent)
        if self.fontbbox is not None:
            file.write("/FontBBox [%d %d %d %d]\n" % tuple(self.fontbbox))
        else:
            # the fontbbox is required, so we have to have to provide some default
            file.write("/FontBBox [0 %d 1000 %d]\n" % (descent, ascent))
        if self.capheight is not None:
            file.write("/CapHeight %d\n" % self.capheight)
        else:
            # the CapHeight is required, so we have to have to provide some default
            file.write("/CapHeight %d\n" % ascent)
        if self.stdvw is not None:
            stemv = self.stdvw
        elif self.weight is not None and ("bold" in self.weight.lower() or "black" in self.weight.lower()):
            stemv = 120 # guessed default
        else:
            stemv = 70 # guessed default
        file.write("/StemV %d\n" % stemv)


if __name__ == "__main__":
    a = AFMfile("/opt/local/share/texmf-dist/fonts/afm/yandy/lucida/lbc.afm")
    print a.charmetrics[0].name
    a = AFMfile("/usr/share/enscript/hv.afm")
    print a.charmetrics[32].name
