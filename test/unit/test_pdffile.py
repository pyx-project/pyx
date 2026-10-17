import sys
if sys.path[0] != "../..":
    sys.path.insert(0, "../..")

import io
import unittest

from pyx import *


class PDFFileTestCase(unittest.TestCase):

    def _make_source_pdf(self):
        c1 = canvas.canvas()
        c1.fill(path.rect_pt(10, 20, 30, 50))
        img = bitmap.image(2, 2, "RGB", b"\xff\x00\x00\x00\xff\x00\x00\x00\xff\xff\xff\x00")
        c1.insert(bitmap.bitmap_pt(15, 25, img, width_pt=20, height_pt=20))

        c2 = canvas.canvas()
        c2.fill(path.rect_pt(0, 0, 50, 80))

        d = document.document([
            document.page(c1, bboxenlarge=0),
            document.page(c2, bboxenlarge=0),
        ])
        buf = io.BytesIO()
        d.writePDFfile(buf, writebbox=True)
        return buf.getvalue()

    def testReaderAndBbox(self):
        pdf_bytes = self._make_source_pdf()
        r = pdffile.PDFreader(io.BytesIO(pdf_bytes))
        bb1 = r.get_page_bbox(1)
        self.assertAlmostEqual(bb1.llx_pt, 10, places=3)
        self.assertAlmostEqual(bb1.lly_pt, 20, places=3)
        self.assertAlmostEqual(bb1.urx_pt, 40, places=3)
        self.assertAlmostEqual(bb1.ury_pt, 70, places=3)

        bb2 = r.get_page_bbox(2)
        self.assertAlmostEqual(bb2.llx_pt, 0, places=3)
        self.assertAlmostEqual(bb2.lly_pt, 0, places=3)
        self.assertAlmostEqual(bb2.urx_pt, 50, places=3)
        self.assertAlmostEqual(bb2.ury_pt, 80, places=3)
        self.assertRaises(ValueError, r.get_page, 3)

    def testAlignmentAndScaling(self):
        pdf_bytes = self._make_source_pdf()
        p = pdffile.pdffile(0, 0, io.BytesIO(pdf_bytes), scale=2, align="cc")
        bb = p.bbox()
        self.assertAlmostEqual(bb.llx_pt, -30, places=3)
        self.assertAlmostEqual(bb.lly_pt, -50, places=3)
        self.assertAlmostEqual(bb.urx_pt, 30, places=3)
        self.assertAlmostEqual(bb.ury_pt, 50, places=3)

        p_w = pdffile.pdffile(0, 0, io.BytesIO(pdf_bytes), width=60 * unit.t_pt, align="tr")
        bb_w = p_w.bbox()
        self.assertAlmostEqual(bb_w.llx_pt, -60, places=3)
        self.assertAlmostEqual(bb_w.lly_pt, -100, places=3)
        self.assertAlmostEqual(bb_w.urx_pt, 0, places=3)
        self.assertAlmostEqual(bb_w.ury_pt, 0, places=3)

    def testEmbedIntoPDF(self):
        pdf_bytes = self._make_source_pdf()
        c = canvas.canvas()
        c.insert(pdffile.pdffile(0, 0, io.BytesIO(pdf_bytes), page=1))
        c.insert(pdffile.pdffile(2, 0, io.BytesIO(pdf_bytes), page=1, scale=2))
        c.insert(pdffile.pdffile(5, 0, io.BytesIO(pdf_bytes), page=2))

        out = io.BytesIO()
        c.writePDFfile(out, page_bboxenlarge=0, write_compress=False)
        out.seek(0)

        out_reader = pdffile.PDFreader(out)
        page = out_reader.get_page(1)
        resources = out_reader.get_object(page["Resources"])
        xobjects = out_reader.get_object(resources["XObject"])
        self.assertEqual(len(xobjects), 2)
        for xobj_ref in xobjects.values():
            xobj = out_reader.get_object(xobj_ref)
            self.assertEqual(xobj.dict.get("Type"), "XObject")
            self.assertEqual(xobj.dict.get("Subtype"), "Form")


if __name__ == "__main__":
    unittest.main()
