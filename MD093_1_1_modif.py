# -*- coding: utf-8 -*-
"""
Created on Tue Feb  4 09:59:04 2020

@author: Ngoc Mai DUONG

ERRORS unsovled:
    1. spec.close()



28/05/2020 (Mai)
    1. Adjust the delay time based on the bubbles flow time
    2. Estimate and display the experiment time
    3. Save info of the delay spectra not in 'xx' but in number




"""
# spec.close()

import os
from pathlib import Path
import numpy as np
import pandas as pd
import time
import datetime
from statistics import mean
from matplotlib import pyplot as plt
##
from flask_socketio import emit

from Fluigent_ess.ESS import Switchboard
from Fluigent_FRP.FRP import Flowboard
from Fluigent.SDK import fgt_init, fgt_close
from Fluigent.SDK import fgt_set_pressure, fgt_get_pressure, fgt_get_pressureRange

import usb.core
import seabreeze.spectrometers as sb


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

class SERS():
    '''
    '''
    def __init__(self):

        ## Set INPUT
        self.my_ESS_input = np.array([1,])
        self.my_pressure_input = { 'P_oil_in':380,'P_NPs_in':280,'P_CroLIn_in':220,'P_Water_in':330,'P_Titrant_in':330 }
        self.lval = [0, 1, 2, 4, 5]
        self.t_integration_s = 5   #s
        self.t_step_min = 3         #min
        self.delta_P = 25
        self.cycles = 1      
        # delay_time = 30 #s
        self.step_index = 0
        self.plus_minus = 1
        ##
        self.prepare_folders()
        self.n_from_inputs()           # Calculate n from inputs
        [setattr(self, k, v) for k,v in self.my_pressure_input.items()]
        self.print_params()

        # k = delay_time/t_integration_s

        try:
            self.set_ESS()
            self.set_FRP()
            self.init_spectro()
            self.create_dataframe()
            self.begin_exp()
        except:
            print("Some devices not detected perhaps")

    def prepare_folders(self):
        '''
        '''
        if not os.path.exists('Data'):
            os.mkdir('Data')

    def set_ESS(self):
        '''
        Set up ESS
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
        # wl_index = np.arange(len(wl))

# class Data_handling():
    def __init__(self):
        pass

        
    def prepare_df_info(self):
        '''
        '''
        t = ['t(s)']
        SW_step = ['SW_step']
        switch = ['SW_I', 'SW_II']
        step = ['step']
        pressure = ['P_oil','P_NPs','P_CrosLIn','P_Water','P_Titrant',
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
        
    def plot_intensities(self):
        '''
        '''
        plt.plot(self.intensities)
        addr_img = Path('sers_interface') / 'static' / 'curr_pic' / 'intensities.png'
        plt.savefig( str(addr_img) )
        
    def concat_infos_and_intensities(self):
        '''
        '''
        self.dfIntensity.loc[len(self.dfIntensity)] = self.intensities
        self.plot_intensities()
        self.df_info.loc[len(self.df_info)] = [self.time_string, self.sw_step, self.port_I, self.port_II, self.step_index,
                                self.P_Oil_in, self.P_NPs_in, self.P_CrosLIn_in, self.P_Water_temp, self.P_Titrant_temp,
                                round(self.P_Oil_m,2),round(self.P_NPs_m,2),round(self.P_CrosLIn_out,2),
                                round(self.P_Water_m,2), round(self.P_Titrant_m,2),
                                round(self.Q_NPs,2),round(self.Q_CrosLIn,2),round(self.Q_Water,2),round(self.Q_Titrant,2)]
        self.df_raw_data = pd.concat([self.df_info,self.dfIntensity], axis=1, sort=False)
    
    def save_to_csv(self):
        '''
        '''
        self.df_raw_data.to_csv(f'Data\d_{self.today}.csv', mode='a', header=False, index=True, sep=';')
        self.df_raw_data = pd.DataFrame(columns=self.df_raw_data.columns)
######------------------------------------------------------------------------#####


    def begin_exp(self):
        '''
        '''
        time_start_tuple = time.localtime() # get struct_time
        time_start = time.strftime("%H:%M:%S", time_start_tuple)
        print('Start experiment at ', time_start)
        self.switchboard.set_position("A", self.my_ESS_input[0])
        self.switchboard.set_position("B", self.my_ESS_input[0])
        print( f"Switch on port A is at position {self.switchboard.get_position('A')}" )
        print( f"Switch on port B is at position {self.switchboard.get_position('B')}" )

    def n_from_inputs(self):
        '''
        '''
        self.t_each_step = self.t_step_min*60 #s
        self.t_integration = self.t_integration_s*(1e6) #1e6 = 1s
        self.n = self.t_each_step/(self.t_integration/1e6)

    def print_params(self):
        '''
        '''
        print( f'my_ESS_input =  {self.my_ESS_input}')
        print( f'my_pressure_input = {self.my_pressure_input}')
        print( f't_integration_s = {self.t_integration_s}' )
        print( f'delta_P = {self.delta_P}' )
        print( f'cycles = {self.cycles}' )
        print( f'n = {self.n}' )

    def estimate_experiment_time(self):
        '''
        '''
        ## Estimate the experiment time
        self.n_SW = self.my_ESS_input.size
        self.t_exp_estimated = self.n_SW*self.t_step_min*10*self.cycles # in min
        self.t_exp_estimated_hour = round(self.t_exp_estimated/60, 2)
        print(f'Experiment estimated time = {self.t_exp_estimated_hour} (hours)')

    def Average(self,lst):
        return mean(lst)

    def stablize_to_balance_state(self,t=10):
        '''
        P_in values
        '''
        print('stablizing ...')
        # lval = [0, 1, 2, 4, 5]
        [ fgt_set_pressure(self.lval[j], getattr(self, k)) for j,(k,v) in enumerate(self.my_pressure_input.items()) ]
        time.sleep(t) #sec

    def close(self):
        '''
        '''
        # print('closing (take about 1 min)')
        self.spec.close()
        fgt_set_pressure(0, 0)
        fgt_set_pressure(1, 0)
        fgt_set_pressure(2, 0)
        fgt_set_pressure(4, 0)
        fgt_set_pressure(5, 0)
        # for i in np.range(60):
        #     time.sleep(1)
        #     P_oil = fgt_get_pressure(4)
        #     P_sers= fgt_get_pressure(5)
        #     [ fgt_set_pressure(j, P_sers) if P_sers > P_oil else fgt_set_pressure(j, P_oil) for j in [0,1,5] ]
        #     [ fgt_set_pressure(j, 0)  for j in [0,1,5] ]

    def plot_intensities(self):
        '''
        '''
        plt.plot(self.intensities)
        addr_img = Path('sers_interface') / 'static' / 'curr_pic' / 'intensities.png'
        plt.savefig( str(addr_img) )
        emit( 'addr_img', { 'mess': str(addr_img) } )
        server.sleep(0.5)

    

    def register_results(self):
        '''
        '''
        self.list_Pout = ['Pa_out', 'Pb_out', 'Pc_out', 'Pd_out', 'Pe_out']
        for i in range(int(self.n)):
            self.Q1 = self.flowboard.get_flowrate(self.available_FRP_ports[0])
            self.Q2 = self.flowboard.get_flowrate(self.available_FRP_ports[1])
            if self.Q1 > 2 and self.Q2 > 2 and self.Q1 < 54 and self.Q2 < 54:
                [ settatr(self,k,fgt_get_pressure(j)) for j,k in enumerate(self.list_Pout) ]
                self.time_string = datetime.datetime.now().strftime("%H:%M:%S.%f")
                self.intensities = self.spec.intensities()
                self.concat_infos_and_intensities()
            else:
                self.plus_minus *= -1
                self.count +=  1
                print( f'n = {self.count}' )
                print( f'plus_minus = {self.plus_minus} ' )
                break

    def save_to_csv(self):
        '''
        '''
        self.df_raw_data.to_csv(f'Data\d_{self.today}.csv', mode='a', header=False, index=True, sep=';')
        self.df_raw_data = pd.DataFrame(columns=self.df_raw_data.columns)


######------------------------------------------------------------------------#####
    def one_step(self):
    '''
    Run step by step until , then register results
    '''
    self.list_P_m = ['P_Oil_m', 'P_NPs_m', 'P_CrosLIn_m', 'P_Water_m', 'P_Titrant_m']
    for i in range(int(self.n)):
        self.Q_Water = self.flowboard.get_flowrate(self.available_FRP_ports[2])
        self.Q_Titrant = self.flowboard.get_flowrate(self.available_FRP_ports[3])
        if self.Q_Water > 2 and self.Q_Titrant > 2 and self.Q_Water < 54 and self.Q_Titrant < 54:
            [ settatr(self,k,fgt_get_pressure(j)) for j,k in enumerate(self.list_P_m) ]
            self.time_string = datetime.datetime.now().strftime("%H:%M:%S.%f")
            self.intensities = self.spec.intensities()
            self.concat_infos_and_intensities()
        else:
            self.plus_minus *= -1
            self.cycle +=  1
            print( f'n = {self.cycle}' )
            print( f'plus_minus = {self.plus_minus} ' )
            break
    
    def change_pressures(self):
        '''
        '''
        self.P_Water_temp +=  self.plus_minus*self.delta_P
        self.P_Titrant_temp -=  self.plus_minus*self.delta_P
        fgt_set_pressure(0, self.P_Water_temp)
        fgt_set_pressure(1, self.P_Titrant_temp)

    def one_cycle(self):
        '''
        '''
        # self.change_pressures()
        self.P_Water_temp +=  self.plus_minus*self.delta_P
        self.P_Titrant_temp -=  self.plus_minus*self.delta_P
        fgt_set_pressure(0, self.P_Water_temp)
        fgt_set_pressure(1, self.P_Titrant_temp)
        time.sleep(6)         
        print(f'Applying P_Oil_NPs_CrosLIn =  {self.P_Oil_in},{self.P_NPs_in},{self.P_CrosLIn_in}')
        print(f'Applying P_Water_Titrant =  {self.P_Water_temp},{self.P_Titrant_temp}')
        self.df_info =  pd.DataFrame(columns=self.df_info.columns)
        self.dfIntensity = pd.DataFrame(columns=self.dfIntensity.columns)
        self.step_index +=  1
        
        self.one_step()
        self.save_to_csv()

    def sweep_pressures(self):
        '''
        '''
        self.period = -1 # first haft of the period
        self.P_Water_temp = self.P_Water_in - self.delta_P
        self.P_Titrant_temp = self.P_Titrant_in + self.delta_P
        for item in np.arange(50):
            self.Q_Water = self.flowboard.get_flowrate(self.available_FRP_ports[2])
            self.Q_Titrant = self.flowboard.get_flowrate(self.available_FRP_ports[3])
            # if self.Q1 > 1 and self.Q2 > 1 and self.Q1 < 54 and self.Q2 < 54 and cycle < cycles:
            if self.cycle < self.cycles:
                self.one_cycle()
            else:
                break

    def go_through_my_ESS_input(self):
        '''
        '''
        self.sw_step = 0
        for item in self.my_ESS_input:
            self.sw_step +=  1
            self.port_I = item
            self.port_II = item
            # print('Start pumping air')
            # switchboard.set_position("A", 10) # for pumping air
            # switchboard.set_position("B", 10) # for pumping air
            # fgt_set_pressure(1, 500) # for pumping air
            # time.sleep(2)
            # for i in np.arange(300):
            #     time.sleep(0.5)
            #     if flowboard.get_flowrate(available_FRP_ports[0]) < 1:
            #         print('air starting in flow unit')
            #         break
            # t0 = time.time()
            self.switchboard.set_position("A", self.port_I)
            self.switchboard.set_position("B", self.port_II)
            print( f"Switch on port A is at position {self.switchboard.get_position('A')}" )
            print( f"Switch on port B is at position {self.switchboard.get_position('B')}" )
            # for i in np.arange(300):
            #     flow_list = []
            #     for j in np.arange(1,11):
            #         time.sleep(0.5)
            #         flow_list.append(flowboard.get_flowrate(available_FRP_ports[0]))
            #     if Average(flow_list) > 50:  #(= after x seconds, there is no air flow)
            #         break
            # print('Stop pumping air')
            # stablize_to_balance_state(t=15)
            # t1 = time.time()
            self.sweep_pressures()
            # stablize_to_balance_state(t=1)
            # print('Recording spectra during delay time')
            # df_info_delay =  pd.DataFrame(columns=df_info.columns)
            # dfIntensity_delay = pd.DataFrame(columns=dfIntensity.columns)

            # t_delay = t1 - t0 + 30
            # print('t_delay = ', t_delay)
            # k = 60/t_integration_s

            # for i in range(int(k)):
            #     time_string = datetime.datetime.now().strftime("%H:%M:%S.%f")
            #     intensities = spec.intensities()
            #     P1_delay = fgt_get_pressure(0)
            #     P2_delay = fgt_get_pressure(1)
            #     P3_delay = fgt_get_pressure(2)
            #     P4_delay = fgt_get_pressure(3)
            #     QA_delay = flowboard.get_flowrate(available_FRP_ports[0])
            #     QB_delay = flowboard.get_flowrate(available_FRP_ports[1])
            #     dfIntensity_delay.loc[len(dfIntensity_delay)] = intensities
            #     step_index = step_index+1
            #     df_info_delay.loc[len(df_info_delay)] = [time_string, sw_step, port_I, port_II, step_index,
            #                                                       P1_in, P2_in, P3_in, P4_in,
            #                   round(P1_delay,2), round(P2_delay,2), round(P3_delay,2), round(P4_delay,2),
            #                                                       round(QA_delay,2),round(QB_delay,2)]
            #     df_delay = pd.concat([df_info_delay,dfIntensity_delay], axis=1, sort=False)
            # df_delay.to_csv('Data\d_{}.csv'.format(today), mode='a', header=False, index=True, sep=';')
            # df_delay = pd.DataFrame(columns=df_delay.columns)
######------------------------------------------------------------------------#####
self.close()
