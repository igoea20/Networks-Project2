import sys
import selectors
import json
import io
import struct

#for delay simulation
import time

request_search = {
    "morpheus": "Follow the white rabbit. \U0001f430",
}

#the methods in this class appear in the order in which processing
#takes place for a message

class Message:
    #constructor
    def __init__(self, selector, sock, addr, windmillArray):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self._recv_buffer = b""
        self._send_buffer = b""
        self._jsonheader_len = None
        self.jsonheader = None
        self.request = None
        self.response_created = False
        self.windmillArray = windmillArray  #this is the windmill array

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {repr(mode)}.")
        self.selector.modify(self.sock, events, data=self)

    def _read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(4096)
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError("Peer closed.")

    def _write(self):
        if self._send_buffer:

        #    print("sending", repr(self._send_buffer), "to", self.addr)
            try:
                # Should be ready to write
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]
                # Close when the buffer is drained. The response has been sent.
                if sent and not self._send_buffer:
                    self.close()


    def _json_encode(self, obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

    def _json_decode(self, json_bytes, encoding):
        tiow = io.TextIOWrapper(
            io.BytesIO(json_bytes), encoding=encoding, newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    def _create_message(
        self, *, content_bytes, content_type, content_encoding
    ):
        jsonheader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_bytes),
        }
        jsonheader_bytes = self._json_encode(jsonheader, "utf-8")
        message_hdr = struct.pack(">H", len(jsonheader_bytes))
        message = message_hdr + jsonheader_bytes + content_bytes
        return message

    def _create_response_json_content(self): #creates the response for the client

        action = self.request.get("action")

        if action == "store":
            current = self.request.get("windmill")
            store_speed = self.request.get("windspeed")
            maxspeed = int(store_speed)
            if maxspeed > 45:
                query4 = "SHUTDOWN: windspeed too high."
            else:
                query4 = "Windspeed OK."
            content = {"result": f'Stored data "{store_speed}". {query4}.'}
            self.windmillArray[current] = store_speed #gets the speed and updates the array with it at this point
        elif action == "status":
            val = self.request.get("value") #takes the value passed and saves it
            query = self.request.get("x") #takes the value passed and saves it
            query1 = self.request.get("y") #takes the value passed and saves it
            query5 = self.request.get("vx")
            query6 = self.request.get("vy")
            query7 = self.request.get("vz")
            query2 = self.request.get("windspeed") #takes the value passed and saves it
            #maxspeed = int( query2)
            maxspeed = query2
            query3 = self.request.get("windmill") #takes the value passed and saves it
            # if maxspeed > 45:
            #     query4 = "SHUTDOWN: windspeed too high."
            # else:
            #     query4 = "Windspeed OK."

            # #content = {"result": f'The XYZ coordinates are X{query} Y{query1} Z{query2}. The temperature is {query3}'}
            # answer = request_search.get(val) or f'No match for "{query}".'
            # #content = {"result": answer}
            # content = {"result": f'Windmill {query3}: The XYZ coordinates are X{query} Y{query1}.Windspeed: {query2} km/h. {query4} Update turbine bearing: X vector: {query5} Y vector: {query6} Status: {answer}'}
            answer = request_search.get(val) or f'No match for "{query}".'
            if maxspeed > 45:
                query4 = "SHUTDOWN: windspeed too high."
                content = {"result": f"SHUTDOWN: windspeed too high."}
            else:
                query4 = "Windspeed OK."
                content = {"result": f'Windmill {query3} status update:\n The XYZ coordinates are X{query} Y{query1}.Windspeed: {query2} km/h. {query4} Update turbine bearing: X vector: {query5} Y vector: {query6} Status: {answer}'}
        else:
            content = {"result": f'Error: invalid action "{action}".'}
        content_encoding = "utf-8"
        response = {
            "content_bytes": self._json_encode(content, content_encoding),
            "content_type": "text/json",
            "content_encoding": content_encoding,
        }
        return response


    #called in app-server when events are ready
    #either reads or writes the message
    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()

    #same as client version
    def read(self):
        #calls socket.revc() to read data from socket and store it in a receive _send_buffer
        self._read()
        #three state checks and process methods for each message component
        if self._jsonheader_len is None: #fixed length header
            self.process_protoheader()

        if self._jsonheader_len is not None:
            if self.jsonheader is None: #json header
                self.process_jsonheader()

        if self.jsonheader:
            if self.request is None: #content
                self.process_request()

    def write(self):
        if self.request:    #if a request exists and a response hasnt been created
            if not self.response_created:
                self.create_response() #writes response to the send buffer

        self._write() #this calls socket.send() if data is in the send buffer

    def close(self):
        print("closing connection to", self.addr)
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                "error: selector.unregister() exception for",
                f"{self.addr}: {repr(e)}",
            )

        try:
            self.sock.close()
        except OSError as e:
            print(
                "error: socket.close() exception for",
                f"{self.addr}: {repr(e)}",
            )
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

    #when the server has read >=2bytes the fixed-length header can be processed
    def process_protoheader(self):
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen: #if >=2bytes
            self._jsonheader_len = struct.unpack( #read the value and decode it
                ">H", self._recv_buffer[:hdrlen] #store the header length in _jsonheader_len
            )[0]
            self._recv_buffer = self._recv_buffer[hdrlen:] #once it is processed remove it from the receive buffer

#when the server has read >=header length of bytes the json header can be processed
    def process_jsonheader(self):
        hdrlen = self._jsonheader_len
        if len(self._recv_buffer) >= hdrlen:
            self.jsonheader = self._json_decode(  #decodes and deserialises the json header into a dictionary
                self._recv_buffer[:hdrlen], "utf-8"
            )
            #removed from the buffer (in format utf-8)
            self._recv_buffer = self._recv_buffer[hdrlen:]
            for reqhdr in ( #these are the values required in the header
                "byteorder",
                "content-length",
                "content-type",
                "content-encoding",
            ):
                if reqhdr not in self.jsonheader:
                    raise ValueError(f'Missing required header "{reqhdr}".')

#this is the actual content of the message, descirbed by the json header
    def process_request(self):
        content_len = self.jsonheader["content-length"]
        if not len(self._recv_buffer) >= content_len:
            return
        #when content-length bytes are in the buffer it is ready to process
        data = self._recv_buffer[:content_len] #save message content to data
        self._recv_buffer = self._recv_buffer[content_len:] #remove content from the buffer

        encoding = self.jsonheader["content-encoding"] #decode and deserialise it
        self.request = self._json_decode(data, encoding)
        print("received request", repr(self.request), "from", self.addr)
        # Set selector to listen for write events, we're done reading.
        self._set_selector_events_mask("w")

#when the socket is writable this is called from write()
    def create_response(self):
        response = self._create_response_json_content()
        message = self._create_message(**response)
        self.response_created = True #so not called again
        self._send_buffer += message #message appended to the send buffer
