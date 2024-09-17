'''
Written by Lev Galperin and Shay Gihaz
'''
import os
import signal
import sys
import time
import ctypes
from ctypes import cdll
from ctypes import c_char_p


xclib = cdll.LoadLibrary("D:/XCLIB_source_Code/XCLIB/xclybw64.dll")
FORMATFILE = "C:/Users/aviadkat/Documents/EPIX/XCAP/data/Lev_camera_setup.fmt"

# Set number of expected PIXCI(R) frame grabbers
UNITS = 1
UNITSMAP = (1 << UNITS) - 1  # bitmap of all units
UNITSOPENMAP = UNITSMAP
IMAGEFILE_DIR = "."

def checkexist(name):
    try:
        with open(name, "rb"):
            print(f"Image not saved, file {name} already exists")
            print("")
            return True
    except FileNotFoundError:
        return False

def signaled(sig, frame):
    print(f"Signal {sig} received, closing PIXCI frame grabber.")
    xclib.pxd_PIXCIclose()
    sys.exit(0)

class Camera:
    def __init__(self):
        signal.signal(signal.SIGINT, signaled)
        signal.signal(signal.SIGFPE, signaled)
        # Define the function prototype
        pxd_PIXCIopen = xclib.pxd_PIXCIopen
        pxd_PIXCIopen.restype = ctypes.c_int  # Specify the return type of the function
        pxd_PIXCIopen.argtypes = [ctypes.c_char_p, ctypes.c_char_p,
                                  ctypes.c_char_p]  # Specify the argument types of the function

        # Now you can call the function
        driverparms = b"-DM 0x1"  # Example driver parameters (convert to bytes)
        formatname = None  # Example format name (None or empty string)
        formatfile = b"C:/Users/aviadkat/Documents/EPIX/XCAP/data/exposure_0_1.fmt"  # Example format file (convert to bytes)
        r = pxd_PIXCIopen(driverparms, formatname, formatfile)

        print("Opening EPIX(R) PIXCI(R) Frame Grabber,")
        print(f"using configuration parameters '{driverparms or 'default'},")

        if r < 0:
            print(f"Open Error {xclib.pxd_mesgErrorCode(r)}({r})\a\a")
            xclib.pxd_mesgFault(UNITSMAP)
            raise Exception("Camera could not initialize")


    def save_image(self):              ## this is for to put the image in the image processing algorithm
        err = xclib.pxd_doSnap(UNITSMAP, 1, 0)
        print(f"pxd_doSnap: {'Ok' if err >= 0 else xclib.pxd_mesgErrorCode(err)}")
        print(f"Field count before snap={xclib.pxd_videoFieldCount(1)}")
        print(f"Field count after  snap={xclib.pxd_videoFieldCount(1)}")
        xclib.pxd_mesgFault(UNITSMAP)
        print("Image snapped into buffer 1")
        name = os.path.join(IMAGEFILE_DIR, f"image{0}.bmp")

        # Don't overwrite existing file
        if checkexist(name):
            raise Exception("Image file already exists")

        # Do save of entire image in Bitmap format
        # Monochrome image buffers are saved as an 8 bit monochrome image
        # Color image buffers are saved as a 24 bit RGB color image
        print(f"Image buffer 1 being saved to file {name}")
        err = xclib.pxd_saveBmp(1 << 0, c_char_p(name.encode()), 1, 0, 0, -1, -1, 0, 0)
        if err < 0:
            print(f"pxd_saveBmp: {xclib.pxd_mesgErrorCode(err)}")
            raise Exception("There is a problem with image saving")

        print("Image buffer saved")


    def get_coordinates(self):
        # Get coordinates of the camera
        pass

    def get_camera_util(self):
        expt = xclib.pxd_SILICONVIDEO_setExposure(1)
        return expt



    def camera_util_change(self,new_exp):

        err = xclib.pxd_SILICONVIDEO_setExposure(1,0,ctypes.c_double(new_exp))
        pass


    def set_new_exposure_param(self,new_exp=0.01):
        self.close()
        signal.signal(signal.SIGINT, signaled)
        signal.signal(signal.SIGFPE, signaled)
        # Define the function prototype
        pxd_PIXCIopen = xclib.pxd_PIXCIopen
        pxd_PIXCIopen.restype = ctypes.c_int  # Specify the return type of the function
        pxd_PIXCIopen.argtypes = [ctypes.c_char_p, ctypes.c_char_p,
                                  ctypes.c_char_p]  # Specify the argument types of the function

        # Now you can call the function
        driverparms = b"-DM 0x1"  # Example driver parameters (convert to bytes)
        formatname = None  # Example format name (None or empty string)
        formatfile = b"C:/Users/aviadkat/Documents/EPIX/XCAP/data/exposure_0_01.fmt" if new_exp==0.01 else b"C:/Users/aviadkat/Documents/EPIX/XCAP/data/exposure_0_001.fmt" # Example format file (convert to bytes)
        r = pxd_PIXCIopen(driverparms, formatname, formatfile)

        print("Opening EPIX(R) PIXCI(R) Frame Grabber,")
        print(f"using configuration parameters '{driverparms or 'default'},")

        if r < 0:
            print(f"Open Error {xclib.pxd_mesgErrorCode(r)}({r})\a\a")
            xclib.pxd_mesgFault(UNITSMAP)
            raise Exception("Camera could not initialize")
        err = xclib.pxd_SILICONVIDEO_setExposure(1,0,ctypes.c_double(new_exp))
        pass


    def close(self):
        xclib.pxd_PIXCIclose()
        print("PIXCI(R) frame grabber closed")