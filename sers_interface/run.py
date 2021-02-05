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

try:
    from .MD093_1_1_modif import EXPERIM
    print('Imports are OK')
    Exp1 = EXPERIM()
except:
    print('not using MD093_1_1_modif !!!!!!!!!!')

@socketio.on('connect') #  , namespace='/test'
def test_connect():
    '''
    Websocket connection
    '''
    emit('response', {'data': 'Connected'})
    server.sleep(0.05)

def load_params_in_Exp(Exp, params):
    '''
    Exp : experiment object
    params : experiment parameters from the interface
    '''
    try:
        [ setattr(Exp,k,v) for k,v in params.items() ]
    except:
        pass

def send_estimated_time():
    '''
    '''
    Exp1.estimate_experiment_time()
    emit('estim_time_hours', Exp1.t_exp_estimated_hour)

@socketio.on('params') #
def retrieve_params(prms, debug=[]):
    '''
    Retrieve the parameters from the interface
    '''
    global params
    if 1 in debug: print(f'json file is { json.loads(prms) }')
    params = { p.split(':')[0]:p.split(':')[1] for p in json.loads(prms) }
    print( f"### params are { params } ")
    load_params_in_Exp(Exp1, params)
    send_estimated_time()

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

    emit('state', {'mess': 'beginning '})
    server.sleep(0.05)

    # Exp1.stablize_to_balance_state(5)
    # Exp1.print_info()
    # Exp1.launch_exp()
    # Exp1.close()

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

    address: {host}:{port}

    Addons :

    pip install flask-socketio
    pip install gevent (Windows)
    pip install eventlet

    Change each time the port !!!
    perhaps using random port..

    """ )

if __name__ == '__main__':
    init(app.config)                         # clean last processings and upload folders
    port = 5000; host = '127.0.0.1'
    print("host is " , host)
    launch_browser(port, host, platf)
    message_at_beginning(host,port)
    print(Style.RESET_ALL)
    socketio.run(app, port = port, host = host)
