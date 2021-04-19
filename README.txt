#Project 2: Aoife Igoe, Doan Khuc, Evan Mitchell, Lochlann Hackett

Software Required: We wrote and compiled our code using Python3 on a Windows10 machine. The latest version can be downloaded here "https://www.python.org/downloads/".
        Once downloaded it must be added as a path variable. Instructions on how to do this can be found here "https://geek-university.com/python/add-python-to-the-windows-path/".

1. Set up two three terminals and navigate to the folder containing the 4 code files in each of the CPs.

2. In the first terminal type in "python server.py". You will be prompted with the correct use case of the file. Next
    type in "python server.py 127.0.0.1 65432" You will be notified that the server is now listening.

3. TEST CASES:
        -1: (Incorrect Client arguments) type "python client.py 1" into the second terminal. You will be prompted to enter the correct parameters. The expected dialogue can be seen in Figure 2
            of the report.

        -2: (Angle difference > 2*) type "python client.py 127.0.0.1 65432 store 1 1 30 50 20 1". This will return a 'update turbine bearing to wind direction' status response. The expected
            dialogue can be seen in Figures 3 and 4 of the report.

        -3 (wind speed > 45) type 'python client.py 127.0.0.1 65432 store 1 1 30 30 60 1'. This will immediately give a status response telling the client to shut down, and will
            do so until the wind speed falls below the threshold speed. The expected dialogue can be seen in Figure 5 of the report.

        -4 (Connection between one server and multiple clients) To test this you will need to use all three terminals. Set up one as the server (as in Step 2). Then start the first client in a
            new terminal using: 'python client.py 127.0.0.1 65432 store 1 1 30 40 30 1'.Then start the second client in a new terminal using: 'python client.py 127.0.0.1 65432 store 1 1 30 40 30 2'.
            You will see that both clients will now interact with the server concurrently, with the designation of 1 and 2.  The expected server side dialogue can be seen in Figure 6 of the report,
            showing that there are multiple windmills connecting and being stored in the array.
