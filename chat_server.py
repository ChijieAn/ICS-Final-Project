"""
Created on Tue Jul 22 00:47:05 2014

@author: alina, zzhang
"""

import time
import socket
import select
import sys
import string
import indexer
import json
import pickle as pkl
from chat_utils import *
import chat_group as grp

class Server:
    def __init__(self):
        self.new_clients = []  # list of new sockets of which the user id is not known
        self.logged_name2sock = {}  # dictionary mapping username to socket
        self.logged_sock2name = {}  # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
    # the dictionary for passwords
        try:
            Database=open('namePassword.dat','rb')
            self.password=pkl.load(Database)
            Database.close()
            print('Database loaded successfully\n')
        except(FileNotFoundError,EOFError):
            self.password={}
            print('No Database Found. Creating one.\n')
    #try dicstionary for game records
        try:
            Database_game=open('nameGame.dat','rb')
            self.record=pkl.load(Database_game)
            Database_game.close()
            print("Game Database loaded successfully\n")
        except(FileNotFoundError,EOFError):
            self.record={}
            print('No Game Database found. Creating one.\n')
       
        # start server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        # initialize past chat indices
        self.indices = {}
        # sonnet
        # self.sonnet_f = open('AllSonnets.txt.idx', 'rb')
        # self.sonnet = pkl.load(self.sonnet_f)
        # self.sonnet_f.close()
        '''self.sonnet = indexer.PIndex("AllSonnets.txt")'''
    #add the dictionary for emojis
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
        self.Tnum=-1
#define the function to handle emojis
    def emoji_message(self,message):
        for (emoticon, emoji) in self.emoji.items():
            message = message.replace(emoticon, emoji)
        return message
    
    def new_client(self, sock):
        # add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        # read the msg that should have login code plus username
        try:
            msg = json.loads(myrecv(sock))
            print("login:", msg)
            if len(msg) > 0:

            #add the register action:
                if msg['action']=='register':
                    name=msg['name']
                    password=msg['password']
                    if name in self.password.keys():
                        mysend(sock,json.dumps({'action':'register','status':'duplicate'}))
                    else:
                        self.password[name]=password
                        Database=open('namePassword.dat','wb')
                        pkl.dump(self.password,Database)
                        Database.close()
                        mysend(sock,json.dumps({'action':'register','status':'ok'}))
                        print(name,'successfully registered')

                if msg["action"] == "login":
                    name = msg["name"]
                    password=msg['password']
                    if name not in self.password.keys():
                        mysend(sock,json.dumps({'action':'login','status':'notexist'}))
                    elif self.password[name]!=msg['password']:
                        mysend(sock,json.dumps({'action':'login','status':'wrong'}))
                    else:
                        if self.group.is_member(name) != True:
                        # move socket from new clients list to logged clients
                            self.new_clients.remove(sock)
                        # add into the name to sock mapping
                            self.logged_name2sock[name] = sock
                            self.logged_sock2name[sock] = name
                        # load chat history of that user
                            if name not in self.indices.keys():
                                try:
                                    self.indices[name] = pkl.load(
                                        open(name+'.idx', 'rb'))
                                except IOError:  # chat index does not exist, then create one
                                    self.indices[name] = indexer.Index(name)
                            print(name + ' logged in')
                            self.group.join(name)
                            mysend(sock, json.dumps(
                                {"action": "login", "status": "ok"}))
                        else:  # a client under this name has already logged in
                            mysend(sock, json.dumps(
                                {"action": "login", "status": "duplicate"}))
                            print(name + ' duplicate login attempt')
                else:
                    print('wrong code received')
            else:  # client died unexpectedly
                self.logout(sock)
        except:
            self.all_sockets.remove(sock)

    def logout(self, sock):
        # remove sock from all lists
        name = self.logged_sock2name[sock]
        pkl.dump(self.indices[name], open(name + '.idx', 'wb'))
        del self.indices[name]
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        sock.close()

# ==============================================================================
# main command switchboard
# ==============================================================================
    def handle_msg(self, from_sock):
        # read msg code
        print("mysend", mysend)
        msg = myrecv(from_sock)
        if len(msg) > 0:
            # ==============================================================================
            # handle connect request
            # ==============================================================================
            msg = json.loads(msg)
            if msg["action"] == "connect":
                to_name = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg = json.dumps({"action": "connect", "status": "self"})
                # connect to the peer
                elif self.group.is_member(to_name):
                    print("mysend function", mysend)
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name)
                    msg = json.dumps(
                        {"action": "connect", "status": "success"})
                    for g in the_guys[1:]:
                        to_sock = self.logged_name2sock[g]
                        mysend(to_sock, json.dumps(
                            {"action": "connect", "status": "request", "from": from_name}))
                else:
                    msg = json.dumps(
                        {"action": "connect", "status": "no-user"})
                mysend(from_sock, msg)
# ==============================================================================
# handle messeage exchange: one peer for now. will need multicast later
# ==============================================================================
            elif msg["action"] == "exchange":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                #said = msg["from"]+msg["message"]
                said2 = text_proc(msg["message"], from_name)
                self.indices[from_name].add_msg_and_index(said2)
                for g in the_guys[1:]:
                    to_sock = self.logged_name2sock[g]
                    self.indices[g].add_msg_and_index(said2)
                    mysend(to_sock, json.dumps(
                        {"action": "exchange", "from": msg["from"], "message": msg["message"]}))
# ==============================================================================
#                 listing available peers
# ==============================================================================
            elif msg["action"] == "list":
                from_name = self.logged_sock2name[from_sock]
                msg = self.group.list_all()
                mysend(from_sock, json.dumps(
                    {"action": "list", "results": msg}))
# ==============================================================================
#             retrieve a sonnet
# ==============================================================================
            elif msg["action"] == "poem":
                poem_indx = int(msg["target"])
                from_name = self.logged_sock2name[from_sock]
                print(from_name + ' asks for ', poem_indx)
                poem = self.sonnet.get_poem(poem_indx)
                poem = '\n'.join(poem).strip()
                print('here:\n', poem)
                mysend(from_sock, json.dumps(
                    {"action": "poem", "results": poem}))
# ==============================================================================
#                 time
# ==============================================================================
            elif msg["action"] == "time":
                ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
                mysend(from_sock, json.dumps(
                    {"action": "time", "results": ctime}))
# ==============================================================================
#                 search
# ==============================================================================
            elif msg["action"] == "search":
                term = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                print('search for ' + from_name + ' for ' + term)
                # search_rslt = (self.indices[from_name].search(term))
                search_rslt = '\n'.join(
                    [x[-1] for x in self.indices[from_name].search(term)])
                print('server side search: ' + search_rslt)
                mysend(from_sock, json.dumps(
                    {"action": "search", "results": search_rslt}))
# ==============================================================================
# the "from" guy has had enough (talking to "to")!
# ==============================================================================
            elif msg["action"] == "disconnect":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                if len(the_guys) == 1:  # only one left
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps({"action": "disconnect"}))
# ==============================================================================
#                 the "from" guy really, really has had enough
# ==============================================================================


#create the gaming action
            elif msg['action']=='game':
                #get the person who sent the message
                from_name=self.logged_sock2name[from_sock]
                
                The_guys=self.group.list_me(from_name)
                in_group,groupnum=self.group.find_group(from_name)
                numbers=len(The_guys)

                for g in The_guys:
                    to_sock=self.logged_name2sock[g]

                    if numbers>2:
                        mysend(to_sock,json.dumps(
                            {'action':'game','from':msg['from'],'message':'Unable to start the game because the number of players is more than two',
                            'status':'fail','result':'[server]:Unable to start the game! there are more than two people in the group'}
                        ))
                        mysend(from_sock,json.dumps(
                            {'action':'game','from':msg['from'],'message':'Unable to start the game because the number of players is more than two',
                            'status':'fail','result':'[server]:Unable to start the game! there are more than two people in the group'}
                        ))
                    elif numbers==2:
                        mysend(to_sock,json.dumps({
                            'action':'game','from':msg['from'],
                            'message':'game successfully started','status':'success','result':
                            '[server]:Enjoy the game!'}
                        ))
                        mysend(from_sock,json.dumps(
                            {'action':'game','from':msg['from'],'message':'Unable to start the game because the number of players is more than two',
                            'status':'fail','result':'[server]:Unable to start the game! there are more than two people in the group'}
                        ))

            elif msg['action']=='gaming':
                from_name=self.logged_sock2name[from_sock]
                The_guys=self.group.list_me(from_name)
                to_sock=self.logged_name2sock[The_guys[1:]]
                mysend(to_sock,json.dumps({
                    'action':'gaming','message':msg['message'],'target':to_sock
                }))

            #add the action game1 for guess number game
            elif msg['action']=='game1':
                self.Tnum=msg['target_number']
                from_name=self.logged_sock2name[from_sock]
                the_guys=self.group.list_me(from_name)

                for g in the_guys[1:]:
                    to_sock=self.logged_name2sock[g]
                    mysend(to_sock,json.dumps(
                        {'action':'game_start','from':msg['from']}
                    ))
            
            
            #add the gaming part(guess number)
            elif msg['action']=='guess':
                num=int(msg['number'])
                player=msg['from']
                print(self.Tnum)
                if num<self.Tnum:
                    message=str(num)+' is too small. Try again,'+player+'!'
                elif num>self.Tnum:
                    message=str(num)+' is too large.Try again,'+player+'!'
                else:
                    if player not in self.record.keys():
                        self.record[player]=1
                    elif player in self.record.keys():
                        self.record[player]+=1
                    Database_game=open('nameGame.dat','wb')
                    pkl.dump(self.record,Database_game)
                    Database_game.close()
                    message='You get it right! \n'
                    message+='The number is'+str(self.Tnum)+'.'+'Good job,'+player+'!'
                    message+='\n'
                    message+='input rank to check out the rank'

                from_name=self.logged_sock2name[from_sock]
                the_guys=self.group.list_me(from_name)
                for g in the_guys:
                    to_sock=self.logged_name2sock[g]
                    mysend(to_sock,json.dumps(
                        {'action':'done_guess','from':player,'message':message}
                    ))
            #send the rank of the game to the client
            elif msg['action']=='rank':
                from_name=self.logged_sock2name[from_sock]
                the_guys=self.group.list_me(from_name)
                message=list(self.record.items())
                print(message)
                for g in the_guys:
                    to_sock=self.logged_name2sock[g]
                    mysend(to_sock,json.dumps(
                        {'action':'rank','message':message}
                    ))
            elif msg['action']=='rank1':
                 mysend(from_sock,json.dumps({'action':'rank1','message':self.record,'message1':'here is the rank'}))



#create emoji            
            elif msg['action']=='emoji':
                from_name=self.logged_sock2name[from_sock]
                The_guys=self.group.list_me(from_name)
                for g in The_guys:
                    to_sock=self.logged_name2sock[g]
                    mysend(to_sock,json.dumps({'action':'emoji','from':'['+from_name+']','message':self.emoji_message(msg['message'])}))
        
        
            ####----------------------add the encode message----------------####        
            
            elif msg['action']=='produce_p_p_key':
                from_name=self.logged_sock2name[from_sock]
                The_guys=self.group.list_me(from_name)
                numbers=len(The_guys)
                if numbers>2:
                    mysend(from_sock,json.dumps({'action':'exchange','from':'[server]','message':'unable to encode, more than two people'}))
                elif numbers==2:
                    for g in The_guys[1:]:
                        to_sock=self.logged_name2sock[g]
                        mysend(to_sock,json.dumps(
                            {'action':'produce_p_p_key','target':from_name,'from':from_name,'message':msg['message']}
                        ))
            
            elif msg['action']=='produce_shared_key':
                from_name=self.logged_sock2name[from_sock]
                The_guys=self.group.list_me(from_name)
                numbers=len(The_guys)
                if numbers>2:
                    mysend(from_sock,json.dumps({'action':'exchange','from':'[server]','message':'unable to encode, more than two people'}))
                elif numbers==2:
                    for g in The_guys[1:]:
                        to_sock=self.logged_name2sock[g]
                        mysend(to_sock,json.dumps(
                            {'action':'produce_shared_key','target':from_name,'from':from_name,'message':msg['message']}
                        ))
            elif msg['action']=='coded':
                from_name=self.logged_sock2name[from_sock]
                The_guys=self.group.list_me(from_name)
                for g in The_guys[1:]:
                    to_sock=self.logged_name2sock[g]
                    mysend(to_sock,json.dumps(
                        {'action':'coded','from':from_name,'message':msg['message']}
                    ))
                
        else:
            # client died unexpectedly
            self.logout(from_sock)

# ==============================================================================
# main loop, loops *forever*
# ==============================================================================
    def run(self):
        print('starting server...')
        while(1):
            read, write, error = select.select(self.all_sockets, [], [])
            print('checking logged clients..')
            for logc in list(self.logged_name2sock.values()):
                if logc in read:
                    self.handle_msg(logc)
            print('checking new clients..')
            for newc in self.new_clients[:]:
                if newc in read:
                    self.login(newc)
            print('checking for new connections..')
            if self.server in read:
                # new client request
                sock, address = self.server.accept()
                self.new_client(sock)


def main():
    server = Server()
    server.run()


if __name__ == "__main__":
    main()
