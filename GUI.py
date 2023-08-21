#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 13:36:58 2021

@author: bing
"""

# import all the required  modules
import threading
import select
from tkinter import *
from tkinter import messagebox
from tkinter.messagebox import *
from tkinter import font
from tkinter import ttk
from chat_utils import *
from chat_server import *
import json


# GUI class for the chat


class GUI:
    # constructor method
    def __init__(self, send, recv, sm, s):
        # chat window which is currently hidden
        self.Window = Tk()
        self.Window.withdraw()
        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s
        self.my_msg = ""
        self.system_msg = ""

    def login(self):
        # login window
        self.login = Toplevel()
        # set the title
        self.login.title("Weechat")
        self.login.resizable(width=False,
                             height=False)
        self.login.configure(width=400,
                             height=300,
                             bg='whitesmoke')
        # create a Label
        self.pls = Label(self.login,
                         text="Please login to continue",
                         justify=CENTER,
                         font="Helvetica 14 bold")

        self.pls.place(relheight=0.15,
                       relx=0.2,
                       rely=0.07)
        # create a Label
        self.labelName = Label(self.login,
                               text="Name: ",
                               font="Helvetica 12")
    #creaate password
        self.labelKey = Label(self.login,
                               text="Password: ",
                               font="Helvetica 12")
        
        
        self.labelName.place(relheight=0.2,
                             relx=0.1,
                             rely=0.2)
    #place the password
        self.labelKey.place(relheight=0.2,
                             relx=0.1,
                             rely=0.35)

        # create a entry box for
        # tyoing the message
        self.entryName = Entry(self.login,
                               font="Helvetica 14")
    # password  font
        self.entryKey = Entry(self.login,
                               font="Helvetica 14")       
        
        self.entryName.place(relwidth=0.4,
                             relheight=0.12,
                             relx=0.35,
                             rely=0.23)
    #password place
        self.entryKey.place(relwidth=0.4,
                             relheight=0.12,
                             relx=0.35,
                             rely=0.35)

        # set the focus of the curser
        self.entryName.focus()
        self.entryKey.focus()

        # create a Continue Button
        # along with action
        self.go = Button(self.login,
                         text="LOG IN",
                         font="Helvetica 14",
                         bg='limegreen',
                         fg='black',
                         relief='flat',
                         command=lambda: self.goAhead(self.entryName.get(),self.entryKey.get()))
    # the button to go to the register layer
        self.reg=Button(self.login,
                        text='REGISTER',
                        font='Helvetica 14',
                        bg='limegreen',
                        fg='black',
                        relief='flat',
                        command=lambda:self.regUI())
        self.go.place(relx=0.4,
                      rely=0.55,
                      relwidth=0.29)
        self.reg.place(relx=0.4,
                        rely=0.70,
                        relwidth=0.29)
        self.Window.mainloop()
#add a layout for register
    def regUI(self):
        #login window
        self.regUI=Toplevel()

        self.regUI.title=('REGISTER')
        self.regUI.resizable(width=False,height=False)
        self.regUI.configure(width=400,height=225)
        #label for creating an account
        self.pls=Label(self.regUI,text='Please Create Your Account',
                        justify=CENTER,
                        font='Helvetica 14 bold')
        
        self.pls.place(relheight=0.15,relx=0.2,rely=0.07)

        #create a label for registering
        self.labelName=Label(self.regUI,text='Name:',font='Helvetica 12')
        self.labelKey=Label(self.regUI,text='Password',font='Helvetica 12')
        self.labelName.place(relheight=0.2,relx=0.13,rely=0.2)
        self.labelKey.place(relheight=0.2,relx=0.13,rely=0.35)

        #create an entry box
        self.regName=Entry(self.regUI,font='Helvetica 14')
        self.regKey=Entry(self.regUI,font='Helvetica 14')
        self.regName.place(relwidth=0.4,relheight=0.12,relx=0.35,rely=0.23)
        self.regKey.place(relwidth=0.4,relheight=0.12,relx=0.35,rely=0.35)

        #set the focus on curser
        self.regName.focus()
        self.regKey.focus()

        #set the botton to continue to the register function
        self.reg=Button(self.regUI,text='REGISTER',font='Helvetica 14',bg='limegreen',fg='black',relief='flat',
                        command=lambda:self.Register(self.regName.get(),self.regKey.get()))

        self.reg.place(relx=0.4,
                      rely=0.6)

        self.Window.mainloop()
    
    
    def goAhead(self, name,key):
        if len(name) > 0:
            msg = json.dumps({"action": "login", "name": name,'password':key})
            self.send(msg)
            response = json.loads(self.recv())
            if response['status'] == 'notexist':
                showwarning(title="No account",message="Can't find your account, please register first")
            elif response['status'] == 'wrong':
                showwarning(title="Wrong password",message="your enter a wrong password, please quit and enter again")
            elif response["status"] == 'ok':
                '''print('okay--------------')'''
                self.login.destroy()
                self.sm.set_state(S_LOGGEDIN)
                self.sm.set_myname(name)
                self.layout(name)
                self.textCons.config(state=NORMAL)
                # self.textCons.insert(END, "hello" +"\n\n")
                self.textCons.insert(END, menu + "\n\n")
                self.textCons.config(state=DISABLED)
                self.textCons.see(END)
                # while True:
                #     self.proc()
        # the thread to receive messages
            process = threading.Thread(target=self.proc)
            process.daemon = True
            process.start()
#define the register function
    def Register(self,name,key):
        if name=='' or key=='':
            showwarning(title='Invalid input',message="Helvetica 12")
            return
        else:
            msg=json.dumps({'action':'register','name':name,'password':key})
            self.send(msg)
            response=json.loads(self.recv())
            if response['status']=='duplicate':
                showerror(title='Error',message='you have already logged in. Do not register again')
            elif response['status']=='ok':
                showinfo(title='success',message='you have your account now!')

    # The main layout of the chat
    def layout(self, name):

        self.name = name
        # to show chat window
        self.Window.deiconify()
        self.Window.title("CHATROOM")
        self.Window.resizable(width=False,
                              height=False)
        self.Window.configure(width=470,
                              height=550,
                              bg="lightgrey")
        self.labelHead = Label(self.Window,
                               bg="whitesmoke",
                               fg="black",
                               text=self.name,
                               font="Helvetica 13 bold",
                               pady=5)

        self.labelHead.place(relwidth=1)
        self.line = Label(self.Window,
                          width=450,
                          bg="#ABB2B9")

        self.line.place(relwidth=1,
                        rely=0.07,
                        relheight=0.012)

        self.textCons = Text(self.Window,
                             width=20,
                             height=2,
                             bg="whitesmoke",
                             fg="black",
                             font="Helvetica 14",
                             padx=5,
                             pady=5)

        self.textCons.place(relheight=0.745,
                            relwidth=1,
                            rely=0.08)

        self.labelBottom = Label(self.Window,
                                 bg="whitesmoke",
                                 height=80)

        self.labelBottom.place(relwidth=1,
                               rely=0.825)

        self.entryMsg = Entry(self.labelBottom,
                              bg="whitesmoke",
                              fg="black",
                              font="Helvetica 13")

        # place the given widget
        # into the gui window
        self.entryMsg.place(relwidth=0.74,
                            relheight=0.06,
                            rely=0.004,
                            relx=0.011)

        self.entryMsg.focus()

        # create a Send Button
        self.buttonMsg = Button(self.labelBottom,
                                text="Send",
                                font="Helvetica 10 bold",
                                width=20,
                                bg="gainsboro",
                                fg='limegreen',
                                relief='flat',
                                command=lambda: self.sendButton(self.entryMsg.get()))

        self.buttonMsg.place(relx=0.77,
                             rely=0.004,
                             relheight=0.03,
                             relwidth=0.22)

        self.textCons.config(cursor="arrow")
        
        
        # create a Game button
        self.buttonG = Button(self.labelBottom,
                             text = "Game!!!",
                             font="Helvetica 10 bold",
                             width=20,
                             bg="gainsboro",
                             fg='limegreen',
                             relief='flat',
                             command = self.start_game)
        self.buttonG.place(relx=0.77,
                              rely=0.036,
                              relheight=0.03,
                              relwidth=0.22)

        self.textCons.config(cursor="arrow")
        
        
        # create a scroll bar
        scrollbar = Scrollbar(self.textCons)

        # place the scroll bar
        # into the gui window
        scrollbar.place(relheight=1,
                        relx=0.974)

        scrollbar.config(command=self.textCons.yview)

        self.textCons.config(state=DISABLED)

    # function to basically start the thread for sending messages

    def sendButton(self, msg):
        # self.textCons.config(state=DISABLED)
        self.my_msg = msg
        # print(msg)
        self.entryMsg.delete(0, END)
        self.textCons.config(state=NORMAL)
        self.textCons.insert(END, msg + "\n")
        self.textCons.config(state=DISABLED)
        self.textCons.see(END)

    def proc(self):
        # print(self.msg)
        while True:
            read, write, error = select.select([self.socket], [], [], 0)
            peer_msg = []
            # print(self.msg)
            if self.socket in read:
                peer_msg = self.recv()
            if len(self.my_msg) > 0 or len(peer_msg) > 0:
                # print(self.system_msg)
                self.system_msg = self.sm.proc(self.my_msg, peer_msg)
                self.my_msg = ""
                self.textCons.config(state=NORMAL)
                self.textCons.insert(END, self.system_msg + "\n\n")
                self.textCons.config(state=DISABLED)
                self.textCons.see(END)
    
    
    # define the start game function 
    def start_game(self):
        self.my_msg = "request_to_start_a_game"
    
    def run(self):
        self.login()


# create a GUI class object
if __name__ == "__main__":
    # g = GUI()
    pass
