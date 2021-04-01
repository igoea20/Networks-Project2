
import sys
import socket
import selectors
import traceback

#used for simulating time delay for satellites
import time
#this contains the server message class
import libserver

sel = selectors.DefaultSelector()

#to start for me it was python app-server.py "" 65432

#when a client connection is accepted, a message object is created (socket is ready to read)
def accept_wrapper(sock):
    conn, addr = sock.accept()
    print("accepted connection from", addr)
    #blocking is set to false here
    conn.setblocking(False)
    #create a message object
    message = libserver.Message(sel, conn, addr)
    #associate message object with a socket thats monitored for events (set to just read initially)
    sel.register(conn, selectors.EVENT_READ, data=message)

#if user hasnt entered enough arguments, prompt them
if len(sys.argv) != 3:
    print("usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

#this delay simulates the data arriving to the server (ground to satellite to server)
time.sleep(0.56)
#read from command line, use empty string for host to listen on all interfaces
host, port = sys.argv[1], int(sys.argv[2])
#creates a tcp socket
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Avoid bind() exception: OSError: [Errno 48] Address already in use
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
lsock.bind((host, port))
lsock.listen()
print("listening on", (host, port))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True: #catches errors so server stays up and running
        #blocks until events ready, is responsible for process_events being called indirectly
        events = sel.select(timeout=None)
        #when events are ready on the socket
        for key, mask in events:
            if key.data is None:
                #accept the client connection
                accept_wrapper(key.fileobj)
            else:
                #create a message object
                message = key.data
                try:
                    message.process_events(mask)
                except Exception:
                    print(
                        "main: error: exception for",
                        f"{message.addr}:\n{traceback.format_exc()}",
                    )
                    message.close()

except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()
