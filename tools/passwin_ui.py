#!/usr/bin/env python
#-*-coding: utf-8 -*-

'''
I know it's bad, but I really do not want to do
'''

import sys
from Tkinter import *
from PIL import Image, ImageTk

png = sys.argv[1]
root = Tk()
swidth = root.winfo_screenwidth()
sheight = root.winfo_screenheight()
width = 300
height = 250
root.geometry('%dx%d+%d+%d' % (width, height, (swidth-width)/2 , (sheight-height)/2))
#label = Label(root, text=u'请输入验证码:')
label = Label(root, text=u'input passcode:')
label.config(font='-size 30')
label.pack()
img = Image.open(png)
img = img.resize((img.size[0] * 3, img.size[1] * 3))
img_tk = ImageTk.PhotoImage(img)
img_label = Label(root, image=img_tk)
img_label.pack()
passvar = StringVar()
def quit_fun():
    print passvar.get()
    root.quit()
def callback(sv):
    var = sv.get()
    if len(var) >= 4:
        quit_fun()
def enter(event):
    quit_fun()
passvar.trace("w", lambda name, index, mode, passvar=passvar: callback(passvar))
passentry = Entry(root, textvariable=passvar)
passentry.config(font='-size 50')
passentry.config(width='7')
passentry.pack()
passentry.focus()
quit = Button(root, text='确定', command=quit_fun)
quit.config(font='-size 30')
quit.config(width='10')
quit.pack()
root.bind('<Return>', enter)
root.attributes("-topmost", True)

if sys.platform == 'darwin':
    import os
    os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "python" to true' ''')

root.mainloop()
