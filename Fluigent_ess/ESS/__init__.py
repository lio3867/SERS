from . import low_level
from . import utils
from .exceptions import ESS_NoSwitchboard, ESS_NoSwitch
from .exceptions import ESS_SwitchNotResponding, ESS_InvalidPosition
import time

class Switchboard(object):
    @staticmethod
    def detect():
        """Returns a list of the serial numbers of the Switchboards 
        currently connected to the computer via USB"""
        c_error, serial_number_list = low_level.ess_detect();
        utils.parse_error(c_error)
        return serial_number_list
    
    def __init__(self, serial_number = 0):
        """Creates an object that respresents the Switchboard device"""
        available_devices = Switchboard.detect()
        if not available_devices:
            utils.parse_error(1)
        if serial_number != 0 and serial_number not in available_devices:
            utils.parse_error(1)
        self.__handle = low_level.ess_initialization(serial_number)
        c_error, self.__serial, self.__sb_version = \
                low_level.ess_get_serial(self.__handle)
        try:
            utils.parse_error(c_error)
        except ESS_NoSwitchboard:
            low_level.ess_close(self.__handle)
            self.__handle = 0
            raise
            
    @property
    def serial(self):
        """The Switchboard's serial number"""
        c_error, serial_number, version = low_level.ess_get_serial(self.__handle)
        utils.parse_error(c_error)
        return serial_number
    
    def get_available_ports(self):
        """Returns a list of the Switchboard ports that have Switches connected"""
        ports = []
        for port in utils.ports:
            try:
                self.get_switch_data(port)
            except ESS_NoSwitch:
                continue
            else:
                ports.append(port)
        return ports

    def __iter__(self):
        """Allows iterating through all the available Switches in a for loop"""
        for port in utils.ports:
            try:
                self.get_switch_data(port)
            except ESS_NoSwitch:
                continue
            else:
                yield Switchboard.Switch(self, port)
            
    def __getitem__(self, port):
        """Return a switch object when Switchboard is indexed with the
        bracket [] syntax"""
        # Get data to ensure the Switch is there. Raises an error otherwise
        data = self.get_switch_data(port)
        del data
        return Switchboard.Switch(self, port)
    
    def get_position(self, port):
        """Returns the current position of the Switch at the specified port"""
        data = self.get_switch_data(port)
        return data["position"]
            
    def set_position(self, port, position, direction = 0, wait = True):
        """Set the position of a connected Switch
            port      : The Switchboard port to which the Switch is connected
            pos       : The desired position 
                          1-10 for the M-Switch, 
                          1-2 for the 2-Switch and L-Switch
            direction : Turning direction (only affects the M-Switch)
                          0 for shortest path (default)
                          1 for counterclockwise
                          2 for clockwise
            wait      : If True, block until the Switch has finished turning"""
        switch_type, port_number = utils.parse_port(port)
        data = self.get_switch_data(port)
        if position not in data["available_positions"]:
            raise ESS_InvalidPosition("Positions for the {} are {}".format(data["model"], data["available_positions"]))
        assert switch_type in ("rot", "two")
        if switch_type == "rot":
            c_error = low_level.ess_set_rot_switch(self.__handle, port_number,  
                                         position-1, direction)
        elif switch_type == "two":
            c_error = low_level.ess_set_two_switch(self.__handle, port_number, 
                                                   position-1)
            wait = False # Do not wait for 2-Switch
        utils.parse_error(c_error)
        wait_count = 0
        wait_timeout = 3
        wait_step = 0.05
        while wait:
            time.sleep(wait_step)
            wait_count += wait_step
            if wait_count > wait_timeout:
                raise ESS_SwitchNotResponding("Set position failed")
            wait = (self.get_position(port) != position)
            
        
    def get_positions(self, port):
            """Returns a list of the positions that the Switch  at the 
            specifiedcan be set to"""
            data = self.get_switch_data(port)
            return data["available_positions"]
        
    def position(self, port, pos = None, direction = 0, wait = True):
        if pos is None:
            return self.get_position(port)
        else:
            self.set_position(port, pos, direction, wait)
        
    def get_switch_data(self, port):
        """Returns data on the Switch connected to the specified port, as a 
        dictionary containing the following keys:
        model     : "2-Switch", "M-Switch" or "L-Switch"
        soft_vers : firmware version of the Switch's processor
        position  : Switch's current position
        origin    : 0 if the Switch was last switched by software
                    1 if it was last switched by a button press
                    (only for 2-Switches)
        processing: 1 if the Switch is still turning, 0 otherwise
        available_positions: The positions this Switch can be set to"""
        switch_data = {}
        switch_type, port_number = utils.parse_port(port)
        assert switch_type in ("rot", "two")
        if switch_type == "rot":
            (c_error, presence, switch_type, model, soft_vers, err_code, 
            processing, position) = \
                    low_level.ess_get_data_rot_switch(self.__handle, port_number)
            origin = 0    
        elif switch_type == "two":
            (c_error, presence, switch_type, model, soft_vers, position, 
            origin) = \
                    low_level.ess_get_data_two_switch(self.__handle, port_number)
            processing = 0
            err_code = 0
        utils.parse_error(c_error)
        utils.parse_switch_error(err_code)
        switch_name, valid_positions = utils.parse_switch_model(switch_type, model)
        switch_data["model"] = switch_name
        switch_data["soft_vers"] = soft_vers
        switch_data["position"] = position + 1
        switch_data["origin"] = origin
        switch_data["processing"] = processing
        switch_data["available_positions"] = valid_positions
        return switch_data
    
    def set_all_rot_switch(self, position, direction = 0, wait = True):
        """Sets all the Rotating Switches to the specified position
            position  : The desired position 
                          1-10 for the M-Switch, 
                          1-2 for the 2-Switch and L-Switch
            direction : Turning direction (only affects the M-Switch)
                          0 for shortest path (default)
                          1 for counterclockwise
                          2 for clockwise
            wait      : If True, block until the Switches have finished 
                        turning"""
        c_error = low_level.ess_set_all_rot_switch(self.__handle, position-1, direction)
        utils.parse_error(c_error)
        wait_count = 0
        wait_timeout = 3
        wait_step = 0.05
        while wait:
            wait = False
            time.sleep(wait_step)
            wait_count += wait_step
            if wait_count > wait_timeout:
                raise ESS_SwitchNotResponding("Set position failed")
            for port in "ABCD":
                try:
                    data = self.get_switch_data(port)
                    if data["model"] == "L-Switch" and position > 2:
                        continue
                    if data["position"] != position:
                        wait = True
                except ESS_NoSwitch:
                    continue
            
        
    def set_all_two_switch(self, position):
        """Sets all the 2-Switches to the specified position
           position  : The desired position (1 or 2)"""
        c_error = low_level.ess_set_all_two_switch(self.__handle, position-1)
        utils.parse_error(c_error)
            
    def __repr__(self):
        return "Fluigent Switchboard With {} Switches".format(len(self.get_available_ports()))
        
    def __del__(self):
        """Close the handle so that the shared library stops communicating
        with the instrument"""
        try:
            if self.__handle != 0:
                low_level.ess_close(self.__handle)
        except:
            pass

    class Switch(object):
        """Represents an individual Switch connected to a Switchboard. 
        This class should not be instantiated directly. To obtain a Channel 
        instance, initialize the corresponding instrument and then index it
        (e.g., switch = instrument[1], switch = instrument["A"]) """
        def __init__(self, switchboard, port):
            self.__switchboard = switchboard
            self.__port = port
            
        def get_data(self):
            """Returns data on the Switch connected to the specified port, as  
            a dictionary containing the following keys:
            model     : "2-Switch", "M-Switch" or "L-Switch"
            soft_vers : firmware version of the Switch's processor
            position  : Switch's current position
            origin    : 0 if the Switch was last switched by software
                        1 if it was last switched by a button press
                        (only for 2-Switches)
            processing: 1 if the Switch is still turning, 0 otherwise
            available_positions: The positions this Switch can be set to"""
            return self.__switchboard.get_switch_data(self.__port)
            
        def get_position(self):
            """Returns the current position of the Switch"""
            switch_data = self.data
            if switch_data["processing"]:
                raise Warning("Switch is still turning")
            return switch_data["position"]
            
        def set_position(self, pos, direction = 0, wait = True):
            """Set the position of the Switch. This method offers additional 
            options not available through the position property
            pos       : the desired position
            direction : Turning direction (only affects the M-Switch)
                        0 for fastest path (default), 
                        1 for counterclockwise
                        2 for clockwise
            wait      : If True, block until the Switch has finished turning"""
            self.__switchboard.set_position(self.__port, pos, direction, wait)
            
        def get_positions(self):
            """Returns a list of the positions that this Switch can be set to"""
            return self.__switchboard.get_positions(self.__port)
        
        @property
        def positions(self):
            """A list of the positions that this Switch can be set to"""
            return self.get_positions()
        
        @property
        def position(self):
            """The current position of the Switch. Assigning a new value
            will case the Switch to change.
            e.g., switch.position = new_position
            Setting the Switch in this manner will cause it to use the 
            default options for the M-Switch (take the shortest path to the 
            new position and wait until the Switch stops turning before 
            exiting the function). To set the switch with different options,
            use the set_position() method"""
            return self.get_position()
        
        @position.setter
        def position(self, pos):
            self.set_position(pos)
        
        @property        
        def data(self):
            """Data on the Switch connected to the specified port, as a 
            dictionary containing the following keys:
            model     : "2-Switch", "M-Switch" or "L-Switch"
            soft_vers : firmware version of the Switch's processor
            position  : Switch's current position
            origin    : 0 if the Switch was last switched by software
                        1 if it was last switched by a button press
                        (only for 2-Switches)
            processing: 1 if the Switch is still turning, 0 otherwise
            available_positions: The positions this Switch can be set to"""
            return self.get_data()
            
        @property
        def port(self):
            """The Switchboard port to which the Switch is connected"""
            return self.__port
        
        def __repr__(self):
            switch_data = self.data
            return "{} port {} position {}".format(switch_data["type"], 
                            self.__port, switch_data["position"])
        
def detect():
        """Returns a list of the serial numbers of the Switchboards 
        currently connected to the computer via USB"""
        return Switchboard.detect()
