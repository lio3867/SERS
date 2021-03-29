#!/usr/bin/env python
# encoding: utf-8

"""

Simple interface

pip install flask-socketio
pip install eventlet
pip install eventlet==0.26 (for Windows)

python -m simple_interface.run

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
from simple_interface.modules.pages.define_all_pages import *
from simple_interface.modules.util_interf import *

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
app.config['UPLOADED_PATH'] = opj(os.getcwd(),'simple_interface','upload')              # upload directory from the Dropzone
print("######### app.config['UPLOADED_PATH'] is {0} !!!".format(app.config['UPLOADED_PATH']))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'F34TF$($e34D';
socketio = SocketIO(app)

@socketio.on('connect') #  , namespace='/test'
def test_connect():
    '''
    Websocket connection
    '''
    emit('response', {'data': 'Connected'})
    server.sleep(0.05)

@app.route('/', methods=['GET', 'POST'])
def main_page(debug=1):
    '''
    '''
    dmp = define_main_page()
    return render_template('index_folder.html', **dmp.__dict__)

@socketio.on('mess') #  ,
def receiving_mess():
    '''
    Receiving a message
    '''
    print( f"mess is { mess }" )
    emit('refresh', "bingo")

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

  # randint is inclusive at both ends

    port = randint(5000, 5999); host = '127.0.0.1'
    print("host is " , host)
    launch_browser(port, host, platf)
    message_at_beginning(host,port)
    print(Style.RESET_ALL)
    socketio.run(app, port = port, host = host)
