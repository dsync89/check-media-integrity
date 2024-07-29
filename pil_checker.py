import PIL
from PIL import Image as ImageP

class PILChecker:
    @staticmethod
    def check(filename):
        img = ImageP.open(filename)  # open the image file
        img.verify()  # verify that it is a good image, without decoding it.. quite fast
        img.close()

        # Image manipulation is mandatory to detect few defects
        img = ImageP.open(filename)  # open the image file
        # alternative (removed) version, decode/recode:
        # f = cStringIO.StringIO()
        # f = io.BytesIO()
        # img.save(f, "BMP")
        # f.close()
        img.transpose(PIL.Image.FLIP_LEFT_RIGHT)
        img.close()    
