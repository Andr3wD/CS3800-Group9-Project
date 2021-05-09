import argparse
import socket
import threading

# TODO change defaults
ipHost = socket.gethostname()
portHost = 5050
clientCapacity = 10
FORMAT = "utf-8"
threads = []
clientSocks = []
bufferSize = 2048
running = True


def main():
    # Create the socket with TCP and ipv4
    serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to a hostID and port
    serverSock.bind((ipHost, portHost))
    # Start listening on the socket for connections
    print("listening to port", portHost, " on ", ipHost)
    serverSock.listen(clientCapacity)  # who knows. they could all connect at the same time?

    thread1 = threading.Thread(target=terminalHandler)
    thread1.start()

    # Listen
    while running:
        clientSock, clientAddr = serverSock.accept()
        # Speak to server
        print(f"Client {clientAddr} has connected to the server. We have {len(clientSocks) + 1} client in the room")
        broadcastMessage(f"Client {clientAddr} has connected to the server. We have {len(clientSocks) + 1} client in the room", clientSock)
        clientSocks.append(clientSock)
        clientThread = threading.Thread(target=handleClient, args=(clientSock,))
        threads.append(clientThread)
        clientThread.start()


def removeFromClientSocksList(clientSock):
    clientSocks.remove(clientSock)


def handleClient(clientSock):
    while running:

        msg = clientSock.recv(bufferSize)
        fullMsg = msg.decode(FORMAT)

        while not fullMsg.find("\0"):
            msg = clientSock.recv(bufferSize)
            fullMsg += msg.decode(FORMAT)

        if len(fullMsg) > 0:
            print(f"{clientSock.getpeername()}: {fullMsg}")
            if fullMsg == "logout()\0":
                broadcastMessage(f"Client {clientSock.getpeername()} has logged out. We have {len(clientSocks)} client in the room", clientSock)
                threading.currentThread.join()
                clientSock.close()
                removeFromClientSocksList(clientSock)
            else:
                broadcastMessage(fullMsg, clientSock)


def broadcastMessage(msg, excludeClient):

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

def terminalHandler():
    global running  # idk why this wants the global reference here...
    while running:
        x = input()
        if x == "exit" or x == "shutdown":
            shutDown()


def shutDown():
    global running
    running = False
    for t in threads:
        t.join()

    for c in clientSocks:
        c.close()

    print("Oyasumi.")
    exit()


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
