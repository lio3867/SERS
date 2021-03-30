#!/usr/bin/env python
# encoding: utf-8

"""

SERS program

pip install flask-socketio
pip install eventlet
pip install eventlet==0.26 (for Windows)

python -m sers_interface.run

"""
from __future__ import print_function, division, absolute_import

import errno, os, sys, csv, json, glob, logging
from random import randint
op = os.path
opd, opb, opj = op.dirname, op.basename, op.join
import shutil as sh
from colorama import Fore, Back, Style      # Color in the Terminal
import time
from datetime import datetime
import subprocess
import multiprocessing

##
import threading, webbrowser
from sys import platform as _platform

##
from matplotlib import pyplot as plt
import numpy as np
##
from flask import Flask, render_template, request, redirect    # Flask imports
from flask_socketio import SocketIO, emit
from sers_interface.modules.pages.define_all_pages import *
from sers_interface.modules.util_interf import *

platf  = find_platform()

if platf =='win':
    import gevent as server
    from gevent import monkey
    monkey.patch_all()
else:
    import eventlet as server
    server.monkey_patch()

Debug = True            # Debug Flask

app = Flask(__name__)
app.config['UPLOADED_PATH'] = opj(os.getcwd(),'sers_interface','upload')              # upload directory from the Dropzone
print("######### app.config['UPLOADED_PATH'] is {0} !!!".format(app.config['UPLOADED_PATH']))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'F34TF$($e34D';
socketio = SocketIO(app)

from .MD093_1_1_modif import EXPERIM
print('Imports are OK')

pinput = [ 'P_Oil_in','P_NPs_in','P_CrosLIn_in','P_Water_in','P_Titrant_in' ]

@socketio.on('connect') #  , namespace='/test'
def test_connect():
    '''
    Websocket connection
    '''
    emit('response', {'data': 'Connected'})
    server.sleep(0.05)

def print_loaded_params(Exp):
    '''
    '''
    print( f'P1 = { Exp.P1 }' )
    print( f't_step_min = { Exp.t_step_min }' )
    print( f'my_ESS_input = { Exp.my_ESS_input }' )
    print( f't_integration_s = { Exp.t_integration_s }' )

def load_params_in_Exp(Exp, params):
    '''
    Exp : experiment object
    params : experiment parameters from the interface
    '''
    for k,v in params.items():
        if v.isdigit():
            setattr(Exp,k,int(v))      # integer
        elif ',' not in v:
            setattr(Exp,k,v)           # string and not list
        else:
            Exp.my_ESS_input = np.array(list(map(int,params['sb_pos'].split(','))))  # list
    for i in range(len(pinput)):
        setattr(Exp, pinput[i], getattr(Exp,'P' + str(i+1))) # P_oil_in = P1 etc....
    print_loaded_params(Exp)

def send_estimated_time():
    '''
    '''
    Exp1.estimate_experiment_time()
    emit('estim_time_hours', round( Exp1.t_exp_estimated_hour,2 ) )

@socketio.on('params') #
def retrieve_params(prms, debug=[]):
    '''
    Retrieve the parameters from the interface
    '''
    global params, Exp1
    Exp1 = EXPERIM()
    if 1 in debug: print(f'json file is { json.loads(prms) }')
    params = { p.split(':')[0]:p.split(':')[1] for p in json.loads(prms) }
    print( f"### params are { params } ")
    load_params_in_Exp(Exp1, params)
    send_estimated_time()

@socketio.on('rangexy') #
def rangexy(rangexy, debug=[]):
    '''
    '''
    global Exp1
    rangex = rangexy.split('_')[0]
    rangey = rangexy.split('_')[1]
    print(f'rangexy { rangexy }')
    x = rangex.split(',')
    y = rangey.split(',')
    Exp1.rangex = [x[0],x[1]]
    Exp1.rangey = [y[0],y[1]]

@app.route('/', methods=['GET', 'POST'])
def main_page(debug=1):
    '''
    '''
    dmp = define_main_page()
    return render_template('index_folder.html', **dmp.__dict__)

@socketio.on('launch_proc') #
def proc(msg, debug=1):
    '''
    Process
    '''
    global Exp1

    #emit('state', {'mess': 'beginning '})
    sleep(1)
    emit('check_emit', "received the message")
    server.sleep(0.05)

    Exp1.stablize_to_balance_state(t=5)
    Exp1.print_info()
    Exp1.launch_exp()
    Exp1.close()

    server.sleep(0.05)
    emit('end_proc','finished')

def shutdown_server():
    '''
    Quit the application
    called by method shutdown() (hereunder)
    '''
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown')
def shutdown():
    '''
    Shutting down the server.
    '''
    shutdown_server()

    return 'Server shutting down...'

def message_at_beginning(host,port):
    '''
    '''
    print( Fore.YELLOW + f"""
    ***************************************************************
    Launching the SERS program

    address: { host }:{ port }

    Addons :

    pip install flask-socketio
    pip install gevent (Windows)
    pip install eventlet

    Change each time the port !!!
    perhaps using random port..

    """ )

if __name__ == '__main__':
    init(app.config)                         # clean last processings and upload folders


    port = randint(5000, 5999); host = '127.0.0.1'
    print("host is " , host)
    launch_browser(port, host, platf)
    message_at_beginning(host,port)
    print(Style.RESET_ALL)
    socketio.run(app, port = port, host = host)
