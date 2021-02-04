import threading
import sys
import os
import time
import re
import json
import logging
import http
import urllib
from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter import filedialog
from pytube import YouTube

Url = ''            #youtube url used globally
audio_itag = None   #this is used to download audio. gui does not need to process this. used globally
mes_line = 42       #controls the message coordination on the canvas, used globally
thread_ind = True   #controls whether to end the thread.
streamName = ''     #used to get the original stream name for autofill
Filepath = os.path.dirname(os.path.realpath(__file__))  #used globally where the downloaded files are saved
#none tkinter func
def check():
    global mes_line
    while thread_ind:
        if mes_line>200:
            mes_canvas.yview_moveto(str((mes_line-200)/2000))
        time.sleep(2)
#none tkinter func
def prep_mes(message,n=1):
    global mes_line
    mes_line += int(21*(n-1)/2)            #used when the mes is more than one line 
    mes = ttk.Label(mes_canvas,text=message)
    mes_canvas.create_window(140,mes_line,window=mes)
    mes_line += 21*n
    mainframe.update()

def check_entry(n,stat):
    '''for url entry validatecommand'''
    global Url
    valid = re.search('youtube.com',n)
    if stat == 'key':
        if n == '':
            ok_button.state(['disabled'])
        elif valid:
            error_msg['text'] = ''
            ok_button.state(['!disabled'])
        else:
            ok_button.state(['!disabled'])
    elif stat == 'focusout':
        if not valid:
            error_msg['text'] = content
            Url = ''
        else:
            error_msg['text'] = ''
            Url = n
    return True

def auto_fill():
    '''command for rename button'''
    global streamName
    rename_entry.delete(0,END)
    rename_entry.insert(0,streamName)

def file_dialog():
    global Filepath
    filepath = filedialog.askdirectory()
    if filepath != '':
        Filepath = filepath
    path_text.configure(state=NORMAL)
    path_text.delete('1.0',END)
    path_text.insert('1.0',Filepath)
    path_text.configure(state=DISABLED)

def connecting(url):
    iamtrying = True
    message = 'Connecting to website... Please wait'
    prep_mes(message)
    while iamtrying:
        try:
            video = YouTube(url)
        except json.decoder.JSONDecodeError as e:
            logging.exception(e)
            message = 'Trying to connect to website... Please wait'
            prep_mes(message)
        except http.client.RemoteDisconnected as e:
            logging.exception(e)
            message = '对方拒绝了你的访问请求，请稍后重试。'
            prep_mes(message)
        except urllib.error.URLError as e:
            if str(e.reason) == '[Errno 2] No such file or directory':
                message = str(e.reason)+'\nLooking for file...'
                message += '\nCould choose to end program and try later'
                prep_mes(message,3)
            else:
                logging.exception(e)
                message = 'urllib.error.URLError. Please end program'
                prep_mes(message)
        except BaseException as e:
            logging.exception(e)
            message = 'Something went wrong. Please end program'
            prep_mes(message)
        else:
            return video
def collect_streams():
    global Url,audio_itag,video,streamName
    if Url != '':
        nostream = True
        while nostream:
            video = connecting(Url)
            #search for available streams
            res_list_1 = {}
            res_list_2 = {}
            sub_list = {}
            nostream = False
            while not streamName:     #get file name so that can autofill
                stream = video.streams.otf()[0]
                streamName = stream.title
            for stream in video.streams.otf():
                print(stream)
                temp = str(stream)
                #find video&audio combined
                if 'mp4' in temp and 'video' in temp and 'True' in temp:
                    m = temp.find('res')
                    n = temp.find('fps')
                    res = temp[m+5:n-2]
                    res_list_1[res] = False
                #find seperated video
                elif 'mp4' in temp and 'video' in temp:
                    m = temp.find('res')
                    n = temp.find('fps')
                    res = temp[m+5:n-2]
                    m = temp.find('itag')
                    n = temp.find('mime')
                    itag = int(temp[m+6:n-2])
                    print(itag)
                    if res not in res_list_1.keys() and res not in res_list_2.keys():
                        if res != 'None':
                            res_list_2[res] = [False,itag]
                #find audio(kinda random audio)
                elif 'audio' in temp and 'mp4' in temp:
                    m = temp.find('itag')
                    n = temp.find('mime')
                    audio_itag = int(temp[m+6:n-2])
            for sub in video.captions.all():
                m,n = re.findall(r'"\w*[ \w()-.]*"',str(sub))
                m = m[1:-1]
                n = n[1:-1]
                sub_list[m] = [False,n]

            if res_list_2 == {}:
                nostream = True
                message = 'Looking for streams\nCould choose to end program and try later'
                prep_mes(message,2)
        return res_list_1,res_list_2,sub_list
def display_streams():
    '''okne button command. connect to internet. collect video streams.
    populate listbox. disable some widget. obtain cutomized filename if any.
    show blue label.'''
    global vachoices,vchoices,subchoices
    if error_msg['text'] == '':
        vachoices,vchoices,subchoices = collect_streams()
        spacing = 4
        for i in vachoices.keys():
            vachoices[i] = BooleanVar()
            a = ttk.Checkbutton(vacanvas,text=i,variable=vachoices[i])
            vacanvas.create_window(4,spacing,anchor='nw',window=a)
            spacing += 22
        spacing = 4
        for i in vchoices.keys():
            vchoices[i][0] = BooleanVar()
            a = ttk.Checkbutton(vcanvas,text=i,variable=vchoices[i][0])
            vcanvas.create_window(4,spacing,anchor='nw',window=a)
            spacing += 22
        spacing = 4
        for i in subchoices.keys():
            subchoices[i][0] = BooleanVar()
            a = ttk.Checkbutton(subcanvas,text=i,variable=subchoices[i][0])
            subcanvas.create_window(4,spacing,anchor='nw',window=a)
            spacing += 22
        message = 'Please select file(s)'
        prep_mes(message)
        re_button['state'] = '!disabled'
        rename_entry['state'] = '!disabled'
        s_msg.set(message)
        s_label['background'] = 'blue'
        d_button['state'] = 'normal'
        if len(subchoices) > 9:
            sub_bar.grid()

def download():
    '''command for d_button'''
    global audio_itag,Filepath,streamName
    fileName = rename_entry.get()
    if fileName == '':
        fileName = streamName
    for res in vachoices.keys():
        if vachoices[res].get():
            dl = True
            stream = video.streams.get_by_resolution(res)
            fileName += res
            message = 'Downloading %s...' % res
            prep_mes(message)
            while dl:
                try:
                    stream.download(output_path=Filepath,filename=fileName)
                except FileNotFoundError as e:
                    logging.exception(e)
                    message = 'Trying to download...'
                    prep_mes(message)
                except urllib.error.URLError as e:
                    logging.exception(e)
                    message = 'Trying to download...'
                    prep_mes(message)
                else:
                    dl = False
            message = 'Done'
            prep_mes(message)
    for res in vchoices.keys():
        if vchoices[res][0].get():
            dl = True
            stream = video.streams.get_by_itag(vchoices[res][1])
            fileName += res
            message = 'Downloading video %s...' % res
            prep_mes(message)
            while dl:   #video
                try:
                    stream.download(output_path=Filepath,filename=fileName)
                except FileNotFoundError as e:
                    logging.exception(e)
                    message = 'Trying to download...'
                    prep_mes(message)
                except urllib.error.URLError as e:
                    logging.exception(e)
                    message = 'Trying to download...'
                    prep_mes(message)
                else:
                    dl = False
            message = 'Done'
            prep_mes(message)
            if audio_itag:
                fileName += '_audio'
                stream = video.streams.get_by_itag(audio_itag)
                audio_itag = None
                dl = True       #download audio
                message = 'Downloading audio...'
                prep_mes(message)
                while dl:       #audio
                    try:
                        stream.download(output_path=Filepath,filename=fileName)
                    except FileNotFoundError as e:
                        logging.exception(e)
                        message = 'Trying to download...'
                        prep_mes(message)
                    except urllib.error.URLError as e:
                        logging.exception(e)
                        message = 'Trying to download...'
                        prep_mes(message)
                    else:
                        dl = False
                message = 'Done'
                prep_mes(message)
    for lang in subchoices.keys():
        if subchoices[lang][0].get():
            dl = True
            cap = video.captions.get_by_language_code(subchoices[lang][1])
            fileName += subchoices[lang][1]
            message = 'Downloading caption %s...' % lang
            prep_mes(message)
            while dl:
                try:
                    cap.download(fileName,output_path=Filepath)
                except FileNotFoundError as e:
                    logging.exception(e)
                    message = 'Trying to download...'
                    prep_mes(message)
                except urllib.error.URLError as e:
                    logging.exception(e)
                    message = 'Trying to download...'
                    prep_mes(message)
                else:
                    dl = False
            message = 'Done'
            prep_mes(message)

#root
root = Tk()
root.title('YouTube Downloader')
root.resizable(0,0)
#mainframe
mainframe = ttk.Frame(root,padding=(5,10))  #5 on l,r, 10 on t,b
#message canvas
mes_canvas = Canvas(mainframe,background='grey95',width=280,scrollregion=(0,0,280,2000),relief='sunken',borderwidth=2)
#message label
mes_label = ttk.Label(mes_canvas,text='Messages')
mes_canvas.create_window(40,20,window=mes_label)
#message scrollbar
s_bar = ttk.Scrollbar(mainframe,orient=VERTICAL,command=mes_canvas.yview)
mes_canvas['yscrollcommand'] = s_bar.set
#Enter label
myfont = font.Font(family='arial',size=10,weight='bold')
enter_label = ttk.Label(mainframe,text='Enter video URL :',font=myfont)
#Enter entry
check_entry_wrapper = (root.register(check_entry),'%P','%V')
url = StringVar()
entry = ttk.Entry(mainframe,textvariable=url,width=40,validate='all',validatecommand=check_entry_wrapper)
#Wrong URL message label
content = 'Please enter valid URL first'
error_msg = ttk.Label(mainframe,foreground='red',text='')
#rename label
re_label = ttk.Label(mainframe,text='Save file as :',font=myfont)
#rename checkbutton
re_button = ttk.Button(mainframe,text='Autofill original filename',command=auto_fill)
re_button['state'] = 'disabled'
#rename entry
rename_entry = ttk.Entry(mainframe,width=40)        #when pressing the ok button, it will get the renamed filename if any. 
rename_entry['state'] = 'disabled'
#file path label
path_label = ttk.Label(mainframe,text='Save To',font=myfont)
#file path text
path_text =Text(mainframe,width=40,height=1,relief='flat',wrap='none')
path_text.insert('1.0',Filepath)
path_text.configure(state=DISABLED)       #do not allow users to edit
#file path button call filedialog
path_button = ttk.Button(mainframe,text='Browse',command=file_dialog)
#ok button
ok_button = ttk.Button(mainframe,text='Load',default='active',command=display_streams)
ok_button.state(['disabled'])
#select label
s_msg = StringVar()
s_msg.set('')
s_label = ttk.Label(mainframe,textvariable=s_msg,foreground='white')
#stream labels
valabel = ttk.Label(mainframe,text='video&audio\ncombined download')
vlabel = ttk.Label(mainframe,text='video&audio\nseperated download')
sublabel = ttk.Label(mainframe,text='subtitles')
#stream canvases
vacanvas = Canvas(mainframe,width=170,height=100,background='white',relief='sunken',borderwidth=2)
vcanvas = Canvas(mainframe,width=170,height=100,background='white',relief='sunken',borderwidth=2)
subcanvas = Canvas(mainframe,width=170,height=200,scrollregion=(0,0,170,2000),background='white',relief='sunken',borderwidth=2)
#sub scrollbar
sub_bar = ttk.Scrollbar(mainframe,orient=VERTICAL,command=subcanvas.yview)
subcanvas['yscrollcommand'] = sub_bar.set
#download button
d_style = ttk.Style()
myfont = font.Font(family='arial',size=14)
d_style.configure('d_button.TButton',font=myfont)
d_button = ttk.Button(mainframe,text='Download',style='d_button.TButton',default='active',command=download,state='disabled')

#grid
mainframe.grid(column=0,row=0,sticky=(N,S,E,W))
mes_canvas.grid(column=0,columnspan=2,row=7,rowspan=9,sticky=(N,S,E,W))
s_bar.grid(column=2,row=7,rowspan=9,sticky=(N,S,E,W))
enter_label.grid(column=0,row=0,sticky=(W))
entry.grid(column=0,columnspan=2,row=1,sticky=(W))
error_msg.grid(column=1,row=0,sticky=(E,S))
re_label.grid(column=0,row=3,sticky=(W,N))
re_button.grid(column=1,row=3,sticky=(E,N))
rename_entry.grid(column=0,columnspan=2,row=4,sticky=(N,W))
#rename_entry.grid_remove()      #first this entry is not visible
path_label.grid(column=0,row=5,sticky=(W))
path_button.grid(column=1,row=5,sticky=(E),pady=5)
path_text.grid(column=0,columnspan=2,row=6,sticky=(N,W))
ok_button.grid(column=0,columnspan=2,row=2,sticky=(N))
s_label.grid(column=3,row=0)
valabel.grid(column=3,row=1,padx=(20,0),sticky=(W))
vlabel.grid(column=3,row=5,padx=(20,0),sticky=(W))
sublabel.grid(column=3,row=9,padx=(20,0),sticky=(W))
vacanvas.grid(column=3,row=2,rowspan=3,padx=(20,0))
vcanvas.grid(column=3,row=6,rowspan=3,padx=(20,0),sticky=(N,W,E,S))
subcanvas.grid(column=3,row=10,rowspan=6,padx=(20,0),sticky=(N,W,E,S))
sub_bar.grid(column=4,row=10,rowspan=6,sticky=(N,S,E,W))
sub_bar.grid_remove()      #first this scrollbar is not visible,only when captions overfill canvas
d_button.grid(column=0,columnspan=4,row=16)

t = threading.Thread(target=check)
t.start()
root.mainloop()
thread_ind = False