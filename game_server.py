import socket,threading
import select
import json
PORT=5050
IP=socket.gethostbyname(socket.gethostname())
ADDR=(IP,PORT)
server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind(ADDR)
conns=[]
def handleclient(conn,addr):
    conns.append(conn)
    while True:
        read,write,error=select.select(conns,[],[])
        for client in read:
            handle_msg(client)
        

def mysend(s, msg):
    # append size to message and send it
    SIZE_SPEC=5
    msg = ('0' * SIZE_SPEC + str(len(msg)))[-SIZE_SPEC:] + str(msg)
    msg = msg.encode()
    total_sent = 0
    while total_sent < len(msg):
        sent = s.send(msg[total_sent:])
        if sent == 0:
            print('server disconnected')
            break
        total_sent += sent


def myrecv(s):
    # receive size first
    size = ''
    SIZE_SPEC=5
    while len(size) < SIZE_SPEC:
        text = s.recv(SIZE_SPEC - len(size)).decode()
        if not text:
            print('disconnected')
            return('')
        size += text
    print(size)
    size = int(size)
    # now receive message
    msg = ''
    while len(msg) < size:
        text = s.recv(size-len(msg)).decode()
        if text == b'':
            print('disconnected')
            break
        msg += text
    #print ('received '+message)
    return (msg)

def handle_msg(from_sock):
    print('mysend',mysend)
    msg=myrecv(from_sock)
    print(msg)
    if len(msg)>0:
        msg=json.loads(msg)
        for client in conns:
            if client!=from_sock:
                print('message sent to',clinet)
                mysend(client,json.dumps({'message':msg['message']}))

def start():
    server.listen()
    print('SERVER LISTENING')
    while True:
        conn,addr=server.accept()
        threading.Thread(target=handleclient,args=(conn,addr)).start()
        print('CLIENT CONNECTED')
        '''read,write,error=select.select(conns,[],[])
        for client in read:
            handle_msg(client)'''
start()