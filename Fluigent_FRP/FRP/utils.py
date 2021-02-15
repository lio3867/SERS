from .exceptions import FRP_NoFlowboard, FRP_InvalidPort, FRP_NoFlowUnit
from .exceptions import FRP_InvalidCalibration, FRP_CalibrationNotSupported

error_messages =  {1: "Flowboard not connected",
                   2: "No Flow Unit on this port",
                   3: "Invalid calibration table for this Flow Unit"
                   }

def parse_error(c_error):
    if c_error == 1:
        raise FRP_NoFlowboard(error_messages[c_error])
    if c_error == 2:
        raise FRP_NoFlowUnit(error_messages[c_error])
    if c_error == 3:
        raise FRP_CalibrationNotSupported(error_messages[c_error])

def parse_port(port):
    port = int(port)
    if int(port) < 1 or int(port) > 8:
        raise FRP_InvalidPort("Port is between 1 and 8")
    return port-1

def parse_calibration(calibration):
    if type(calibration) is str:
        if calibration.upper() in ["0", "WATER", "H2O"]:
            calibration = 0
        elif calibration.upper() in ["1", "IPA", "ISOPROPANOL", "ISOPROPYL ALCOHOL"]:
            calibration = 1
    if calibration in [0, 1]:
        return calibration
    else: 
        raise FRP_InvalidCalibration("Invalid Calibration {}. \
                             Options are 'H2O' and 'IPA'".format(calibration))
        