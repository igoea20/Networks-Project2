
import sys
import socket
import selectors
import traceback

#used for simulating time delay for satellites
import time
#import the client message class
import libclient

#to simulate random wind conditions
import random

sel = selectors.DefaultSelector()

#to start client type python client.py 127.0.0.1 65432 store 30 3

#python client.py 127.0.0.1 65432 store 30 1 1 3 3 3 40 117
#python client.py 127.0.0.1 65432 [store or status] [value] [x] [y] [vx] [vy] [vz] [windspeed] [windmill number]
#input should be: host, socket, request, windspeed, windmill

def create_request(action, value, x, y, vx, vy, vz, windspeed, windmill):
    #we are assuming only json text is being sent
    return dict(
            type="text/json",
            encoding="utf-8",
            content=dict(action=action, value=value,x=x, y=y, vx=vx, vy=vy, vz=vz, windspeed=windspeed, windmill=windmill),
        )


def start_connection(host, port, request):
    addr = (host, port)
    print("starting connection to", addr)
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

if len(sys.argv) != 12: #these are read from the command line
    print("usage:", sys.argv[0], "<host> <port> <action> <value> <x> <y> <vx> <vy> <vz>  <windspeed> <windmill>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
action, value, x, y, vx, vy, vz, windspeed, windmill = sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8], sys.argv[9], int(sys.argv[10]), sys.argv[11]

#get the client to repeatedly connect to the server
try:
    #for x in range(5):
    while True:
        time.sleep(3)
        #dictionary created representing request
        request = create_request(action, value, x, y, vx, vy, vz, windspeed, windmill)
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

        #swaps the value for action
        if action == "status":
            action = "store"
        else:
            action = "status"

            #simulates random wind speeds, only do it when status changes
            randomnumber = random.randint(-2, 3)
            windspeed = windspeed + randomnumber
            

finally:
    sel.close()
