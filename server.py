import argparse
import socket
import ssl
import threading
import select
import time
from queue import Queue
from Crypto.Cipher import AES

# TODO change defaults
ipHost =  socket.gethostname() #'AWSaddy' 52.53.221.224
portHost = 9999
clientCapacity = 10
FORMAT = "utf-8"
threads = []
clientSocks = []
messageDatabaseQueue = Queue(maxsize = 50)
bufferSize = 2048
running = True
serverSock = None


def main():
    global serverSock
    global wrappedServerSock
    global ipHost
    global portHost
    # Create the socket with TCP and ipv4
    serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    wrappedServerSock = ssl.wrap_socket(serverSock, cert_reqs=ssl.CERT_NONE)
    # Bind the socket to a hostID and port
    wrappedServerSock.bind((ipHost, portHost))
    # Start listening on the socket for connections
    print("listening to port", portHost, " on ", ipHost)
    wrappedServerSock.listen(clientCapacity)  # who knows. they could all connect at the same time?

    thread1 = threading.Thread(target=listen, daemon=True)
    thread1.start()

    while running:
        x = input()
        if x.strip().lower() == "exit" or x == "shutdown":
            shutDown()


def removeFromClientSocksList(clientSock):
    clientSocks.remove(clientSock)


def handleClient(clientSock):
    while running:
        clientSock.setblocking(0)
        ready = select.select([clientSock], [], [], 0.00001)
        if ready[0]:
            msg = clientSock.recv(bufferSize)
            fullMsg = msg.decode(FORMAT)
            while not fullMsg.find("\0"):
                msg = clientSock.recv(bufferSize)
                fullMsg += msg.decode(FORMAT)
            if len(fullMsg) > 0:
                print(f"User {clientSocks.index(clientSock)} said: {fullMsg}")
                if fullMsg.replace(" ","") == "logout()\0":
                    broadcastMessage(f"User {clientSocks.index(clientSock) + 1} has logged out. We have {len(clientSocks) -1} client in the room", clientSock)
                    clientSocks.remove(clientSock)
                    clientSock.close()
                    break
                else:
                    fullMsg = "User " + str(clientSocks.index(clientSock) + 1) + ": " + fullMsg
                    broadcastMessage(fullMsg, clientSock)


def broadcastMessage(msg, excludeClient):
    global messageDatabaseQueue
    global clientSocks
    dataToSend = ""
    #Speak to Client
    for c in clientSocks:
        if c != excludeClient:
            totalSent = 0
            dataToSend = bytes(msg + "\0", FORMAT)
            while totalSent < len(dataToSend):
                sent = c.send(dataToSend[totalSent:])
                if sent == 0:
                    # socket closed on us.
                    print(f"ERR: Socket closed on {c.getpeername()}!")
                totalSent += sent
    if messageDatabaseQueue.full():
        messageDatabaseQueue.get()
    messageDatabaseQueue.put(msg)  # Saving to message database


def listen():
    global running  # idk why this wants the global reference here...
    global clientSocks
    global wrappedServerSock
    global threads
    while running:
        ready = select.select([wrappedServerSock], [], [], 0.00001)
        if ready[0]:
            clientSock, clientAddr = wrappedServerSock.accept()
            clientSocks.append(clientSock)
            print(f"User {clientSocks.index(clientSock)+1} has connected to the server. We have {len(clientSocks) } client in the room")
            broadcastMessage(f"User {clientSocks.index(clientSock)+1} has connected to the server. We have {len(clientSocks)} client in the room",clientSock)
            print(f"Update User {clientSocks.index(clientSock) + 1} all previous messages based on message database. We have {sendFullDatabase(clientSock)} messages")
            clientThread = threading.Thread(target=handleClient, args=(clientSock,), daemon=True)
            threads.append(clientThread)
            clientThread.start()

def sendFullDatabase(sock):
    for index,message in enumerate(messageDatabaseQueue.queue):
        sock.send(bytes(message, FORMAT))
        if index < len(messageDatabaseQueue.queue)-1:
            sock.send(bytes("\n", FORMAT))
    return len(messageDatabaseQueue.queue)

def shutDown():
    global running
    running = False

    time.sleep(1) # give threads time to finish
    for c in clientSocks:
        c.close()

    print("Oyasumi.")
    exit()

def do_encrypt(message):
    obj = AES.new('This is a key123', AES.MODE_CBC, 'This is an IV456')
    ciphertext = obj.encrypt(message)
    return ciphertext


if __name__ == "__main__":
    requireArgs = False
    # Add args and parse them for ip and port.
    parser = argparse.ArgumentParser(description="Run the server")
    parser.add_argument('-ip', dest="ipAddress", required=requireArgs, help="ip address to host from")
    parser.add_argument('-port', dest="port", required=requireArgs, help="port to accept connections from", type=int)
    parser.add_argument("-clients", dest="clients", required=False, help="max number of clients to host", type=int)
    args = parser.parse_args()

    # If any args set, then overwrite global defaults.
    if args.ipAddress:
        ipHost = args.ipAddress
    if args.port:
        portHost = args.port
    if args.clients:
        clientCapacity = args.clients

    main()
