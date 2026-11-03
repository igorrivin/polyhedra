"""Regression for a computational pathname broken across a printed page."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('repository_linker', Path(__file__).parents[1]/'link_repository.py')
linker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(linker)
try:
    import pymupdf
except ImportError:
    pymupdf = None


@unittest.skipIf(pymupdf is None, 'PDF publication requires PyMuPDF')
class PDFPaths(unittest.TestCase):
    def test_page_break_retains_both_segments_without_linking_margin_text(self):
        with pymupdf.open() as doc:
            for number in range(2):
                page = doc.new_page(width=595,height=842)
                page.insert_text((60,45),'Polyhedra, Moduli, and Quantum Geometry',fontsize=9)
                page.insert_text((440,45),'Research monograph',fontsize=9)
                page.insert_text((290,810),str(number+1))
            doc[0].insert_text((200,760),'artifacts/normalizations/',fontname='cour',fontsize=10)
            doc[1].insert_text((60,80),'result.json. These are finite checks.',fontname='cour',fontsize=10)
            name='artifacts/normalizations/result.json'
            matches=linker.pdf_path_locations(doc,{name:'https://example.org/source'})
            self.assertEqual(len(matches),1)
            self.assertEqual(matches[0][0],name)
            self.assertEqual({c[2][0] for c in matches[0][1]},{0,1})
            self.assertTrue(all(60 < c[1][1] < 780 for c in matches[0][1]))
            # Ordinary body text between the fragments must prevent a match.
            doc[0].insert_text((60,775),'Intervening body prose.')
            self.assertEqual(linker.pdf_path_locations(doc,{name:''}),[])


if __name__ == '__main__':
    unittest.main()
