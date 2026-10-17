import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import io
import os
import struct
import unittest

from pyx import canvas, config, text, trafo
from pyx.font import OTFfont
from pyx.font.otffile import OTFFile, _encode_cff_fixed_int, _encode_cff_float, _encode_cff_int, _make_cff_index, checksum


def _make_sfnt(sfnt_version, tables):
    tags = sorted(tables.keys())
    num_tables = len(tags)
    max_pow2 = 1
    entry_selector = 0
    while max_pow2 * 2 <= num_tables:
        max_pow2 *= 2
        entry_selector += 1
    search_range = max_pow2 * 16
    range_shift = num_tables * 16 - search_range
    dir_offset = 12 + 16 * num_tables
    directory = bytearray(struct.pack(">4sHHHH", sfnt_version, num_tables, search_range, entry_selector, range_shift))
    body = bytearray()
    for tag in tags:
        tdata = tables[tag]
        cs = checksum(tdata)
        offset = dir_offset + len(body)
        length = len(tdata)
        directory.extend(struct.pack(">4sLLL", tag, cs, offset, length))
        body.extend(tdata)
        pad = (4 - length % 4) % 4
        if pad:
            body.extend(b"\x00" * pad)
    return bytes(directory + body)


def _make_common_tables():
    head = bytearray(54)
    struct.pack_into(">IIHH", head, 0, 0x00010000, 0x00010000, 0, 0)
    struct.pack_into(">IH", head, 12, 0x5F0F3CF5, 0)
    struct.pack_into(">H", head, 18, 1000)
    struct.pack_into(">hhhh", head, 36, 0, -200, 1000, 800)
    struct.pack_into(">h", head, 50, 0)

    hhea = bytearray(36)
    struct.pack_into(">Ihhh", hhea, 0, 0x00010000, 800, -200, 0)
    struct.pack_into(">H", hhea, 34, 4)

    maxp = struct.pack(">IH", 0x00005000, 4)
    hmtx = struct.pack(">HhHhHhHh", 500, 0, 600, 50, 550, 40, 700, 50)

    fam = "TestOTF".encode("utf-16be")
    sub = "Regular".encode("utf-16be")
    psn = "TestOTF-Regular".encode("utf-16be")
    str_data = fam + sub + psn
    name_hdr = struct.pack(">HHH", 0, 3, 6 + 3 * 12)
    recs = (
        struct.pack(">HHHHHH", 3, 1, 1033, 1, len(fam), 0) +
        struct.pack(">HHHHHH", 3, 1, 1033, 2, len(sub), len(fam)) +
        struct.pack(">HHHHHH", 3, 1, 1033, 6, len(psn), len(fam) + len(sub))
    )
    name = name_hdr + recs + str_data

    post = bytearray(32)
    struct.pack_into(">I", post, 0, 0x00030000)

    # cmap format 12: 'A' (65) -> 1, 'V' (86) -> 2, 'f' (102) -> 1, 'i' (105) -> 2, '=' (61) -> 1
    groups = [
        (61, 61, 1),
        (65, 65, 1),
        (86, 86, 2),
        (102, 102, 1),
        (105, 105, 2),
    ]
    sub12 = struct.pack(">HHIII", 12, 0, 16 + 12 * len(groups), 0, len(groups))
    for sc, ec, sg in groups:
        sub12 += struct.pack(">III", sc, ec, sg)
    cmap = struct.pack(">HH", 0, 1) + struct.pack(">HHI", 3, 10, 12) + sub12

    # kern table: (1, 2) -> -80
    kern = struct.pack(">HHHHHHHHH", 0, 1, 0, 20, 1, 1, 6, 0, 0) + struct.pack(">HHh", 1, 2, -80)

    # GSUB table: 'liga' (1, 2) -> 3
    # Header (10), ScriptList (2), FeatureList (14), LookupList (30)
    # FeatureList at offset 12: count=1, tag='liga', off=8 -> Feature at 20: params=0, count=1, idx=0
    # LookupList at offset 26: count=1, off=4 -> Lookup at 30: type=4, flag=0, scount=1, soff=8
    # Subtable at 38: fmt=1, cov_off=8, set_count=1, set_off=14
    # Coverage at 46: fmt=1, count=1, gid=1
    # LigSet at 52: count=1, lig_off=4 -> Ligature at 56: lig_gid=3, comp_count=2, comp1=2
    gsub = (
        struct.pack(">IH", 0x00010000, 10) + struct.pack(">HH", 12, 26) +
        struct.pack(">H", 0) +
        struct.pack(">H4sH", 1, b"liga", 8) + struct.pack(">HHH", 0, 1, 0) +
        struct.pack(">HH", 1, 4) +
        struct.pack(">HHHH", 4, 0, 1, 8) +
        struct.pack(">HHHH", 1, 8, 1, 14) +
        struct.pack(">HHH", 1, 1, 1) +
        struct.pack(">HH", 1, 4) +
        struct.pack(">HHH", 3, 2, 2)
    )

    return {
        b"head": bytes(head),
        b"hhea": bytes(hhea),
        b"maxp": maxp,
        b"hmtx": hmtx,
        b"name": name,
        b"post": bytes(post),
        b"cmap": cmap,
        b"kern": kern,
        b"GSUB": gsub,
    }


def _make_ttf_bytes():
    tables = _make_common_tables()
    # 4 glyphs: 0 (.notdef empty), 1 (simple rectangle), 2 (simple triangle), 3 (composite of 1 and 2)
    g1 = (
        struct.pack(">hhhhh", 1, 50, 0, 550, 700) +
        struct.pack(">H", 3) +
        struct.pack(">H", 0) +
        bytes([0x01, 0x01, 0x01, 0x01]) +
        struct.pack(">hhhh", 50, 500, 0, -500) +
        struct.pack(">hhhh", 0, 0, 700, 0)
    )
    if len(g1) % 2:
        g1 += b"\x00"
    g2 = (
        struct.pack(">hhhhh", 1, 40, 0, 510, 700) +
        struct.pack(">H", 2) +
        struct.pack(">H", 0) +
        bytes([0x01, 0x01, 0x01]) +
        struct.pack(">hhh", 40, 470, -235) +
        struct.pack(">hhh", 700, 0, -700)
    )
    if len(g2) % 2:
        g2 += b"\x00"
    g3 = (
        struct.pack(">hhhhh", -1, 50, 0, 700, 700) +
        struct.pack(">HHbb", 0x0022, 1, 0, 0) +
        struct.pack(">HHbb", 0x0002, 2, 100, 0)
    )
    if len(g3) % 2:
        g3 += b"\x00"
    glyf = g1 + g2 + g3
    locs = [0, 0, len(g1), len(g1) + len(g2), len(glyf)]
    loca = struct.pack(">5H", *[l // 2 for l in locs])
    tables[b"glyf"] = glyf
    tables[b"loca"] = loca
    return _make_sfnt(b"\x00\x01\x00\x00", tables)


def _make_cff_otf_bytes():
    tables = _make_common_tables()
    # Type 2 charstrings: rmoveto (21), hlineto (6), vlineto (7), endchar (14)
    cs0 = _encode_cff_int(500) + bytes([14])
    cs1 = (
        _encode_cff_int(600) + _encode_cff_int(50) + _encode_cff_int(200) + bytes([21]) +
        _encode_cff_int(500) + _encode_cff_int(100) + _encode_cff_int(-500) + bytes([6]) +
        bytes([14])
    )
    cs2 = (
        _encode_cff_int(550) + _encode_cff_int(40) + _encode_cff_int(0) + bytes([21]) +
        _encode_cff_int(470) + _encode_cff_int(700) + _encode_cff_int(-470) + bytes([6]) +
        bytes([14])
    )
    cs3 = cs1
    charstrings_idx = _make_cff_index([cs0, cs1, cs2, cs3])
    charset = b"\x00" + struct.pack(">3H", 34, 55, 109) # A, V, fi
    priv_dict = _encode_cff_int(0) + bytes([20]) + _encode_cff_int(0) + bytes([21])
    hdr = b"\x01\x00\x04\x04"
    name_idx = _make_cff_index([b"TestOTF-Regular"])
    string_idx = _make_cff_index([])
    gsubr_idx = _make_cff_index([])
    fm_bytes = (
        _encode_cff_float(0.001) + _encode_cff_int(0) + _encode_cff_int(0) +
        _encode_cff_float(0.001) + _encode_cff_int(0) + _encode_cff_int(0) + bytes([12, 7])
    )
    bbox_bytes = _encode_cff_int(0) + _encode_cff_int(-200) + _encode_cff_int(1000) + _encode_cff_int(800) + bytes([5])

    def make_td(c_off, cs_off, p_size, p_off):
        return (
            fm_bytes + bbox_bytes +
            _encode_cff_fixed_int(c_off) + bytes([15]) +
            _encode_cff_fixed_int(cs_off) + bytes([17]) +
            _encode_cff_fixed_int(p_size) + _encode_cff_fixed_int(p_off) + bytes([18])
        )

    dummy_td = _make_cff_index([make_td(0, 0, len(priv_dict), 0)])
    base_off = len(hdr) + len(name_idx) + len(dummy_td) + len(string_idx) + len(gsubr_idx)
    c_off = base_off
    cs_off = c_off + len(charset)
    p_off = cs_off + len(charstrings_idx)
    top_dict_idx = _make_cff_index([make_td(c_off, cs_off, len(priv_dict), p_off)])
    tables[b"CFF "] = hdr + name_idx + top_dict_idx + string_idx + gsubr_idx + charset + charstrings_idx + priv_dict
    return _make_sfnt(b"OTTO", tables)


class OTFFileTestCase(unittest.TestCase):

    def _check_otf_instance(self, data, expect_cff):
        otf = OTFFile(data)
        self.assertEqual(otf.is_cff, expect_cff)
        self.assertEqual(otf.name, "TestOTF-Regular")
        self.assertEqual(otf.width_ds("equal"), 600)
        self.assertEqual(otf.width_ds("V"), 550)
        self.assertAlmostEqual(otf.width_pt(["equal", "V"], 10), 11.5, places=3)
        self.assertEqual(otf.resolveligatures(["equal", "V"]), ["glyph3" if not expect_cff else "fi"])
        kerned = otf.resolvekernings(["equal", "V"], 10)
        self.assertEqual(kerned[0], "equal")
        self.assertAlmostEqual(kerned[1], -0.8, places=3)
        self.assertEqual(kerned[2], "V")

        f = OTFfont(otf)
        c = canvas.canvas()
        t = f.text_pt(10, 20, "=V", 12, kerning=True, ligatures=True, slant=0.1, spaced_pt=1.0)
        c.insert(t)
        tp = t.textpath()
        self.assertTrue(len(tp.normpath().normsubpaths) > 0)

        for strip in (True, False):
            ps_buf = io.BytesIO()
            c.writePSfile(ps_buf, write_stripfonts=strip)
            self.assertTrue(len(ps_buf.getvalue()) > 100)

            pdf_buf = io.BytesIO()
            c.writePDFfile(pdf_buf, write_stripfonts=strip)
            self.assertTrue(pdf_buf.getvalue().startswith(b"%PDF-"))

        for tap in (True, False):
            svg_buf = io.BytesIO()
            c.writeSVGfile(svg_buf, write_textaspath=tap)
            self.assertIn(b"<svg", svg_buf.getvalue())

    def testTrueTypeOTF(self):
        self._check_otf_instance(_make_ttf_bytes(), expect_cff=False)

    def testCFFOTF(self):
        self._check_otf_instance(_make_cff_otf_bytes(), expect_cff=True)

    def testUnicodeEngineWithOTF(self):
        ttf_bytes = _make_ttf_bytes()
        key = ("memory_test.ttf", (config.format.type1.name, config.format.otf.name, config.format.ttf.name))
        config.opener_cache[key] = lambda: io.BytesIO(ttf_bytes)
        try:
            ue = text.UnicodeEngine(fontname="memory_test.ttf", size=12)
            tb = ue.text(0, 0, ["=", text.StackedText([text.Text("=", shift=0.3), text.Text("V", shift=-0.9)], frac=True, align=0.5)])
            self.assertTrue(tb.bbox().width_pt() > 0)
        finally:
            config.opener_cache.pop(key, None)

    def testSystemFonts(self):
        for fontpath in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/opentype/unifont/unifont.otf",
        ]:
            if not os.path.exists(fontpath):
                continue
            ue = text.UnicodeEngine(fontname=fontpath, size=10)
            c = canvas.canvas()
            c.insert(ue.text(0, 0, "Hello, World!"))
            c.insert(ue.text(0, 1, ["10", text.Text("2", shift=0.5, scale=0.8)]))
            ps_buf = io.BytesIO()
            c.writePSfile(ps_buf)
            self.assertTrue(len(ps_buf.getvalue()) > 100)
            pdf_buf = io.BytesIO()
            c.writePDFfile(pdf_buf)
            self.assertTrue(pdf_buf.getvalue().startswith(b"%PDF-"))
            svg_buf = io.BytesIO()
            c.writeSVGfile(svg_buf)
            self.assertIn(b"<svg", svg_buf.getvalue())


if __name__ == "__main__":
    unittest.main()
