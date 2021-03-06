'''
Utilities for the interface
'''
import os, subprocess, json
import shutil as sh
opd, opb, opj = os.path.dirname, os.path.basename, os.path.join
from sys import platform as _platform
import threading, webbrowser

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

def try_nb(s):
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s

def translate_params(p):
    '''
    '''
    print(f"##### p is {p}")
    if ':' in p:
        ps = p.split(':')
        if ',' in ps[1]:
            return { ps[0]:'[{}]'.format(ps[1]) }             # list case
        else:
            if '&' in ps[1]:
                if ps[0] == 'select_model':
                    part = ps[1].split('&')
                    dic_mod_with_event = { 'model': part[0], 'model_events': part[1] }
                    print(f"dic is {dic_mod_with_event} ")
                    return dic_mod_with_event
            else:
                return { ps[0]: try_nb(ps[1]) }                   # return key/value
    else:
        return { p:True }                                     # return a boolean

def clean_dir(dir):
    '''
    Clear folder dir
    '''
    try:
        for f in glob.glob(opj(dir, '*.*')):
            os.remove(f)
    except:
        print(f"can't clean {dir}")

def open_folder(path):
    '''
    Open folder
    '''
    if platf == 'win':
        os.startfile(path)
    elif platf == 'mac':
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

def rm_make_upload(config):
    '''
    '''
    upload = config['UPLOADED_PATH']
    try:
        sh.rmtree(upload)                        # Reinitializes the upload folder
    except:
        print(f"cannot find {upload}")
    os.mkdir(upload)

def init(config):
    '''
    Prepare interface.
    '''
    rm_make_upload(config)

def save_with_date(dest='previous_proc', debug=0):
    '''
    Save the processing with full structure in previous_proc
    Folders saved are Processings and Controls
    File saved is list_proc.json
    '''
    now = datetime.now()
    path_static = opj(os.getcwd(), 'static')
    dproc, dctrl = opj(path_static, 'processings'), opj(path_static, 'controls')
    dlist_proc = opj(path_static, 'list_proc.json')
    dest_path = opj(path_static, dest)
    try:
        os.mkdir(dest_path)                             # path for previous processings
        print("########## made new dest_path !!!! ")
    except:
        # print("#### In except loop !!!!")
        # print(dest_path)
        # print(os.path.exists(dest_path))
        # sh.rmtree(dest_path)
        # os.mkdir(dest_path)
        # # print("########## removed dest_path !!!! ")
        print("Possible issue with previous_proc")
    #path_static = opj(os.getcwd(), 'static')
    date = f"{now.year}-{now.month}-{now.day}-{now.hour}-{now.minute}"
    ppdate = opj(dest_path, date)
    try:
        sh.copytree(dproc, opj(ppdate,'processings'))
    except:
        print("yet existing folder")
    if debug>0: print("copied dproc")
    try:
        sh.copytree(dctrl, opj(ppdate,'controls'))
    except:
        print("yet existing folder")
    try:
        sh.copy(dlist_proc, ppdate)
    except:
        print("yet existing file")
    if debug>0: print("copied dlist_proc")
    sh.make_archive(ppdate, "zip", ppdate) # Zip the archive
    return ppdate +'.zip'

def find_chrome_path(platf):
    '''
    '''
    # MacOS
    if platf == 'mac':
        chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
    # Linux
    elif platf == 'lin':
        chrome_path = '/usr/bin/google-chrome %s'
    else:
        chrome_path = False
    return chrome_path

def launch_browser(port, host, platf):
    '''
    Launch Chrome navigator
    '''
    chrome_path = find_chrome_path(platf)
    url = f"http://{host}:{port}" #
    if platf != 'win':
        b = webbrowser.get(chrome_path)
        threading.Timer(1.25, lambda: b.open_new(url)).start()    # open a page in the browser.
    else:
        try:
            print('using first path')
            subprocess.Popen(f'"C:\Program Files\Google\Chrome\Application\chrome.exe" {url}')
        except:
            print('using second path')
            subprocess.Popen(f'"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" {url}')
