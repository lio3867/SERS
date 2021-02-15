# -*- coding: utf-8 -*-
"""This module contains the exceptions raised by the FRP SDK, to enable 
application control via try/except blocks"""

from __future__ import print_function
import sys
import inspect

class FRP_NoFlowboard(Exception):
    """Raised if the specified Flowboard is not connected to the computer"""
    
class FRP_InvalidPort(Exception):
    """Raised if the specified port does not exist on the Flowboard"""
    
class FRP_NoFlowUnit(Exception):
    """Raised if no Flow Unit is connected to the specified port"""
    
class FRP_InvalidCalibration(Exception):
    """Raised if the specified calibration table is invalid"""
    
class FRP_CalibrationNotSupported(Exception):
    """Raised if the specified calibration table is valid but not supported
    by the specified Flow Unit"""
    
def doc():
    for c in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        print("{} \n    {}\n".format(c[0], c[1].__doc__))