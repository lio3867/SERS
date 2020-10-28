# -*- coding: utf-8 -*-
"""
Created on Tue Feb  4 09:59:04 2020

@author: Ngoc Mai DUONG

ERRORS unsovled:
    1. spec.close()



28/05 (Mai)
    1. Adjust the delay time based on the bubles flow time
    2. Estimate and display the experiment time
    3. Save info of the delay spectra not in 'xx' but in number




"""
# spec.close()

import numpy as np
import pandas as pd
import time
import datetime
from statistics import mean

from Fluigent_ess.ESS import Switchboard
from Fluigent_FRP.FRP import Flowboard
from Fluigent.SDK import fgt_init, fgt_close
from Fluigent.SDK import fgt_set_pressure, fgt_get_pressure, fgt_get_pressureRange

import usb.core
import seabreeze.spectrometers as sb

# Clear all
from IPython import get_ipython
get_ipython().magic('reset -sf')

class SERS():
    '''
    '''
    def __init__(self):

        ## Set INPUT
        self.my_ESS_input = np.array([1,])
        self.my_pressure_input = { 'Pa_in':250,'Pb_in':260,'Pc_in':220,'Pd_in':150,'Pe_in':115 }
        self.t_integration_s = 15 #s
        self.t_step_min = 3 #min
        self.delta_P = 25
        self.replicates = 1  # 2 for 1 replicate; #3 for 2 replicates
        # delay_time = 30 #s
        self.step_index = 0
        self.plus_minus = 1
        ##
        self.n_from_inputs()           # Calculate n from inputs
        [setattr(self.args, k, v) for k,v in my_pressure_input.items()]
        self.print_params()

        # k = delay_time/t_integration_s

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
        print( f'replicates = {self.replicates}' )
        print( f'n = {self.n}' )

    def estimate_experiment_time(self):
        '''
        '''
        ## Estimate the experiment time
        self.n_SW = self.my_ESS_input.size
        self.t_exp_estimated = self.n_SW*self.t_step_min*10*self.replicates # in min
        self.t_exp_estimated_hour = round(self.t_exp_estimated/60, 2)
        print(f'Experiment estimated time = {self.t_exp_estimated_hour} (hours)')

    def Average(self,lst):
        return mean(lst)

    def stablize_to_balance_state(self,t=10):
        '''
        '''
        print('stablizing ...')
        fgt_set_pressure(0, self.Pa_in)
        fgt_set_pressure(1, self.Pb_in)
        fgt_set_pressure(4, self.Pc_in)
        fgt_set_pressure(5, self.Pd_in)
        fgt_set_pressure(6, self.Pe_in)
        time.sleep(t) #sec

    def close(self):
        '''
        '''
        print('closing (take about 1 min)')
        spec.close()
        fgt_set_pressure(4, 0)
        fgt_set_pressure(6, 0)
        for i in np.range(60):
            time.sleep(1)
            P_oil = fgt_get_pressure(4)
            P_sers= fgt_get_pressure(5)

            [ fgt_set_pressure(j, P_sers) if P_sers > P_oil else fgt_set_pressure(j, P_oil) for j in [0,1,5] ]
            [ fgt_set_pressure(j, 0)  for j in [0,1,5] ]

    def fill_infos(self):
        '''
        '''
        Q1 = flowboard.get_flowrate(available_FRP_ports[0])
        Q2 = flowboard.get_flowrate(available_FRP_ports[1])
        if Q1 > 2 and Q2 > 2 and Q1 < 54 and Q2 < 54:
            [ settatr(self,k,fgt_get_pressure(j)) for j,k in enumerate(self.list_Pout) ]
            time_string = datetime.datetime.now().strftime("%H:%M:%S.%f")
            intensities = spec.intensities()
            dfIntensity.loc[len(dfIntensity)] = intensities
            df_info.loc[len(df_info)] = [time_string, sw_step, port_I, port_II, step_index,
                                    self.Pa_temp, self.Pb_temp, self.Pc_in, self.Pd_in, self.Pe_in,
                                    round(self.Pa_out,2),round(self.Pb_out,2),
                                    round(self.Pc_out,2),round(self.Pd_out,2), round(self.Pe_out,2),
                                    round(Q1,2),round(Q2,2)]
            df_raw_data = pd.concat([df_info,dfIntensity], axis=1, sort=False)
        else:
            plus_minus *= -1
            count +=  1
            print('n= ', count)
            print('plus_minus= ', plus_minus)
            break

    def one_step(self):
        '''
        '''
        self.Pa_temp +=  self.plus_minus*self.delta_P
        self.Pb_temp -=  self.plus_minus*self.delta_P
        fgt_set_pressure(0, self.Pa_temp)
        fgt_set_pressure(1, self.Pb_temp)
        time.sleep(6)
        print(f'Applying P01245 =  {Pa_temp},{Pb_temp},{self.Pc_in},{self.Pd_in},{self.Pe_in} ')
        df_info =  pd.DataFrame(columns=df_info.columns)
        dfIntensity = pd.DataFrame(columns=dfIntensity.columns)
        step_index +=  1
        self.list_Pout = ['Pa_out', 'Pb_out', 'Pc_out', 'Pd_out', 'Pe_out']
        for i in range(int(self.n)):
            self.fill_infos()
        df_raw_data.to_csv('Data\d_{}.csv'.format(today), mode='a', header=False, index=True, sep=';')
        df_raw_data = pd.DataFrame(columns=df_raw_data.columns)


    def sweep_pressures(self):
        global plus_minus,step_index,df_info,dfIntensity
        count = -1 # first haft of the period
        Pa_temp = Pa_in - delta_P
        Pb_temp = Pb_in + delta_P
        for item in np.arange(50):
            Q1 = flowboard.get_flowrate(available_FRP_ports[0])
            Q2 = flowboard.get_flowrate(available_FRP_ports[1])
            # if Q1 > 1 and Q2 > 1 and Q1 < 54 and Q2 < 54 and count < replicates:
            if count < self.replicates:
                self.one_step()
            else:
                break

    def go_through_my_ESS_input(self):
        '''
        '''
        sw_step = 0
        for item in self.my_ESS_input:
            sw_step +=  1
            port_I = item
            port_II = item

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
            switchboard.set_position("A", port_I)
            switchboard.set_position("B", port_II)
            print("Switch on port A is at position {}".format(switchboard.get_position('A')))
            print("Switch on port B is at position {}".format(switchboard.get_position('B')))

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
            sweep_pressures()
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

        close()


## Set up ESS
ESS_serial_numbers = Switchboard.detect()
switchboard = Switchboard(ESS_serial_numbers[0])

## Set up FRP
FRP_serial_numbers = Flowboard.detect()
flowboard = Flowboard(FRP_serial_numbers[0])
flowboard.set_calibration(1, "Water")
flowboard.set_calibration(2, "Water")
available_FRP_ports = flowboard.get_available_ports()

## Initialize Spectrometer
usb.core.find()
devices = sb.list_devices()
spec = sb.Spectrometer(devices[0])
spec.integration_time_micros(t_integration)
wl = spec.wavelengths()
# wl_index = np.arange(len(wl))

## Create a Dataframe
t = np.array(['t(s)'])
switch = np.array(['SW_I', 'SW_II'])
SW_step = np.array(['SW_step'])
step = np.array(['step'])
pressure = np.array(['Pa', 'Pb', 'Pc', 'Pd','Pe',
                     'Pa_m', 'Pb_m', 'Pc_m', 'Pd_m', 'Pe_m'])
FRP = np.array(['Q1', 'Q2'])

dftime = pd.DataFrame(columns = t)
dfSW_step = pd.DataFrame(columns = SW_step)
dfSwitch = pd.DataFrame(columns = switch)
dfStep = pd.DataFrame(columns = step)
dfPressure = pd.DataFrame(columns = pressure)
dfFRP = pd.DataFrame(columns = FRP)
dfIntensity = pd.DataFrame(columns = wl)
df_info = pd.concat([dftime,dfSW_step,dfSwitch,dfStep,dfPressure,dfFRP], axis=1, sort=False)

my_file = pd.concat([df_info,dfIntensity], axis=1, sort=False)
today = datetime.datetime.today().strftime('%Y%m%d-%H%M')
my_file.to_csv('Data\d_{}.csv'.format(today), index=True, sep=';')

time_start_tuple = time.localtime() # get struct_time
time_start = time.strftime("%H:%M:%S", time_start_tuple)
print('Start experiment at ', time_start)
switchboard.set_position("A", my_ESS_input[0])
switchboard.set_position("B", my_ESS_input[0])
print("Switch on port A is at position {}".format(switchboard.get_position('A')))
print("Switch on port B is at position {}".format(switchboard.get_position('B')))


sr = SERS()
sr.stablize_to_balance_state(t=60)
sr.go_through_my_ESS_input()
