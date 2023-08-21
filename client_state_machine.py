"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat_utils import *
import json
#import operating system to start the game
import os
import sys
#import chess files
#import snake_ladder as snake
import random
import threading

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s
        # add the emoji function
        self.emoji = {
        ':-)': chr(0x1F642),
        ':-D': chr(0x1F600),
        ':-(': chr(0x2639),
        ':\'-(': chr(0x1F622),
        ':-O': chr(0x1F62E),
        ';-)': chr(0x1F609),
        ':-P': chr(0x1F61B),
        '>:[': chr(0x1F620),
        ':-/': chr(0x1F914),
        'B-)': chr(0x1F60E),
            }
        ####------------secure message--------#######
        self.private_key=random.randint(1,25)
        #create the base of public-private number
        self.base=6
        # the clock need to be devided: requirement: primitive root of clock key
        self.clock=11
        #shared key, undecided yet
        self.shared_key=None
        self.p_p_key=self.base**self.private_key%self.clock
    
    #track the last move from your oppornent
        self.last_move=None
#send back the movement of your opponent to the chess python file
    def send_movement(self):
        return self.last_move
####---------------------secure message functions---------------------####
    def get_p_p_key(self):
        return self.base**self.private_key%self.clock

    def get_shared_key(self,p_p_key):
        return p_p_key**self.private_key%self.clock
    
    def encoded(self,msg):
        encoded_msg=''
        for i in msg:
            encoded_msg+=chr(ord(i)+self.shared_key)
        return encoded_msg

    def decoded(self,msg):
        decoded_msg=''
        for i in msg:
            decoded_msg+=chr(ord(i)-self.shared_key)
        return decoded_msg
####---------------------secure message functions edn------------------####

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = json.dumps({"action":"connect", "target":peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def proc(self, my_msg, peer_msg):
        self.out_msg = ''
#==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
#==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:

                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE
                
                #add the emoji
                elif my_msg=='emoji':
                    self.out_msg+='try the following emojis!\n'
                    for i in self.emoji.keys():
                        self.out_msg+=i
                        self.out_msg+='\n'
                
                #add check game rank
                elif my_msg=='rank':
                    self.out_msg+='requesting for rank'
                    mysend(self.s,json.dumps({'action':'rank1','from':self.me}))
                    message=json.loads(myrecv(self.s))['message']
                    message1=json.loads(myrecv(self.s))['message1']
                    self.out_msg+=message1

                    for item in message:
                        for i in item:
                            self.out_msg+=str(i)
                        self.out_msg+='\n'
                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action":"list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"search", "target":term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p' and my_msg[1:].isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"poem", "target":poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    # print(poem)
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"] == "connect":
                    self.peer = peer_msg["from"]
                    self.out_msg += 'Request from ' + self.peer + '\n'
                    self.out_msg += 'You are connected with ' + self.peer
                    self.out_msg += '. Chat away!\n\n'
                    self.out_msg += '------------------------------------\n'
                    self.state = S_CHATTING

#==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
#==============================================================================
        elif self.state == S_CHATTING:
            if len(my_msg) > 0:     # my stuff going out
                # add the game request 
                if my_msg=='request_to_start_a_game':
                    mysend(self.s,json.dumps({'action':'game','from':'['+self.me+']'}))
                    self.out_msg+=' game request sent, waiting for the server to check...\n'
                    response=json.loads(myrecv(self.s))
                    if response['status']=='success':
                        self.out_msg+='Gaming request approved, enjoy your game!\n'
                        self.out_msg+='--------------------------------------------\n'
                        self.state=S_GAMING1
                    elif response['status']=='fail':
                        self.out_msg+=response['message']
                
                elif my_msg=='guess':
                    target_num=random.randint(0,100)
                    mysend(self.s,json.dumps({'action':'game1','from':self.me,'target_number':target_num}))
                    self.out_msg+='Game start successfully\n Guess a number between 0 to 100:\n Type the number with "Game:" at the beginning.'

                elif my_msg[:5]=='Game:':
                    num=my_msg[5:]
                    number=int(num)
                    mysend(self.s,json.dumps({'action':'guess','from':self.me,'number':number}))
            
                
                #check the rank
                elif my_msg=='rank':
                    mysend(self.s,json.dumps({'action':'rank','from':self.me}))
                    self.out_msg+='requesting for the rank'
            
             ####--------------------encode the message------------------####
                elif my_msg[0]=='#':
                    print('this is private key',self.private_key)
                    mysend(self.s,json.dumps(
                        {'action':'produce_p_p_key','from':'['+self.me+']',
                        'message':self.p_p_key}
                    ))
                    self.out_msg+='public private key sent, waiting for response'
                    print('this is p_p_key',self.p_p_key)
                
                elif my_msg[0]=='^':
                    if self.shared_key==None:
                        self.out_msg+='you do not have a shared key yet, can not send encoded message'
                    else:
                        encoded='^'
                        encoded+=self.encoded(my_msg[1:])
                        mysend(self.s,json.dumps({'action':'coded','from':'['+self.me+']','message':encoded}))
            ####-------------------end of encode message-----------------####      

            #add the emoji function
                elif my_msg in self.emoji.keys():
                    mysend(self.s,json.dumps({'action':'emoji','message':my_msg}))
                
                else:
                    mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
            
            if len(peer_msg) > 0:    # peer's stuff, coming in
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"] == "connect":
                    self.out_msg += "(" + peer_msg["from"] + " joined)\n"
                elif peer_msg["action"] == "disconnect":
                    self.state = S_LOGGEDIN
                ####---------------------------encode the message--------------------####
                
                elif peer_msg['action']=='produce_p_p_key':
                    print('this is private key',self.private_key)
                    p_p_key=self.get_p_p_key()
                    print('this is public private key',p_p_key)
                    mysend(self.s,json.dumps({
                        'action':'produce_shared_key','message':p_p_key}
                    ))
                    print('this is the peer p_p_key',int(peer_msg['message']))
                    self.shared_key=self.get_shared_key(int(peer_msg['message']))
                    print('this is shared key',self.shared_key)
                    self.out_msg+='you have got the shared key, type ^ before your message to encode your message'
                
                elif peer_msg['action']=='produce_shared_key':
                    print('this is the peer p_p_key',int(peer_msg['message']))
                    self.shared_key=self.get_shared_key(int(peer_msg['message']))
                    print('this is the shared key',self.shared_key)
                    self.out_msg+='you have got the shared key, type ^ before your message to encode your message'
                
                elif peer_msg['action']=='coded':
                    if self.shared_key==None:
                        self.out_msg+='you do not have a shared key yet, can not send encoded message'
                    else:
                        decode=self.decoded(peer_msg['message'][1:])
                        self.out_msg+='['
                        self.out_msg+=peer_msg['from']
                        self.out_msg+=']'
                        self.out_msg+=decode
                
                elif peer_msg['action']=='game_start':
                    self.out_msg+=peer_msg['from']
                    self.out_msg+="invites you to the game.\nGuess a number between 0 to 100:\nType the number with 'Game:' at the beginning." 
                
                elif peer_msg['action']=='done_guess':
                    self.out_msg+=peer_msg['message']
                
                #show game rank
                elif peer_msg['action']=='rank':
                    message=peer_msg['message']
                    for item in message:
                        for i in item:
                            self.out_msg+=str(i)
                        self.out_msg+='\n'
                
                # add the response for peer message gaming
                elif peer_msg['action']=='game':
                    self.out_msg+='You recieced a request for gaming from peer\n'
                    if peer_msg['status']=='fail':
                        self.out_msg+=peer_msg['message']
                    elif peer_msg['status']=='success':
                        self.out_msg+=peer_msg['message']
                        self.out_msg+='\n'
                        self.out_msg+=peer_msg['result']
                        self.out_msg+='\n'
                        self.out_msg+='click the game button to get the game window'
                        self.state=S_GAMING2
                #add the emoji 
                elif peer_msg['action']=='emoji':
                    self.out_msg+=peer_msg['from']
                    self.out_msg+=peer_msg['message']
                #add the gaming action
                elif peer_msg['action']=='gaming':
                    self.out_msg+=peer_msg['message']
                else:
                    self.out_msg += peer_msg["from"] 
                    self.out_msg +=str(peer_msg["message"])
                


            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
        
        # add the game state
        elif self.state==S_GAMING1:
            #the operating system method may induce some unknown mistakes
            os.system('python /Users/chijiean/Desktop/ICS\ final\ project/chat_system_gui\ \(2\)\ 2/chess_v2_GUI2.py')
            #snake.main()
            #os.system('python /Users/chijiean/Desktop/ICS\ final\ project/chat_system_gui\ \(2\)\ 2/game_server.py')
            #os.system('python /Users/chijiean/Desktop/ICS\ final\ project/chat_system_gui\ \(2\)\ 2/snake_ladder.py')
            self.out_msg += "We have stopped your game.\n"
            self.state = S_LOGGEDIN
            self.out_msg += "\n"
            self.out_msg += menu

        elif self.state==S_GAMING2:
            os.system('python /Users/chijiean/Desktop/ICS\ final\ project/chat_system_gui\ \(2\)\ 2/chess_v2_GUI2.py')
            self.out_msg += "We have stopped your game.\n"
            self.state = S_LOGGEDIN
            self.out_msg += "\n"
            self.out_msg += menu
            
#==============================================================================
# invalid state
#==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
