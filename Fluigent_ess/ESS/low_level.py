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
from ctypes import byref, c_uint8, c_uint16, c_uint64, POINTER

# Detect Operating System, processor architecture and bitness
is_64_bits = sys.maxsize > 2**32

if sys.platform.startswith("win32"):
    libclass = ctypes.WinDLL
    lib_relative_path = ('shared', 'windows')
    if is_64_bits:
        lib_name = "ess_c_64.dll"
    else:
        lib_name = "ess_c_32.dll"
elif sys.platform.startswith("linux"):
    sharedObjectVersion = "2.0.0"
    libclass = ctypes.CDLL
    if is_64_bits:
        lib_name = "libess_64.so"+ "." + sharedObjectVersion
    else:
        lib_name = "libess_32.so"+ "." + sharedObjectVersion
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
lib.ess_detect.argtypes = [POINTER(ctypes.c_uint16)]
lib.ess_initialization.argtypes = [ctypes.c_uint16]
lib.ess_initialization.restype = ctypes.c_uint64
lib.ess_close.argtypes = [ctypes.c_uint64]
lib.ess_get_serial.argtypes =  [ctypes.c_uint64, POINTER(ctypes.c_uint16), POINTER(ctypes.c_uint16)]
lib.ess_read.argtypes = [ctypes.c_uint64, POINTER(ctypes.c_uint8)]
lib.ess_write.argtypes = [ctypes.c_uint64, POINTER(ctypes.c_uint8)]
lib.ess_set_two_switch.argtypes = [ctypes.c_uint64, ctypes.c_uint8, ctypes.c_uint8]
lib.ess_set_rot_switch.argtypes = [ctypes.c_uint64, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
lib.ess_set_all_two_switch.argtypes = [ctypes.c_uint64, ctypes.c_uint8]
lib.ess_set_all_rot_switch.argtypes = [ctypes.c_uint64, ctypes.c_uint8, ctypes.c_uint8]
lib.ess_get_data_two_switch.argtypes =  [ctypes.c_uint64, ctypes.c_uint8, 
            POINTER(ctypes.c_uint8), POINTER(ctypes.c_uint8), 
            POINTER(ctypes.c_uint8), POINTER(ctypes.c_uint8),
            POINTER(ctypes.c_uint8), POINTER(ctypes.c_uint8)]
lib.ess_get_data_rot_switch.argtypes =  [ctypes.c_uint64, ctypes.c_uint8, 
            POINTER(ctypes.c_uint8), POINTER(ctypes.c_uint8), 
            POINTER(ctypes.c_uint8), POINTER(ctypes.c_uint8),
            POINTER(ctypes.c_uint8), POINTER(ctypes.c_uint8),
            POINTER(ctypes.c_uint8)]

def ess_detect():
    serial_number_list = (ctypes.c_uint16*256)(*([0]*256))
    c_error = c_uint8(lib.ess_detect(serial_number_list))
    serial_number_list = list(filter(None, serial_number_list))
    return (c_error.value, serial_number_list)
  
def ess_initialization(serial = 0):
    """Initializes a session with the Switchboard whose serial number was provided.
    The default serial number (0) initializes the first Switchboard found"""
    handle = c_uint64(lib.ess_initialization(c_uint16(serial)))
    return handle.value
    
def ess_close(handle):
    """Closes the connection with the Switchboard"""
    c_error = c_uint8(lib.ess_close(c_uint64(handle)))
    return c_error.value
    
def ess_get_serial(handle):
    """Read the serial number and firmware version of the Switchboard"""
    serial = ctypes.c_uint16(0)
    sb_version = ctypes.c_uint16(0)
    c_error = c_uint8(lib.ess_get_serial(c_uint64(handle),
                    byref(serial), byref(sb_version)))
    return (c_error.value, serial.value, sb_version.value)

def ess_set_rot_switch(handle, port, position, direction):
    c_error = c_uint8(lib.ess_set_rot_switch(ctypes.c_uint64(handle), 
                    c_uint8(port), c_uint8(position), c_uint8(direction)))
    return c_error.value
                            
def ess_set_all_rot_switch(handle, position, direction):
    c_error = c_uint8(lib.ess_set_all_rot_switch(c_uint64(handle), 
                    c_uint8(position), c_uint8(direction)))
    return c_error.value
                            
def ess_set_two_switch(handle, port, position):
    c_error = c_uint8(lib.ess_set_two_switch(c_uint64(handle),  
                    c_uint8(port), c_uint8(position)))
    return c_error.value
                            
def ess_set_all_two_switch(handle, position):
    c_error = c_uint8(lib.ess_set_all_two_switch(c_uint64(handle), 
                    c_uint8(position)))
    return c_error.value

def ess_get_data_rot_switch(handle, port):
    presence = ctypes.c_uint8(0)
    switch_type = ctypes.c_uint8(0)
    model = ctypes.c_uint8(0)
    soft_vers = ctypes.c_uint8(0)
    err_code = ctypes.c_uint8(0)
    processing = ctypes.c_uint8(0)
    position = ctypes.c_uint8(0)

    c_error = c_uint8(lib.ess_get_data_rot_switch(c_uint64(handle), 
                    c_uint8(port), byref(presence), byref(switch_type), 
                    byref(model), byref(soft_vers), byref(err_code),
                    byref(processing), byref(position)))
    return (c_error.value, presence.value, switch_type.value, model.value, 
            soft_vers.value, err_code.value, processing.value, position.value)
                           
def ess_get_data_two_switch(handle, port):
    presence = ctypes.c_uint8(0)
    switch_type = ctypes.c_uint8(0)
    model = ctypes.c_uint8(0)
    soft_vers = ctypes.c_uint8(0)
    status = ctypes.c_uint8(0)
    origin = ctypes.c_uint8(0)

    c_error = c_uint8(lib.ess_get_data_two_switch(handle, c_uint8(port), 
                    byref(presence), byref(switch_type), byref(model),  
                    byref(soft_vers), byref(status), byref(origin)))
    return (c_error.value, presence.value, switch_type.value, model.value, 
            soft_vers.value, status.value, origin.value)
