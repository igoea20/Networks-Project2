
import sys
import socket
import selectors
import traceback

#used for simulating time delay
import time
#import the client message class
import libclient

#to simulate random wind conditions
import random

sel = selectors.DefaultSelector()

#input should be: host, socket, request, x co-ord, y co-ord, windangle, turbineangle, windspeed, windmill number
#python client.py 127.0.0.1 65432 [store or status] [x] [y] [windangle] [turbine angle]] [windspeed] [windmill number]
#python client.py 127.0.0.1 65432 store 1 1 30 50 40 1


def create_request(action, x, y, windangle, turbineangle, windspeed, windmill, status):
    #we are assuming only json text is being sent
    return dict(
            type="text/json",
            encoding="utf-8",
            content=dict(action=action, x=x, y=y, windangle=windangle,turbineangle=turbineangle, windspeed=windspeed, windmill=windmill, status=status),
        )


def start_connection(host, port, request):
    addr = (host, port)
    print("\nstarting connection to", addr)
    #tcp socket created for the server connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #set to non blocking
    sock.setblocking(False)
    sock.connect_ex(addr)
    #socket is initially set for both read and write events
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    #message object created using request dictionary
    message = libclient.Message(sel, sock, addr, request)
    #message object is associated with the socket
    sel.register(sock, events, data=message)

if len(sys.argv) != 10: #these are read from the command line
    print("usage:", sys.argv[0], "<host> <port> <action> <x> <y> <windangle> <turbineangle> <windspeed> <windmill>")
    sys.exit(1)

#load in the arguments to the client
host, port = sys.argv[1], int(sys.argv[2])
action,x, y, windangle, turbineangle, windspeed, windmill = sys.argv[3], sys.argv[4], sys.argv[5], int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8]), sys.argv[9]

#store the angles
libclient.Message.Cwindangle = windangle
libclient.Message.Cturbineangle = turbineangle

try:
    #for x in range(5):
    while True:
        time.sleep(3)
        #status = libraryinstance.status
        status = libclient.Message.status
        print(libclient.Message.Cwindangle)
        print(libclient.Message.Cturbineangle)
        windangle = libclient.Message.Cwindangle
        turbineangle = libclient.Message.Cturbineangle

        request = create_request(action,x, y, windangle, turbineangle, windspeed, windmill, status)
        #a request is made for the server, containing the clients data inputs
        start_connection(host, port, request)
        try:
            while True:
                events = sel.select(timeout=1)
                for key, mask in events:
                    message = key.data
                    try:
                        message.process_events(mask)
                    #any exceptions raised by the message class are caught here
                    except Exception:
                        print(
                            "main: error: exception for",
                            f"{message.addr}:\n{traceback.format_exc()}",
                        )
                        #nb removes socket from being monitored
                        message.close()
                # Check for a socket being monitored to continue.
                if not sel.get_map():
                    break
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")

        #swaps the request type to vary the data
        if action == "status":
            action = "store"
        else:
            action = "status"

            #simulates random wind speeds, wind angles, only do it when request is status
            randomnumber = random.randint(-2, 2)
            randomnumber1 = random.randint(-1, 1)
            windspeed = windspeed + randomnumber
            libclient.Message.Cwindangle = libclient.Message.Cwindangle + randomnumber1
            if abs(windangle-turbineangle) > 1:
                turbineangle = windangle


finally:
    sel.close()
