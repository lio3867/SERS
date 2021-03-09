# -*- coding: utf-8 -*-
"""
Created on Tue Feb  4 09:59:04 2020

@author: Ngoc Mai DUONG


"""
# spec.close()

import os
from pathlib import Path
import numpy as np
import pandas as pd
import time
from time import sleep
import datetime
from statistics import mean
from matplotlib import pyplot as plt
##
from flask_socketio import emit

try:
    from Fluigent_ess.ESS import Switchboard
    from Fluigent_FRP.FRP import Flowboard
    from Fluigent.SDK import fgt_init, fgt_close
    from Fluigent.SDK import fgt_set_pressure, fgt_get_pressure, fgt_get_pressureRange
    ###
    import usb.core
    import seabreeze.spectrometers as sb
except:
    print('did not import some of modules')

# Clear all
try:
    from IPython import get_ipython
    get_ipython().magic('reset -sf')
except:
    print("Issue with IPython")

from sys import platform as _platform

def find_platform():
    '''
    Find which platform is currently used
    '''
    print('platform is ',_platform)
    if _platform == "linux" or _platform == "linux2":
       platf = 'lin'
    elif _platform == "darwin":
       platf = 'mac'
    elif _platform == "win32":
       platf = 'win'
    return platf

def chose_server(platf):
    '''
    '''
    if platf =='win':
        import gevent as server
        from gevent import monkey
        monkey.patch_all()
    else:
        import eventlet as server
        server.monkey_patch()
    return server

platf  = find_platform()
server = chose_server(platf)

class INPUT():
    '''
    '''
    def __init__(self):
        ## Set INPUT
        self.my_ESS_input = np.array([1,])
        self.make_pressure_gate_variables()
        self.t_integration_s = 15   #s
        self.t_step_min = 3         #min
        self.delta_P = 20
        self.cycles = 3
        ## other variables
        self.step_index = 0
        self.plus_minus = 1
        ## print info
        self.print_params()
        self.estimate_experiment_time()

    def make_pressure_gate_variables(self):
        '''
        '''
        self.injected = ['Oil', 'NPs', 'CrosLIn', 'Water', 'Titrant']
        self.pressure_input = { 'P_Oil_in':780,'P_NPs_in':770,'P_CrosLIn_in':580,'P_Water_in':600,'P_Titrant_in':600 }
        self.gate_input = { 'gate_Oil':0,'gate_NPs':1,'gate_CrosLIn':2,'gate_Water':4,'gate_Titrant':5 }
        [setattr(self, k, v) for k,v in self.pressure_input.items()]       # self.P_Oil_in, self.P_NPs_in etc..
        [setattr(self, k, v) for k,v in self.gate_input.items()]           # self.gate_Oil, self.gate_NPs etc..

    def print_params(self):
        '''
        '''
        print( f'my_ESS_input =  {self.my_ESS_input}')
        print( f'pressure_input = {self.pressure_input}')
        print( f't_integration_s = {self.t_integration_s}' )
        print( f'delta_P = {self.delta_P}' )
        print( f'cycles = {self.cycles}' )
        self.N_points()
        print( f'n points = {self.n_points}' )

    def N_points(self):
        '''
        '''
        self.t_each_step = self.t_step_min*60 # s
        self.t_integration = self.t_integration_s*(1e6) # 1e6 = 1s
        self.n_points = self.t_each_step/(self.t_integration/1e6)

    def estimate_experiment_time(self):
        '''
        '''
        ## Estimate the experiment time
        self.N_points()
        print( f'n points = {self.n_points}' )
        self.n_SW = self.my_ESS_input.size
        self.t_exp_estimated = self.n_SW*self.t_step_min*10*self.cycles # in min
        self.t_exp_estimated_hour = round(self.t_exp_estimated/60, 2)
        print(f'Experiment estimated time = {self.t_exp_estimated_hour} (hours)')

class INIT_INSTRUMENTS():
    def __init__(self):
        try:
            self.set_ESS()
            self.set_FRP()
            self.init_spectro()
            self.create_dataframe()
        except:
            print("Some devices not detected perhaps")

    def set_ESS(self):
        '''
        '''
        ESS_serial_numbers = Switchboard.detect()
        self.switchboard = Switchboard(ESS_serial_numbers[0])

    def set_FRP(self):
        '''
        Set up FRP
        '''
        FRP_serial_numbers = Flowboard.detect()
        self.flowboard = Flowboard(FRP_serial_numbers[0])
        self.flowboard.set_calibration(1, "Water")
        self.flowboard.set_calibration(2, "Water")
        self.flowboard.set_calibration(3, "Water")
        self.flowboard.set_calibration(4, "Water")
        self.available_FRP_ports = self.flowboard.get_available_ports()

    def init_spectro(self):
        '''
        Initialize Spectrometer
        '''
        usb.core.find()
        devices = sb.list_devices()
        self.spec = sb.Spectrometer(devices[0])
        self.spec.integration_time_micros(self.t_integration)
        self.wl = self.spec.wavelengths()

class DATA_HANDLING():
    '''
    '''
    def __init__(self):
        self.prepare_folders()
        self.prepare_df_info()
        self.create_dataframe()

    def prepare_folders(self):
        '''
        '''
        if not os.path.exists('Data'):
            os.mkdir('Data')

    def prepare_df_info(self):
        '''
        '''
        t = ['t(s)']
        SW_step = ['SW_step']
        switch = ['SW_I', 'SW_II']
        step = ['step']
        pressure = ['P_Oil','P_NPs','P_CrosLIn','P_Water','P_Titrant',
                'P_Oil_m','P_NPs_m','P_CrosLIn_m','P_Water_m','P_Titrant_m']
        FRP = ['Q_NPs', 'Q_CrosLIn','Q_Water','Q_Titrant']
        ltit = [ pd.DataFrame(columns = i) for i in [ t, SW_step, switch, step, pressure, FRP ]]
        self.df_info = pd.concat(ltit, axis=1, sort=False)

    def create_dataframe(self):
        '''
        Create a Dataframe
        '''

        self.prepare_df_info()
        self.dfIntensity = pd.DataFrame(columns = self.wl)
        ##
        my_file = pd.concat([self.df_info,self.dfIntensity], axis=1, sort=False)
        self.today = datetime.datetime.today().strftime('%Y%m%d-%H%M')
        my_file.to_csv('Data\d_{}.csv'.format(self.today), index=True, sep=';')

    def concat_infos_and_intensities(self):
        '''
        '''
        self.dfIntensity.loc[len(self.dfIntensity)] = self.intensities
        self.plot_intensities()
        self.df_info.loc[len(self.df_info)] = [self.time_string, self.sw_step, self.port_I, self.port_II, self.step_index,
                                self.P_Oil_in, self.P_NPs_in, self.P_CrosLIn_in, self.P_Water_temp, self.P_Titrant_temp,
                                round(self.P_Oil_m,2),round(self.P_NPs_m,2),round(self.P_CrosLIn_m,2),
                                round(self.P_Water_m,2), round(self.P_Titrant_m,2),
                                round(self.Q_NPs,2),round(self.Q_CrosLIn,2),round(self.Q_Water,2),round(self.Q_Titrant,2)]
        self.df_raw_data = pd.concat([self.df_info,self.dfIntensity], axis=1, sort=False)

    def save_to_csv(self):
        '''
        '''
        try:
            self.df_raw_data.to_csv(f'Data\d_{self.today}.csv', mode='a', header=False, index=True, sep=';')
            self.df_raw_data = pd.DataFrame(columns=self.df_raw_data.columns)
        except:
            print("self.df_raw_data has to be created before saving...")

class INTERF():
    '''
    Interface
    '''
    def __init__(self):
        pass
        # emit('new_spec', '')
        # server.sleep(0.05)

    def plot_intensities(self):
        '''
        '''
        try:
            plt.xlim(self.rangex[0],self.rangex[1])
            plt.ylim(self.rangey[0],self.rangey[1])
            plt.plot(self.intensities)
            addr_img = Path('sers_interface') / 'static' / 'curr_pic' / 'intensities.png'
            plt.savefig( str(addr_img) )
            emit('new_spec', '')
            sleep(1)
            server.sleep(0.05)
        except:
            # print('we are not using interface')
            pass

# class TEST():
#     '''
#     Test socket
#     '''
#     def __init__(self):
#         pass
#
#
#     def test_socket(self):
#         '''
#         '''
#
#         emit('new_spec', '')
#         server.sleep(0.05)


class EXPERIM(INPUT,INIT_INSTRUMENTS,DATA_HANDLING,INTERF):
    '''
    '''
    def __init__(self):
        try:
            INPUT.__init__(self)
            INIT_INSTRUMENTS.__init__(self)
            DATA_HANDLING.__init__(self)
        except:
            print('not loading for just interface')
        INTERF.__init__(self)

    def stablize_to_balance_state(self, t = 20):
        '''
        P_in values
        '''
        print('stabilizing ...')
        [ fgt_set_pressure(getattr(self, f'gate_{inj}'), getattr(self, f'P_{inj}_in')) for inj in self.injected ]
        time.sleep(t) #sec

    def print_info(self):
        '''
        '''
        time_start_tuple = time.localtime() # get struct_time
        time_start = time.strftime("%H:%M:%S", time_start_tuple)
        print('Start experiment at ', time_start)
        self.switchboard.set_position("A", self.my_ESS_input[0])
        self.switchboard.set_position("B", self.my_ESS_input[0])
        print( f"Switch on port A is at position {self.switchboard.get_position('A')}" )
        print( f"Switch on port B is at position {self.switchboard.get_position('B')}" )

    def launch_exp(self):
        '''
        '''
        self.sw_step = 0
        for item in self.my_ESS_input:
            self.sw_step +=  1
            self.port_I = item
            self.port_II = item
            ##
            self.switchboard.set_position("A", self.port_I)
            self.switchboard.set_position("B", self.port_II)
            print( f"Switch on port A is at position {self.switchboard.get_position('A')}" )
            print( f"Switch on port B is at position {self.switchboard.get_position('B')}" )
            ##
            self.sweep_pressures()

    def sweep_pressures(self):
        '''
        Go through various pressures
        '''
        self.cycle = 0                                     # first half of the period
        self.P_Water_temp = self.P_Water_in - self.delta_P
        self.P_Titrant_temp = self.P_Titrant_in + self.delta_P
        for item in np.arange(50):
            self.Q_Water = self.flowboard.get_flowrate(self.available_FRP_ports[2])
            self.Q_Titrant = self.flowboard.get_flowrate(self.available_FRP_ports[3])
            # if self.Q1 > 1 and self.Q2 > 1 and self.Q1 < 54 and self.Q2 < 54 and cycle < cycles:
            if self.cycle <= self.cycles:
                self.one_cycle()
            else:
                break

    def one_cycle(self):
        '''
        '''
        self.P_Water_temp +=  self.plus_minus*self.delta_P
        self.P_Titrant_temp -=  self.plus_minus*self.delta_P

        fgt_set_pressure(self.gate_Water, self.P_Water_temp)
        fgt_set_pressure(self.gate_Titrant, self.P_Titrant_temp)
        time.sleep(15)

        print(f'Applying = {self.P_Oil_in},{self.P_NPs_in},{ self.P_CrosLIn_in},{self.P_Water_temp},{self.P_Titrant_temp}')
        self.df_info =  pd.DataFrame(columns=self.df_info.columns)
        self.dfIntensity = pd.DataFrame(columns=self.dfIntensity.columns)
        self.step_index +=  1     # increment step
        self.one_step()           # make the step
        self.save_to_csv()        # save

    def one_step(self):
        '''
        Run step by step until , then register results
        Define self.P_Oil_m, self.P_NPs_m etc..
        '''
        for i in range(int(self.n_points)):
            self.Q_NPs = self.flowboard.get_flowrate(self.available_FRP_ports[0])
            self.Q_CrosLIn = self.flowboard.get_flowrate(self.available_FRP_ports[1])
            self.Q_Water = self.flowboard.get_flowrate(self.available_FRP_ports[2])
            self.Q_Titrant = self.flowboard.get_flowrate(self.available_FRP_ports[3])
            cnd0 = 2 < self.Q_Titrant < 80
            cnd1 = 2 < self.Q_Water < 80
            cnd2 = 2 < self.Q_NPs
            cnd3 = 2 < self.Q_CrosLIn
            if cnd0 and cnd1 and cnd2 and cnd3:
                for inj in self.injected:
                    p = fgt_get_pressure(getattr(self, f'gate_{inj}'))
                    setattr(self, f'P_{inj}_m',p)                                      # define self.P_Oil_m, self.P_NPs_m etc..
                self.time_string = datetime.datetime.now().strftime("%H:%M:%S.%f")
                self.intensities = self.spec.intensities()
                self.concat_infos_and_intensities()
            else:
                self.plus_minus *= -1
                self.cycle +=  1
                print( f'cycle no = { self.cycle }' )
                print( f'plus_minus = { self.plus_minus } ' )
                break

    def close(self):
        '''
        Finishing the experiment
        '''
        print('closed')
        self.spec.close()
        [ fgt_set_pressure(getattr(self, f'gate_{inj}'), 0) for inj in self.injected ]

        # fgt_set_pressure(self.gate_Oil, 0)
        # for i in range(60):
        #     time.sleep(1)
        #     P_Oil = fgt_get_pressure(self.gate_Oil)
        #     [ fgt_set_pressure(getattr(self, f'gate_{inj}'), P_Oil) for inj in ['NPs', 'CrosLIn', 'Water', 'Titrant'] ]
        # [ fgt_set_pressure(getattr(self, f'gate_{inj}'), 0) for inj in self.injected ]


######------------------------------------------------------------------------#####
if __name__ == '__main__':
    Exp1 = EXPERIM()

    Exp1.stablize_to_balance_state(5)
    Exp1.print_info()
    Exp1.launch_exp()
    Exp1.close()
