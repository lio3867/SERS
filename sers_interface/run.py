#!/usr/bin/env python
# encoding: utf-8

"""

Image Analysis program

pip install flask-socketio
pip install eventlet
pip install eventlet==0.26 (for Windows)

python -m sers_interface.run

"""
from __future__ import print_function, division, absolute_import

import errno, os, sys, csv, json, glob, logging
opd, opb, opj = os.path.dirname, os.path.basename, os.path.join
import shutil as sh
from colorama import Fore, Back, Style      # Color in the Terminal
import time
from datetime import datetime
import subprocess
import multiprocessing
#import asyncio
##
import threading, webbrowser
from sys import platform as _platform
#from util.mail import send_email
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

from MD093_1_1_modif import SERS

print('Imports are OK')

@socketio.on('connect') #  , namespace='/test'
def test_connect():
    '''
    Websocket connection
    '''
    emit('response', {'data': 'Connected'})
    server.sleep(0.05)
    infos_hard_soft()                                             # infos about hardware ans software

@socketio.on('operation') #
def set_curr_op(operation):
    '''
    Select the operation
    '''
    global op
    op = operation
    print(f'current operation is {op}')

@socketio.on('params') #
def retrieve_params(prms):
    '''
    Retrieve the parameters from the interface
    '''
    global params
    params = json.loads(prms)
    print( f"### params are {params} ")

def select_dic_proc(params):
    '''
    Begin to build dic_proc
    '''
    dic_proc = {}
    dic_op =  {'nbcells':'ep5_v3', 'segm':'ep5_v3', 'test':'ep5_v3'}     # choice and associated model
    dic_proc.update({'model':dic_op[op]})
    for p in params:
        elem = translate_params(p)    # interpret the params inputs for detect_cells.py
        print(f'elem is {elem}')
        try:
            dic_proc.update(elem)
        except:
            print(f'not working for elem = {elem}')
    return dic_proc

def make_dic_proc(i,addr):
    '''
    Build the dictionary used for the processing
    '''
    print("current op in make_on_proc is ", op)
    dic_base = select_dic_proc(params)
    print("dic_base", dic_base)
    dic_proc = { 'film': addr }
    dic_proc.update(dic_base)
    try:
        print('save_in',save_in)
    except:
        save_in = '.'
    dic_proc.update({'save_in':save_in}) # reuse previous directory
    print("dic_proc is ", dic_proc)
    return dic_proc

def make_one_proc(i,addr):
    '''
    Process one dataset
    '''
    global save_in
    dic_proc = make_dic_proc(i,addr)
    t0 = time.time()
    fc = FIND_CELLS(dic_proc)
    save_in = fc.dir_result
    t1 = time.time()
    tproc = round((t1-t0)/60,2)
    print('time elapsed for processing is {0} min '.format(tproc))
    emit('time_one_proc', { 'mess': str(tproc) })
    server.sleep(0.05)

def currproc_done(addr):
    '''
    Message indicating the processing is finished
    '''
    emit('proc_done', {'mess': opb(addr)})            # sending address of the completed processing
    server.sleep(0.05)

def done_and_currproc(i, lengthdata, addr):
    '''
    Ratio of processings done
    '''
    emit('ratio', {'mess': 'processing : ' + str(i+1) + '/' + lengthdata  })
    server.sleep(0.05)
    emit('curr_proc', {'mess': addr})            # sending address of current processed file
    server.sleep(0.05)

def process(dict_data, debug=1):
    '''
    Apply the processing on the datasets registered in the list dict_data.
    dict_data: list of files to be processed
    '''
    if debug>1: print("######## dict_data is ", dict_data)
    tt0 = time.time()
    list_processed = []
    lengthdata = str(len(dict_data))
    for i,addr in enumerate(dict_data):
        print("addr is ", addr)
        if debug>0: print("######## list_processed is ", list_processed)
        if addr not in list_processed  :                # if not yet processed
            done_and_currproc(i, lengthdata, addr)
            make_one_proc(i,addr)                                               # performing a processing
            currproc_done(addr)
            list_processed.append(addr)                                         # list of the processed files
            count = int(len(list_processed)/len(dict_data)*100)                 # percent of processings done
            if debug > 0: print(f"#### count {count}% ")
    tt1 = time.time()
    print('total time elapsed is {0} min '.format((tt1-tt0)/60))                # time elapsed for the whole processing..
    #path_save_with_date = save_with_date()                                     # save the processing in previous_proc
    #return path_save_with_date

def save_file(f, full_path, debug=0):
    '''
    Save full f in full_path
    '''
    try:
        f.save(full_path)
    except IOError as e:
        # ENOENT(2): file does not exist, raised also on missing parent dir
        if e.errno != errno.ENOENT:
            raise
        # try creating parent directories
        os.makedirs(os.path.dirname(full_path))    # Makes folder
        f.save(full_path)                          # Save locally the file in the folder upload
        if debug>0: print(f"###################### Saved file {full_path} !!!! ")

def infos_hard_soft():
    '''
    Send to the client informations about computing ressource..
    '''
    try:
        hard_soft_infos = get_computing_infos()
        emit('hard_soft_infos', { 'mess': json.dumps(hard_soft_infos) })
        server.sleep(0.05)
    except:
        print('working out of context')

@app.route('/', methods=['GET', 'POST'])
def main_page(debug=1):
    '''
    '''
    dmp = define_main_page()

    return render_template('index_folder.html', **dmp.__dict__)

def full_addr(list_files):
    '''

    '''
    lf0 = [f.replace('box_','') for f in list_files]
    print("lf0 is ", lf0)
    lf1 = [os.path.join(app.config['UPLOADED_PATH'],f) for f in lf0]
    return lf1

@socketio.on('launch_proc') #
def proc(list_files, debug=1):
    '''
    Process the data
    '''
    print("##### list_files ", list_files)
    dict_data = full_addr(json.loads(list_files))
    print("### dict_data is ", dict_data)
    ### Processing
    emit('state', {'mess': 'beginning all the processings'})
    server.sleep(0.05)
    process(dict_data)                                  # Processing all the datasets
    server.sleep(0.05)
    emit('end_proc','finished')
    emit('state', {'mess': 'end of the processings'})
    time.sleep(0.1)
    emit('state', {'mess': ''})
    print("######   emitted finished !!!")

@socketio.on('save_addr') #
def proc(save_addr, debug=1):
    '''
    save address
    '''
    global save_in
    print(f"address where to save the processings {save_addr} ")
    save_in = save_addr

@app.route('/erase_processed', methods = ['GET', 'POST'])
def erase_processed(debug=0):
    '''
    Erase selected datasets (those checked on the "processed" page)
    '''
    define_processed()
    selected_checks = json.loads(request.form.get('erase_data'))
    print(selected_checks)
    for folder in selected_checks:
        pathf = opj(os.getcwd(), 'static', 'previous_proc', folder.strip())  # path to folders to be deleted
        sh.rmtree(pathf)                                                     # delete the folder
        print(f"removed {folder} ")

    return render_template('processed.html', **define_processed().__dict__) #

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
    Launching the Image Analysis program

    address: {host}:{port}

    Drop the dataset in the drop zone,
    select the operation
    and click on "processings"

    Addons :

    pip install flask-socketio
    pip install gevent (Windows)
    pip install eventlet

    """ )

if __name__ == '__main__':
    init(app.config)                         # clean last processings and upload folders
    port = 5000; host = '0.0.0.0'
    print("host is " , host)
    launch_browser(port, host, platf)
    message_at_beginning(host,port)
    print(Style.RESET_ALL)
    socketio.run(app, port = port, host = host)
