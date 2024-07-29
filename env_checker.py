import PIL

class EnvChecker:
    @staticmethod
    def check(filename):
        if not EnvChecker.is_pil_simd():
            print("********WARNING*******************************************************")
            print("You are using Python Pillow PIL module and not the Pillow-SIMD module.")
            print("Pillow-SIMD is a 4x faster drop-in replacement of the base PIL module.")
            print("Uninstalling Pillow PIL and installing Pillow-SIMD is a good idea.")
            print("**********************************************************************")

    def is_pil_simd():
        return 'post' in PIL.__version__
