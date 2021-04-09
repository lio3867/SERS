# -*- coding: utf-8 -*-
"""


"""

import os
from pathlib import Path
import numpy as np
import time
from time import sleep
import datetime
from matplotlib import pyplot as plt
##
from flask_socketio import emit

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

class EXPERIM():
    '''
    '''
    def __init__(self, N=100):
        '''
        '''
        self.N = N

    def make_plots(self):
        '''

        '''

        for i in range(self.N):
            x = 10*np.arange(self.N)/self.N+i*0.33
            y = np.cos(x)
            plt.figure()
            plt.plot(x,y, 'g--')
            addr_img = Path('simple_interface') / 'static' / 'curr_pic' / 'intensities.png'
            plt.savefig(addr_img)
            plt.close()
            time.sleep(0.1)         #sec
            emit('new_spec', "")
            print(f'making curve {i}')
            emit('curr_val', str(i))


######------------------------------------------------------------------------#####
if __name__ == '__main__':
    pass
