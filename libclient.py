import sys
import selectors
import json
import io
import struct

class Message:
    #starts the value for status
    status = "ON"
    Cwindangle = 0
    Cturbineangle = 0

    #function setting the values of the Message
    def __init__(self, selector, sock, addr, request):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self.request = request
        self._recv_buffer = b""
        self._send_buffer = b""
        self._request_queued = False
        self._jsonheader_len = None
        self.jsonheader = None
        self.response = None

    #determines whether it is a read, write, or read and write event
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
            #pass over it so we can get another chance to read
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError("Peer closed.")


    def _write(self):
        if self._send_buffer:
            #there is something waiting in the send buffer
            try:
                #Should be ready to write
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                #Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                #remove what has just been sent from the buffer
                self._send_buffer = self._send_buffer[sent:]


    def _json_encode(self, obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

    def _json_decode(self, json_bytes, encoding):
        tiow = io.TextIOWrapper(
            io.BytesIO(json_bytes), encoding=encoding, newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    #this creates the message, combining the actual content with the header required, and encoding it correctly
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

    #reads in the response from the 'status' request and updates the turbines values
    def _process_response_json_content(self):
        content = self.response
        result = content.get("result")
        print(f"From Server: {result}")

        if result == "SHUTDOWN: windspeed too high.":
            Message.status = "OFF"
        elif result == "STARTUP: Windspeed OK.":
            Message.status = "ON"
        elif result == "Update turbine bearing to wind direction.":
            temp = Message.Cturbineangle
            Message.Cturbineangle = Message.Cwindangle
            print(f"Updated turbine bearing from {temp} to {Message.Cturbineangle}")

        print("Windmill status: ")
        print(Message.status)


    #calls either read or write depending on the state
    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()

    #seperates up the response so the header length, header, and body can be processed
    def read(self):
        self._read()

        if self._jsonheader_len is None:
            self.process_protoheader()

        if self._jsonheader_len is not None:
            if self.jsonheader is None:
                self.process_jsonheader()

        if self.jsonheader:
            if self.response is None:
                self.process_response()

    def write(self):

        if not self._request_queued:
            #if a request hasnt been queeued
            #create the request and write it to the send buffer
            self.queue_request()

        #calls socket.send() if there is data in the send buffer
        self._write()

        if self._request_queued:
            if not self._send_buffer:
                #Set selector to listen for read events, we're done writing.
                self._set_selector_events_mask("r")


    def close(self):
        print("closing connection to", self.addr)
        try:
            #unregister the socket from the server
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                "error: selector.unregister() exception for",
                f"{self.addr}: {repr(e)}",
            )
        try:
            #close the socket
            self.sock.close()
        except OSError as e:
            print(
                "error: socket.close() exception for",
                f"{self.addr}: {repr(e)}",
            )
        finally:
            # Delete reference to socket object
            self.sock = None

    #encode a request and add it to the send buffer
    def queue_request(self):
        content = self.request["content"]
        content_type = self.request["type"]
        content_encoding = self.request["encoding"]
        req = {
            "content_bytes": self._json_encode(content, content_encoding),
            "content_type": content_type,
            "content_encoding": content_encoding,
        }
        message = self._create_message(**req)
        #appened to buffer
        self._send_buffer += message
        #set so not called again
        self._request_queued = True

    def process_protoheader(self):
        hdrlen = 2
        #if it contains more than just the headerlength only look at the header bit
        if len(self._recv_buffer) >= hdrlen:
            self._jsonheader_len = struct.unpack(
                ">H", self._recv_buffer[:hdrlen]
            )[0]
            #leave the rest of the response in the buffer (minus headerlength)
            self._recv_buffer = self._recv_buffer[hdrlen:]

    def process_jsonheader(self):
        hdrlen = self._jsonheader_len
        if len(self._recv_buffer) >= hdrlen:
            self.jsonheader = self._json_decode(
                self._recv_buffer[:hdrlen], "utf-8"
            )
            self._recv_buffer = self._recv_buffer[hdrlen:]
            for reqhdr in (
                "byteorder",
                "content-length",
                "content-type",
                "content-encoding",
            ):
                if reqhdr not in self.jsonheader:
                    raise ValueError(f'Missing required header "{reqhdr}".')

    def process_response(self):
        content_len = self.jsonheader["content-length"]
        if not len(self._recv_buffer) >= content_len:
            return
        data = self._recv_buffer[:content_len]
        self._recv_buffer = self._recv_buffer[content_len:]
        encoding = self.jsonheader["content-encoding"]
        self.response = self._json_decode(data, encoding)
        self._process_response_json_content()
        # Close when response has been processed
        self.close()
