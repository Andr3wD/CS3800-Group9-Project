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
    
    
    # Make SSL Context depending if we're running from server or not.
    sslContext = None
    if ipDest != socket.gethostname():
        print("Recognized that client is attempting connection with outside server.")
        sslContext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)  # PROTOCOL_TLS_CLIENT automatically sets CERT_REQUIRED and check_hostname
        sslContext.load_verify_locations(cafile="./KEYS/server.public.pem")
    else:
        # THIS IS ONLY FOR TESTING!
        print("Client only connecting to self. Ignoring cert validations.")
        sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)  # Don't want to check hostname, since cert won't match right now.
    
    # Probably just remove. client doesn't need cert.
    # sslContext.load_cert_chain(certfile="./KEYS/client.public.pem", keyfile="./KEYS/client.private.key")
    
    # Setup socket as ipv4 and TCP.
    selfUnwrappedSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Wrap socket in SSL context.
    selfSock = sslContext.wrap_socket(selfUnwrappedSock, server_hostname=ipDest)

    # Connect to the server
    selfSock.connect((ipDest, portDest))
    
    print(f"Connected to {ipDest}, {selfSock.getpeername()}")

    # Start the serverListener method on a new thread.
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
    global selfSock
    global end
    while running:
        selfSock.setblocking(0)
        ready = select.select([selfSock], [], [], 0.00001)
        if ready[0]:
            msg = selfSock.recv(bufferSize)
            fullMsg = msg.decode(FORMAT)
            while not fullMsg.find("\0"):
                msg = selfSock.recv(bufferSize)
                fullMsg += msg.decode(FORMAT)

            if len(fullMsg) > 0:
                print(fullMsg)
    
    end = True

def send(msg):
    # LOOKAT Always send the message?
    global selfSock

    totalSent = 0
    dataToSend = bytes(msg + "\0", FORMAT)
    while totalSent < len(dataToSend):
        sent = selfSock.send(dataToSend[totalSent:])
        if sent == 0:
            # socket closed on us.
            print("ERR: Socket closed! Shutting down.")
            shutDown()
        totalSent += sent
        
    if msg.strip().lower().replace(" ","") == "logout()":
        shutDown()


def shutDown():
    global running
    global selfSock
    global end
    running = False
    
    while True: # give threads time to finish
        if end:
            break 

    selfSock.close()  # Close socket to server
    
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
