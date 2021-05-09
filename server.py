import argparse
import socket
import threading
import select
import time

# TODO change defaults
ipHost = ''
portHost = 9999
clientCapacity = 10
sock = None

threads = []
clientSocks = []
running = True


def main():
    global sock
    # Create the socket with TCP and ipv4
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to a hostID and port
    sock.bind((ipHost, portHost))
    # Start listening on the socket for connections
    sock.listen(clientCapacity)  # who knows. they could all connect at the same time?

    thread1 = threading.Thread(target=listen, daemon=True)
    thread1.start()

    while running:
        x = input()
        if x.strip().lower() == "exit" or x == "shutdown":
            shutDown()
    


def handleClient(clientSock):
    while running:
        clientSock.setblocking(0)
        ready = select.select([clientSock], [], [], 0.00001)
        if ready[0]:
            msg = clientSock.recv(2048)
            fullMsg = msg.decode("utf-8")
            while not fullMsg.find("\0"):
                msg = clientSock.recv(2048)
                fullMsg += msg.decode("utf-8")

            if len(fullMsg) > 0:
                print(f"{clientSock.getpeername()}: {fullMsg}")
                if fullMsg.replace(" ", "") == "logout()\0":
                    broadcastMessage(f"Client {clientSock.getpeername()} has logged out.", clientSock)
                    clientSock.close()
                    clientSocks.remove(clientSock)
                    break
                else:
                    broadcastMessage(fullMsg, clientSock)


def broadcastMessage(msg, excludeClient):
    for c in clientSocks:
        if c != excludeClient:

            totalSent = 0
            dataToSend = bytes(msg + "\0", "utf-8")
            while totalSent < len(dataToSend):
                sent = c.send(dataToSend[totalSent:])
                if sent == 0:
                    # socket closed on us.
                    print(f"ERR: Socket closed on {c.getpeername()}!")
                totalSent += sent


def listen():
    global running  # idk why this wants the global reference here...
    global sock
    global clientSocks
    global threads
    while running:
        ready = select.select([sock], [], [], 0.00001)
        if ready[0]:
            clientSock, clientAddr = sock.accept()
            print(f"Client {clientAddr} has connected to the server.")
            broadcastMessage(f"Client {clientAddr} has connected to the server.", clientSock)
            clientSocks.append(clientSock)
            clientThread = threading.Thread(target=handleClient, args=(clientSock,), daemon=True)
            threads.append(clientThread)
            clientThread.start()


def shutDown():
    global running
    running = False

    time.sleep(1) # give threads time to finish
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
