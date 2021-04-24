import argparse
import socket
import threading

# TODO change defaults
ipDest = socket.gethostname()
portDest = 9999
selfSock = None
running = True
serverListenerThread = None
inputListenerThread = None


def main():
    global selfSock
    global serverListenerThread
    global inputListenerThread
    # Setup socket as TCP and ipv4
    selfSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    selfSock.connect((ipDest, portDest))

    inputListenerThread = threading.Thread(target=inputListener)
    inputListenerThread.start()

    serverListenerThread = threading.Thread(target=serverListener)
    serverListenerThread.start()


def inputListener():
    global running
    while running:
        msg = input()
        send(msg)


def serverListener():
    global running
    global selfSock
    while running:
        msg = selfSock.recv(2048)
        fullMsg = msg.decode("utf-8")
        while not fullMsg.find("\0"):
            msg = selfSock.recv(2048)
            fullMsg += msg.decode("utf-8")

        if len(fullMsg) > 0:
            print(fullMsg)


def send(msg):
    # LOOKAT Always send the message?
    global selfSock

    totalSent = 0
    dataToSend = bytes(msg + "\0", "utf-8")
    while totalSent < len(dataToSend):
        sent = selfSock.send(dataToSend[totalSent:])
        if sent == 0:
            # socket closed on us.
            print("ERR: Socket closed! Shutting down.")
            shutDown()
        totalSent += sent

    if msg == "logout()":
        shutDown()


def shutDown():
    global running
    running = False
    selfSock.close()  # Close socket to server
    serverListenerThread.join()  # Stop listening to the server
    # inputListenerThread.join()  # Stop listening for input

    print("Goodbye!")
    exit()


if __name__ == "__main__":
    requireArgs = False
    # Add args and parse them for ip and port.
    parser = argparse.ArgumentParser(description="Run the client")
    parser.add_argument('-ip', dest="ipAddress", required=requireArgs)
    parser.add_argument('-port', dest="port", required=requireArgs, type=int)
    args = parser.parse_args()

    # If any args set, then overwrite global defaults.
    if args.ipAddress:
        ipDest = args.ipAddress
    if args.port:
        portDest = args.port

    main()
