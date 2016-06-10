"""Nano Python Server"""

__version__ = "0.3.3"
__author__ = "DefaltSimon"

import socket,sys,threading,json

def excepthook(exctype, value, traceback):
    if exctype == ConnectionResetError:
        print("Client disconnected.")
        return
    else:
        sys.__excepthook__(exctype, value, traceback)
sys.excepthook = excepthook

# Outgoing
hostd, portd = "",420
# Incoming
defclientportd = 421

def gotmsg(user,content,to):
    if not content:
        content = None
    print("Message from " + user + " to " + str(to) + ": " + str(content))

def clientsrequested(user):
    print("{} requested client list.".format(str(user)))

class PythonChat:
    def __init__(self,host,port):
        self.wasconnected = []
        self.users = {}
        self.ips = {}

        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
        self.sock.setblocking(1)

        self.sock.bind((host, port))
        self.sock.listen(5)
    def waitforfirstconn(self):
        while True:
            conn, addr = self.sock.accept()
            self.wasconnected.append(str(addr[0]))

            data = bytes(conn.recv(4096)).decode("utf-8")
            #print("Data: " + data)
            initial = json.loads(data)

            if initial["type"] == "initial":
                self.users[str(addr[0])] = initial["username"]
                self.ips[initial["username"]] = str(addr[0])
            else:
                print("Error: Not an initial connection")
                continue

            conn.send("Nano Server 0.1 OK".encode("utf-8"))
            try:
                currentuser = str(self.users.get(addr[0]))
            except TypeError:
                currentuser = "error"
            print("Connected from " + str(addr[0]) + " (" + currentuser + ")")

            anotherthread = threading.Thread(target=self.waitformsg,args=[conn,addr])
            anotherthread.daemon = True
            anotherthread.start()
    def waitformsg(self,conn1, addr1):
        while True:
            demsg = None
            try:
                msg = bytes(conn1.recv(4096)).decode("utf-8")
                if msg:
                    demsg = json.loads(msg)
                else:
                    continue
                username1 = str(demsg["username"])

                # Beacuse of multiple threads, this checks if the message received should even be processed
                if self.users[addr1[0]] == username1:
                    sock2 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    sock2.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
                    sock2.setblocking(1)

                    if demsg["type"] == "getclients":
                        sock2.connect((addr1[0],defclientportd))
                        raw = json.dumps({"type":"clients","content":self.users}).encode("utf-8")
                        sock2.send(raw)
                        clientsrequested(demsg["username"])
                    elif demsg["type"] == "connectiontest":
                        sock2.connect((addr1[0],defclientportd))
                        raw = ({"type":"connectiontest","content":"ok"})
                        senc = json.dumps(raw).encode("utf-8")
                        sock2.send(senc)
                    elif demsg["type"] == "disconnect":
                        print("{} ({})  disconnected.".format(str(addr1[0]),str(self.users[addr1[0]])))
                        self.users.pop(str(addr1[0]))
                        return
                    if "sendto" in demsg:
                        try:
                            gotmsg(self.users.get(addr1[0]),demsg["content"],demsg["sendto"])
                        except TypeError:
                            gotmsg("somebody",demsg["content"],demsg["sendto"])
                        sock2.connect((self.ips.get(str(demsg["sendto"])),defclientportd))
                        raw = json.dumps({"type":"msg","from":str(demsg["username"]),"content":str(demsg["content"])}).encode("utf-8")
                        sock2.send(raw)
            except ConnectionResetError:
                print("{} ({})  disconnected.".format(str(addr1[0]),str(self.users[addr1[0]])))
                self.users.pop(str(addr1[0]))
                return
    def closesocket(self):
        self.sock.close()
    def getdata(self):
        conn, addr = self.sock.accept()
        data = conn.recv(4096)
        print(data)

print("Nano Chat Server " + __version__ + "\n-------------------------")

# todo Feature: autoconnect from a text file?
#try:
#    with open("friends.txt","r") as file:
#        file = file.readlines()
#        users = {}
#        for c, line in enumerate(file):
#            if line.startswith("#"):
#                continue
#            thing = line.strip("\n").split("::")
#            host1 = thing[0]
#            alias = thing[1]
#            users[host1] = alias
#except IndexError:
#    print("Error while parsing friends.txt, quiting.")
#    exit()


chat = PythonChat(hostd,portd)
chat.waitforfirstconn()