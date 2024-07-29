import PyPDF2

from magick_checker import MagickChecker

class PDFChecker:
    @staticmethod
    def check(filename):
        pdfobj = PyPDF2.PdfFileReader(open(filename, "rb"))
        pdfobj.getDocumentInfo()

        # Check with imagemagick
        MagickChecker.check(filename, False)

