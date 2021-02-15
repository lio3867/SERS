# -*- coding: utf-8 -*-
"""Module for communicating with the Fluigent Flowboard and its Flow Units"""
from . import low_level
from . import utils
from .exceptions import FRP_NoFlowboard, FRP_NoFlowUnit

class Flowboard(object):
    """Represents a Flowboard instrument, allowing the user to send 
    commands and read values from the device and the connected Flow Units"""
    @staticmethod
    def detect():
        """Returns a list of the serial numbers of the Flowboards 
        currently connected to the computer via USB"""
        c_error, serial_number_list = low_level.frp_detect();
        utils.parse_error(c_error)
        return serial_number_list
    
    def __init__(self, serial_number = 0):
        available_devices = Flowboard.detect()
        if not available_devices:
            utils.parse_error(1)
        if serial_number != 0 and serial_number not in available_devices:
            utils.parse_error(1)
        self.__handle = low_level.frp_initialization(serial_number)
        c_error, self.__serial, self.__version = low_level.frp_get_serial(self.__handle)
        try:
            utils.parse_error(c_error)
        except FRP_NoFlowboard:
            low_level.frp_close(self.__handle)
            self.__handle = 0
            raise
            
    def get_available_ports(self):
        """Returns a list of the Flowboard ports that have Flow Units connected
        to them"""
        ports = []
        for port in range(1,9):
            try:
                self.get_flowrate(port)
            except FRP_NoFlowUnit:
                continue
            else:
                ports.append(port)
        return ports
        
                
    def __iter__(self):
        """Allows iterating over the connected Flow Units in a for loop"""
        for port in range(1,9):
            try:
                self.get_flowrate(port)
            except FRP_NoFlowUnit:
                continue
            else:
                yield Flowboard.FlowUnit(self, port)
            
    def __getitem__(self, port):
        """Return a Flow Unit object when Flowboard is indexed with 
        the bracket [] syntax"""
        # Get data to ensure the Flow Unit is there. Raises an error otherwise
        self.get_flowrate(port)
        return Flowboard.FlowUnit(self, port)
        
    @property
    def serial(self):
        """The Flowboard's serial number"""
        c_error, serial_number, version = low_level.frp_get_serial(self.__handle)
        utils.parse_error(c_error)
        return serial_number
    
    def get_flowunit_data(self, port):
        """Returns data on the Flow Unit connected to the specified port, 
        as a dictionary containing the following keys:
        calibration  : 0 for water, 1 for isopropanol
        resolution   : measurement resolution in bits
        article_code : String that identifies the type of Flow Unit
        scale_factor : factor to convert the raw sensor value into a
                       measurement in the sensor's unit
        unit         : volume unit used by the sensor
                         0 : nanoliters
                         1 : microliters
                         2 : milliliters 
        timebase     : time unit used by the sensor
                         0 : microsecond
                         1 : millisecond
                         2 : second
                         3 : minute"""
        port_number = utils.parse_port(port)
        c_error, calibration, resolution, article_code, scale_factor, unit, \
                        timebase = low_level.frp_data_FU(self.__handle, port_number)
        utils.parse_error(c_error)
        return {"calibration" : calibration,
                "resolution" : resolution+9,
                "article_code" : article_code,
                "scale_factor" : scale_factor,
                "unit" : unit,
                "timebase" : timebase}
        
    def get_flowrate(self, port):
        """Returns the current flow rate of the Flow Unit connected to the 
        specified port
        port : a number from 1 to 8, as displayed on the instrument's 
               front panel"""
        port_number = utils.parse_port(port)
        c_error, flowrate, timestamp = low_level.frp_read_flow(self.__handle, port_number)
        utils.parse_error(c_error)
        return flowrate
    
    def set_calibration(self, port, calibration):
        """Set the flow rate calibration to use on the Flow Unit connected to 
        the specified port"""
        port_number = utils.parse_port(port)
        cal_number = utils.parse_calibration(calibration)
        c_error = low_level.frp_set_calibration(self.__handle, port_number, cal_number)
        utils.parse_error(c_error)
        
    def __repr__(self):
        return "Fluigent Flowboard S/N With {} Flow Units".format(len(self.get_available_ports()))
        
    def __del__(self):
        """Close the handle so that the shared library stops communicating
        with the instrument"""
        try:
            if self.__handle != 0:
                low_level.frp_close(self.__handle)
        except:
            pass
          
    class FlowUnit(object):
        """Represents an individual Flow Unit connected to a Flowboard. 
        This class should not be instantiated directly. To obtain a 
        FlowUnit instance, initialize the corresponding Flowboard and
        index it (e.g., flow_unit = flowboard[1])"""
        def __init__(self, instrument, port):
            self.__instrument = instrument
            self.__port = port
            self.__unit = "ul/min"
            
        def get_flowrate(self):
            """Returns the current flow rate measurement on the Flow Unit
            in ul/min"""
            return self.__instrument.get_flowrate(self.__port)
        
        def get_data(self):
            """Data on the Flow Unit connected to the specified port, 
            as a dictionary containing the following keys:
            calibration  : 0 for water, 1 for isopropanol
            resolution   : measurement resolution in bits
            article_code : String that identifies the type of Flow Unit
            scale_factor : factor to convert the raw sensor value into a
                           measurement in the sensor's unit
            unit         : volume unit used by the sensor
                             0 : nanoliters
                             1 : microliters
                             2 : milliliters 
            timebase     : time unit used by the sensor
                             0 : microsecond
                             1 : millisecond
                             2 : second
                             3 : minute"""
            return self.__instrument.get_flowunit_data(self.__port)
        
        def set_calibration(self, cal):
            """Set the flow rate calibration to use on the Flow Unit connected
            to the specified port"""
            self.__instrument.set_calibration(self.__port, cal)
            
        @property
        def serial(self):
            """The serial number of the Flowboard to which this Flow Unit is
            connected"""
            return self.__instrument.serial
        
        @property
        def port(self):
            """The port to which this Flow Unit is connected on the Flowboard,
            as displayed on the instrument's front panel (1 to 8)"""
            return self.__port
        
        @property
        def flowrate(self):
            """Current flow rate measurement in ul/min"""
            return self.get_flowrate()
            
        @property
        def data(self):
            """Data on the Flow Unit connected to the specified port, 
            as a dictionary containing the following keys:
            calibration  : 0 for water, 1 for isopropanol
            resolution   : measurement resolution in bits
            article_code : String that identifies the type of Flow Unit
            scale_factor : factor to convert the raw sensor value into a
                           measurement in the sensor's unit
            unit         : volume unit used by the sensor
                             0 : nanoliters
                             1 : microliters
                             2 : milliliters 
            timebase     : time unit used by the sensor
                             0 : microsecond
                             1 : millisecond
                             2 : second
                             3 : minute"""
            return self.get_data()
             
        @property
        def unit(self):
            """Flow rate unit used by this Flow Unit, as a string"""
            return self.__unit
            
        @property
        def calibration(self):
            """Calibration table used by this Flow Unit. Set this property to 
            change the calibration
            0 if calibrated for water
            1 if calibrated for isopropanol"""
            return self.data["calibration"]
        
        @calibration.setter
        def calibration(self, cal):
            return self.set_calibration(cal)
        
        def __repr__(self):
            return "{} on port {} of Flowboard S/N {}".format(self.data["article_code"], 
                    self.__port, self.__instrument.serial)
            
def detect():
    """Returns a list of the serial numbers of the Flowboards 
    currently connected to the computer via USB"""
    return Flowboard.detect()
        
