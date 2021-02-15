"""This module contains the exceptions raised by the ESS SDK, to enable 
application control via try/except blocks"""

from __future__ import print_function
import sys
import inspect

class ESS_NoSwitchboard(Exception):
    """Raised if the specified Switchboard is not connected to the computer"""

class ESS_NoSwitch(Exception):
    """Raised if there is no Switch at the specified port"""

class ESS_InvalidPort(Exception):
    """Raised if the specified port does not exist on the Switchboard"""

class ESS_InvalidPosition(Exception):
    """Raised if the specified position is not available for the specified 
    Switch"""
    
class ESS_WrongSwitchType(Exception):
    """Raised if a 2-Switch is connected to a Rot Switch port or vice-versa"""
    
class ESS_SwitchError(Exception):
    """Raised if a Rot Switch returns an error code"""
    
class ESS_SwitchNotResponding(Exception):
    """Raised if a Rot Switch fails to turn to the requested position"""
    
def doc():
    for c in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        print("{} \n    {}\n".format(c[0], c[1].__doc__))
