from wand.image import Image as ImageW
from subprocess import Popen, PIPE

class MagickChecker:
    @staticmethod
    def check(filename, flip=True):
        # very useful for xcf, psd and aslo supports pdf
        img = ImageW(filename=filename)
        if flip:
            temp = img.flip
        else:
            temp = img.make_blob(format='bmp')
        img.close()
        return temp

    def identify_check(filename):
        proc = Popen(['identify', '-regard-warnings', filename], stdout=PIPE,
                    stderr=PIPE)  # '-verbose',
        out, err = proc.communicate()
        exitcode = proc.returncode
        if exitcode != 0:
            raise Exception('Identify error:' + str(exitcode))
        return out