# -*- coding: utf-8 -*-
"""Internal helper functions for the SDK. These functions are not meant to be
invoked directly by the user
"""
from .exceptions import ESS_NoSwitchboard, ESS_InvalidPort, ESS_NoSwitch
from .exceptions import ESS_InvalidPosition, ESS_WrongSwitchType, ESS_SwitchError

ports = "ABCD12345678"

error_messages =  {1: "Switchboard not connected",
                   2: "Invalid command for this type of Switch",
                   3: "No Switch on this port",
                   4: "This port does not support this type of Switch",
                   }

def parse_error(c_error):
    if c_error == 1:
        raise ESS_NoSwitchboard(error_messages[c_error])
    elif c_error == 2:
        raise ESS_InvalidPosition(error_messages[c_error])
    elif c_error == 3:
        raise ESS_NoSwitch(error_messages[c_error])
    elif c_error == 4:
        raise ESS_WrongSwitchType(error_messages[c_error])
        
def parse_switch_error(error_code):
    if error_code:
        raise ESS_SwitchError("Rot Switch error state {}".format(error_code))

def wrong_port_error():
    raise ESS_InvalidPort("Port is A-D for Rotating Switches or 1-8 for 2-Switches")
   
def parse_port(port):
    if type(port) == str:
        port = port.upper()
        if len(port) != 1:
            wrong_port_error()
        elif port in "ABCD":
            return "rot", "ABCD".index(port)
        elif port in "12345678":
            return "two", "12345678".index(port)
        else:
            wrong_port_error()
    elif type(port) == int and port > 0 and port <= 8:  
        return "two", port-1
    else:
        wrong_port_error()
        
    
def parse_switch_model(switch_type, model):
    """Returns the name of the Switch and the available positions"""
    if switch_type == 1:
        return "2-Switch", (1, 2)
    elif model == 1:
        return "M-Switch", list(range(1,11))
    elif model == 3:
        return "L-Switch", (1, 2)
    else:
        raise Exception("Invalid Switch type {} - {}".format(switch_type, model))
