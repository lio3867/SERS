# -*- coding: utf-8 -*-
"""
Wrapper for the shared library. Functions that return more than one value will
return a tuple containing all of the outputs in order, starting from the
error code.
"""
import sys
import platform
import os
import pkg_resources
import ctypes
from ctypes import byref, c_uint8, c_uint16, c_uint64, c_float, POINTER


is_64_bits = sys.maxsize > 2**32
if sys.platform.startswith("win32"):
    libclass = ctypes.WinDLL
    lib_relative_path = ('shared', 'windows')
    if is_64_bits:
        lib_name = "frp_c_64.dll"
    else:
        lib_name = "frp_c_32.dll"
elif sys.platform.startswith("linux"):
    sharedObjectVersion = "2.0.0"
    libclass = ctypes.CDLL
    if is_64_bits:
        lib_name = "libfrp_64.so"+ "." + sharedObjectVersion
    else:
        lib_name = "libfrp_32.so"+ "." + sharedObjectVersion
    if platform.machine().lower().startswith('arm'):
        lib_relative_path = ('shared', 'pi')
    else:
        lib_relative_path = ('shared', 'linux')
else: 
    raise NotImplementedError("SDK not available on " + sys.platform)

# Find shared library in package
resource_package = __name__
resource_path = '/'.join(lib_relative_path)
libpath = pkg_resources.resource_filename(resource_package, resource_path)
lib = libclass(os.path.join(libpath, lib_name))  

# Function prototypes
lib.restype = c_uint8
lib.frp_detect.argtypes = [POINTER(c_uint16)]
lib.frp_initialization.argtypes = [c_uint16]
lib.frp_initialization.restype = c_uint64
lib.frp_close.argtypes = [c_uint64]
lib.frp_get_serial.argtypes = [c_uint64, POINTER(c_uint16), POINTER(c_uint16)]
lib.frp_read.argtypes = [c_uint64, POINTER(c_uint8)]
lib.frp_write.argtypes = [c_uint64, POINTER(c_uint8)]
lib.frp_read_flow.argtypes = [c_uint64, c_uint8, POINTER(c_uint8), POINTER(c_float)]
lib.frp_set_calibration.argtypes = [c_uint64, c_uint8, c_uint8]
lib.frp_data_FU.argtypes = [c_uint64, c_uint8, POINTER(c_uint8),
    ctypes.POINTER(c_uint8), POINTER(c_uint8), POINTER(c_uint16), 
    ctypes.POINTER(c_uint8), POINTER(c_uint8)]

def frp_detect():
    serial_number_list = (c_uint16*256)(*([0]*256))
    c_error = c_uint8(lib.frp_detect(serial_number_list))
    serial_number_list = list(filter(None, serial_number_list))
    serial_number_list = [int(hex(s)[2:]) for s in serial_number_list]
    return (c_error.value, serial_number_list)
    
def frp_initialization(serial_number = 0):
    """Default (0) initializes the first Flowboard found"""
    # Convert serial number from Hex to Dec to match the instrument label
    serial_number = int(str(serial_number), 16)
    handle = c_uint64(lib.frp_initialization(c_uint16(serial_number)))
    return handle.value
    
def frp_close(handle):
    c_error = c_uint8(lib.frp_close(c_uint64(handle)))
    return c_error.value
    
def frp_get_serial(handle):
    serial = c_uint16(0)
    fb_version = c_uint16(0)
    c_error = c_uint8(lib.frp_get_serial(c_uint64(handle), byref(serial),
                                         byref(fb_version)))
    # Convert serial number from Dec to Hex to match the instrument
    serial_corrected = int(hex(serial.value)[2:])
    return (c_error.value, serial_corrected, fb_version.value)
    
def frp_read_flow(handle, channel):
    flow_rate = c_float(0)
    time_stamp = c_uint8(0)
    c_error = c_uint8(lib.frp_read_flow(c_uint64(handle), c_uint8(channel), 
                          byref(time_stamp), byref(flow_rate)))
    return (c_error.value, flow_rate.value, time_stamp.value)

def frp_data_FU(handle, channel):
    calibration = ctypes.c_uint8(0)
    resolution = ctypes.c_uint8(0)
    articleCode = (c_uint8*32)(*([0]*32))
    scaleFactor = ctypes.c_uint16(0)
    unit = ctypes.c_uint8(0)
    timebase = ctypes.c_uint8(0)
    c_error = c_uint8(lib.frp_data_FU(c_uint64(handle), c_uint8(channel), 
               byref(calibration), byref(resolution), articleCode, 
               byref(scaleFactor), byref(unit), byref(timebase)))  
    articleCode = ("".join([chr(c) for c in filter(None, articleCode)])).strip()
    return (c_error.value, calibration.value, resolution.value, articleCode, 
            scaleFactor.value, unit.value, timebase.value)
    
def frp_set_calibration(handle, channel, cal):
    c_error = c_uint8(lib.frp_set_calibration(c_uint64(handle), c_uint8(channel), c_uint8(cal)))
    return c_error.value
