import argparse
import socket
import threading

# TODO change defaults
ipHost = socket.gethostname()
portHost = 9999
clientCapacity = 10

threads = []
clientSocks = []
running = True


def main():
    # Create the socket with TCP and ipv4
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to a hostID and port
    sock.bind((ipHost, portHost))
    # Start listening on the socket for connections
    sock.listen(clientCapacity)  # who knows. they could all connect at the same time?

    thread1 = threading.Thread(target=terminalHandler)
    thread1.start()

    # Listen
    while running:
        clientSock, clientAddr = sock.accept()
        print(f"Client {clientAddr} has connected to the server.")
        clientSocks.append(clientSock)
        clientThread = threading.Thread(target=handleClient, args=(clientSock,))
        threads.append(clientThread)
        clientThread.start()
        pass


def handleClient(clientSock):
    while running:
        msg = clientSock.recv(8)
        fullMsg = msg.decode("utf-8")
        while not fullMsg.find("\0"):
            msg = clientSock.recv(8)
            fullMsg += msg.decode("utf-8")

        if len(fullMsg) > 0:
            print(f"{clientSock.getpeername()}: {fullMsg}")
            if fullMsg == "logout()":
                broadcastMessage(f"Client {clientSock.getpeername()} has logged out.", clientSock)
                clientSock.close()
            else:
                broadcastMessage(fullMsg, clientSock)


def broadcastMessage(msg, excludeClient):
    for x in clientSocks:
        if x != excludeClient:
            x.send(bytes(msg + "\0", "utf-8"))


def terminalHandler():
    global running  # idk why this wants the global reference here...
    while running:
        x = input()
        if x == "exit" or x == "shutdown":
            running = False
            for t in threads:
                t.join()

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
