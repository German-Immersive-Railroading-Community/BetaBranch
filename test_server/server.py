#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler

import json
import threading
import functions
import os

#Making a List of IPs from UTR
IPs = ()
for ip in open('UTR_IPs.txt', 'r'):
    IPs.append(str(ip))


class Requests(BaseHTTPRequestHandler):

    ports = functions.ports()
    queue = []

    def __init__(self, request, client_addr, server):
        if os.path.isfile("queue.json"):
            with open("queue.json", "r") as queue_file:
                self.queue = json.load(queue_file)
        super().__init__(request, client_addr, server)

    def do_POST(self):
        try:
            # Get message from main_server
            mess_len = int(self.headers.get("Content-Length"))
            _rfile = self.rfile.read(mess_len)
            req = json.loads(_rfile)
        except:
            print(_rfile)
            self.send_response(400, "Wrong message")
            raise Exception("payload is no json")
        # check content
        if not set(("event", "prNumber", "repo", "modFile")) == set(req.keys()):
            self.send_response(400, "Wrong json structure")
            raise Exception("Wrong json structure")
        if req["prNumber"] == "":
            self.send_response(400, "No pr_number given")
            raise Exception("No pr_number given")

        # do stuff
        port = ""
        if req["event"] == "update":
            port = self.update(req)
        if req["event"] == "remove":
            self.delete(req)
            port = "Server deleted!"
        self.send_response(204, str(port))
        self.end_headers()

    def update(self, req):
        if self.ports.is_port_avail():
            port = self.ports.get_port(f"{req['repo']}-{req['prNumber']}")
            x = threading.Thread(target=functions.create_server, args=(
                port, req['prNumber'], req['repo'], req['modFile']))
            x.start()
        else:
            self.queue.append(req)
            self.update_json()
        return port

    def delete(self, req):
        self.ports.remove_port(f"{req['repo']}-{req['prNumber']}")
        x = threading.Thread(functions.delete_server(req['prNumber'],
                                                     req['repo']))
        x.start()
        self.update_queue()

    def update_queue(self):
        if len(self.queue) > 0:
            self.update(self.queue.pop(0))
            self.update_json()

    def update_json(self):
        with open("queue.json", "w") as queue_file:
            json.dump(self.queue, queue_file)
    
    #GET for UTR checks
    def do_GET(self):
        if str(self.client_address[0]) in IPs:
            self.send_response(200, "OK, Test recieved!")
            self.end_headers()
            print("GET-Test received, sent 200")
        else:
            self.send_response(403, "Forbidden")
            self.end_headers()
            print("IP of Sender not found in List of IPs; 403")

    #HEAD for UTR checks
    def do_HEAD(self):
        if str(self.client_address[0]) in IPs:
            self.send_response(200, "OK, Test recieved!")
            self.end_headers()
            print("HEAD-Test received, sent 200")
        else:
            self.send_response(403, "Forbidden")
            self.end_headers()
            print("IP of Sender not found in List of IPs; 403")


httpd = HTTPServer(('0.0.0.0', 4433), Requests)
# httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
