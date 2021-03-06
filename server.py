import argparse
import socket
import ssl
import threading
import select
import time
from queue import Queue
from colorama import Fore

ipHost = socket.gethostname()
portHost = 9999
clientCapacity = 10
FORMAT = "utf-8"
threads = []
clientSocks = []
names = {}
messageDatabaseQueue = Queue(maxsize=50)
bufferSize = 2048
running = True
serverSock = None
sslContext = None


def main():
    global sslContext
    global serverSock
    global ipHost
    global portHost

    # Setup SSLContext as TLS server.
    sslContext = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # Give public and private keys to the SSLContext
    sslContext.load_cert_chain(certfile="./KEYS/server.public.pem", keyfile="./KEYS/server.private.key")

    # Create the socket with TCP and ipv4
    serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to a hostID and port
    serverSock.bind((ipHost, portHost))

    # Start listening on the socket for connections
    print("Listening to port", portHost, " on ", ipHost, " using IP: ", socket.gethostbyname(ipHost))
    serverSock.listen(clientCapacity)  # who knows. they could all connect at the same time?

    # Start thread to listen for clients.
    thread1 = threading.Thread(target=listen, daemon=True)
    thread1.start()

    while running:
        try:
            x = input()
        except:
            print(f"{Fore.RED}Forcing a quick shutdown!{Fore.RESET}")
            shutDown()

        if x.strip().lower() == "exit" or x == "shutdown":
            shutDown()


def handleClientDisconnect(clientSock):
    global names
    if clientSock in names:
        del names[clientSock]
    clientSocks.remove(clientSock)
    clientSock.close()
    exit()


def handleClient(clientSock, clientAddr):
    global names
    names[clientSock] = createName(clientSock)  # Get a name from the client

    # Print logging stuff for everyone.
    print(f"{Fore.BLUE}{names[clientSock]}{Fore.RESET} has connected from {clientAddr}. We have {len(names)} client in the room.")
    broadcastMessage(f"{Fore.BLUE}{names[clientSock]}{Fore.RESET} has connected to the server. We have {len(names)} client in the room.", clientSock)
    print(f"Updating {Fore.BLUE}{names[clientSock]}{Fore.RESET} with all previous messages in message database. We have {sendFullDatabase(clientSock)} messages.")

    # Loop for lifetime of server and client.
    while running:
        clientSock.setblocking(0)
        ready = select.select([clientSock], [], [], 0.00001)
        if ready[0]:
            # Handle the client closing the socket abruptly.
            try:
                msg = clientSock.recv(bufferSize)

            except:
                if clientSock.fileno() != -1:
                    print(f"{Fore.RED}Client: {clientAddr} has closed their socket abruptly.{Fore.RESET}")
                    broadcastMessage(f"{Fore.YELLOW}{names.pop(clientSock)}{Fore.RESET} has been disconnected. We have {len(clientSocks)-1} client(s) in the room.", clientSock)
                    handleClientDisconnect(clientSock)
                else:
                    print(f"{Fore.CYAN}Client socket: {clientAddr} has been closed by server.{Fore.RESET}")

            fullMsg = msg.decode(FORMAT)

            # If the msg is empty:
            if msg == b'\x00':
                continue

            while not fullMsg.find("\0"):
                msg = clientSock.recv(bufferSize)
                fullMsg += msg.decode(FORMAT)

            if len(fullMsg) > 0:
                print(f"{names[clientSock]} said: {fullMsg}")
                # Handle clients logging out with "logout()"
                if fullMsg.replace(" ", "") == "logout()\0":
                    broadcastMessage(f"{Fore.YELLOW}{names.pop(clientSock)}{Fore.RESET} has logged out. We have {len(clientSocks)-1} client(s) in the room.", clientSock)
                    handleClientDisconnect(clientSock)
                    break
                else:
                    fullMsg = Fore.BLUE + names[clientSock] + f"{Fore.RESET}: " + fullMsg
                    broadcastMessage(fullMsg, clientSock)


def broadcastMessage(msg, excludeClient):
    global messageDatabaseQueue
    global names
    dataToSend = ""
    # Speak to Client
    for c in names.keys():
        if c != excludeClient:
            totalSent = 0
            dataToSend = bytes(msg + "\0", FORMAT)
            while totalSent < len(dataToSend):
                try:
                    sent = c.send(dataToSend[totalSent:])
                except:
                    print(f"{Fore.RED}Problem sending data to socket: {c}! Closing faulty client socket.{Fore.RESET}")
                    handleClientDisconnect(c)
                    break

                if sent == 0:
                    # socket closed on us.
                    print(f"ERR: Socket closed on {c.getpeername()}!")
                totalSent += sent

    if messageDatabaseQueue.full():
        messageDatabaseQueue.get()
    messageDatabaseQueue.put(msg)  # Saving to message database


def listen():
    global running
    global clientSocks
    global serverSock
    global threads
    global sslContext
    global names

    while running:
        ready = select.select([serverSock], [], [], 0.00001)
        if ready[0]:
            clientSockUnwrapped, clientAddr = serverSock.accept()
            # No clue why it has to be this way, Python docs just want it wrapped after. https://docs.python.org/3/library/ssl.html#server-side-operation
            clientSock = sslContext.wrap_socket(clientSockUnwrapped, server_side=True)

            clientSocks.append(clientSock)

            clientThread = threading.Thread(target=handleClient, args=(clientSock, clientAddr), daemon=True)
            threads.append(clientThread)
            clientThread.start()


def createName(clientSock):
    global names
    clientSock.send(bytes("Input Username: " + "\0", FORMAT))

    # Handle socket closing early.
    try:
        name = clientSock.recv(bufferSize)
    except:
        print(f"{Fore.RED}Client: {clientSock.getpeername()} has disconnected before sending username.{Fore.RESET}")
        handleClientDisconnect(clientSock)

    return name.decode(FORMAT)


def sendFullDatabase(sock):
    for index, message in enumerate(messageDatabaseQueue.queue):
        ret = sock.sendall(bytes(message, FORMAT))
        if ret != None:
            print(f"{Fore.RED}Problem sending all of message database index: {index} to client!{Fore.RESET}")
            print(f"Problematic message: {message}")
    return len(messageDatabaseQueue.queue)


def shutDown():
    global running

    broadcastMessage(f"{Fore.RED}Server shutting down. Goodbye.{Fore.RESET}", None)

    running = False

    time.sleep(1)  # give threads time to finish
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
