import argparse
import socket
import ssl
import threading
import select
import time
from colorama import Fore

# TODO change defaults
ipDest = "ec2-54-67-19-25.us-west-1.compute.amazonaws.com"  # socket.gethostname()  # ec2-54-67-19-25.us-west-1.compute.amazonaws.com
portDest = 9999
selfSock = None
running = True
serverListenerThread = None
inputListenerThread = None
FORMAT = "utf-8"
bufferSize = 2048


def main():
    global selfSock
    global serverListenerThread
    global inputListenerThread

    # Make SSL Context depending if we're running from server or not.
    sslContext = None
    if ipDest != socket.gethostname():
        print(f"{Fore.YELLOW}Recognized that client is attempting connection with outside server.{Fore.RESET}")
        sslContext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)  # PROTOCOL_TLS_CLIENT automatically sets CERT_REQUIRED and check_hostname
        sslContext.load_verify_locations(cafile="./KEYS/server.public.pem")
    else:
        # THIS IS ONLY FOR TESTING!
        print(f"{Fore.RED}Client only connecting to self. Ignoring cert validations.{Fore.RESET}")
        sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)  # Don't want to check hostname, since cert won't match right now.

    # Setup socket as ipv4 and TCP.
    selfUnwrappedSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Wrap socket in SSL context.
    selfSock = sslContext.wrap_socket(selfUnwrappedSock, server_hostname=ipDest)

    # Connect to the server
    selfSock.connect((ipDest, portDest))

    print(selfSock.getpeercert())

    print(f"Connected to {ipDest}, {selfSock.getpeername()}")

    # Get and pring cipher details
    ciph = selfSock.cipher()
    if ciph[1] == "TLSv1.2" or ciph[1] == "TLSv1.3":
        print(f"Using cipher: {ciph[0]}, {Fore.GREEN}Protocol: {ciph[1]}{Fore.RESET}, #Secrets: {ciph[2]}.")

    # Start the serverListener method on a new thread.
    serverListenerThread = threading.Thread(target=serverListener, daemon=True)
    serverListenerThread.start()

    while (running):
        try:
            msg = input()
        except:
            print(f"{Fore.RED}Forcing shutdown!{Fore.RESET}")
            selfSock.shutdown(socket.SHUT_RD)
            exit()

        if len(msg) >= 2048:
            print('Please limit your message to less than 2048 characters')
        else:
            send(msg)


def serverListener():
    global running
    global selfSock
    while running:
        selfSock.setblocking(0)
        ready = select.select([selfSock], [], [], 0.00001)
        if ready[0]:
            try:
                msg = selfSock.recv(bufferSize)
            except ssl.SSLWantReadError as e:
                continue
            except:
                print(f"{Fore.RED}Problem with listening to server! Shutting down!{Fore.RESET}")
                selfSock.close()
                exit()

            fullMsg = msg.decode(FORMAT)
            while not fullMsg.find("\0"):
                try:
                    msg = selfSock.recv(bufferSize)
                except ssl.SSLWantReadError as e:
                    continue
                except:
                    print(f"{Fore.RED}Problem with listening to server! Shutting down!{Fore.RESET}")
                    selfSock.close()
                    exit()

                fullMsg += msg.decode(FORMAT)

            if len(fullMsg) > 0:
                print(fullMsg)


def send(msg):
    global selfSock

    totalSent = 0
    dataToSend = bytes(msg + "\0", FORMAT)
    while totalSent < len(dataToSend):
        try:
            sent = selfSock.send(dataToSend[totalSent:])
        except:
            exit()

        if sent == 0:
            # socket closed on us.
            print("ERR: Socket closed! Shutting down.")
            shutDown()
        totalSent += sent

    if msg.strip().lower().replace(" ", "") == "logout()":
        shutDown()


def shutDown():
    global running
    global selfSock
    running = False

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
