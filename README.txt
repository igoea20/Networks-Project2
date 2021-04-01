#Project 1: Aoife Igoe and Evan Mitchell

Software Required: We wrote and compiled our code using Python3 on a Windows10 machine. The latest version can be downloaded here "https://www.python.org/downloads/". 
        Once downloaded it must be added as a path variable. Instructions on how to do this can be found here "https://geek-university.com/python/add-python-to-the-windows-path/".

1. Set up two Command Prompts and navigate to the folder containing the 4 code files in each of the CPs.

2. In the first Command Prompt type in "python server.py". You will be prompted with the correct use case of the file. Next
    type in "python server.py "" 65432". You will be notified that the server is now listening.

3. In the second Command Prompt type in "python client.py". You will be prompted with the correct use case of the file, including
    the inputs required.
        -TEST CASE a (standard): Type "python client.py 127.0.0.1 65432 1 2 3 45" This will connect to host '127.0.0.1', port 65432.
          The server will see the client connection and handshaking will ensue. The co-ordinates X:1, Y:2, Z:3 and Temperature 45* will
          be saved on the server and echoed back to the client after a 560ns delay (to mimic satellite delay).

        -TEST CASE b (negative inputs): Type "python client.py 127.0.0.1 65432 -40 2 -30 20" This will connect to host '127.0.0.1',
          port 65432. The server will see the client connection and handshaking will ensue. The co-ordinates X:-40, Y:2, Z:-30 and
          Temperature 20* will be saved on the server and echoed back to the client after a 560ns delay (to mimic satellite delay).

        -TEST CASE c (different ports): Close the first Command Prompt and repeat steps 1 and 2, but this time type 65431 as the port
          number. Then go to the second Command Prompt and type "python client.py 127.0.0.1 65431 -40 2 -30 20" This will connect
          to host '127.0.0.1', port 65431. The server will see the client connection and handshaking will ensue. The co-ordinates X:-40,
          Y:2, Z:-30 and Temperature 20* will be saved on the server and echoed back to the client after a 560ns delay (to mimic satellite delay).
