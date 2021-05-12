import argparse
import socket
import ssl
import threading
import select
import time

# TODO change defaults
ipDest = socket.gethostname() #'AWS' 52.53.221.224
portDest = 9999
selfSock = None
running = True
serverListenerThread = None
inputListenerThread = None
FORMAT = "utf-8"
bufferSize = 2048
end = False


def main():
    global selfSock
    global serverListenerThread
    global inputListenerThread
    global wrappedSocket
    # Setup socket as TCP and ipv4
    selfSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    wrappedSocket = ssl.wrap_socket(selfSock, cert_reqs=ssl.CERT_NONE)

    # Connect to the server
    wrappedSocket.connect((ipDest, portDest))

    serverListenerThread = threading.Thread(target=serverListener, daemon=True)
    serverListenerThread.start()

    while (running):
        msg = input()
        if len(msg) >= 2048:
            print('Please limit your message to less than 2048 characters')
        else:
            send(msg)

def serverListener():
    global running
    global wrappedSocket
    global end
    while running:
        wrappedSocket.setblocking(0)
        ready = select.select([wrappedSocket], [], [], 0.00001)
        if ready[0]:
            msg = wrappedSocket.recv(bufferSize)
            fullMsg = msg.decode(FORMAT)
            while not fullMsg.find("\0"):
                msg = wrappedSocket.recv(bufferSize)
                fullMsg += msg.decode(FORMAT)

            if len(fullMsg) > 0:
                print(fullMsg)
    
    end = True

def send(msg):
    # LOOKAT Always send the message?
    global wrappedSocket

    totalSent = 0
    dataToSend = bytes(msg + "\0", FORMAT)
    while totalSent < len(dataToSend):
        sent = wrappedSocket.send(dataToSend[totalSent:])
        if sent == 0:
            # socket closed on us.
            print("ERR: Socket closed! Shutting down.")
            shutDown()
        totalSent += sent
        
    if msg.strip().lower().replace(" ","") == "logout()":
        shutDown()


def shutDown():
    global running
    global wrappedSocket
    global end
    running = False
    
    while True: # give threads time to finish
        if end:
            break 

    wrappedSocket.close()  # Close socket to server 
    
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
