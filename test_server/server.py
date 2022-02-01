#!/usr/bin/env python3
import json
import logging as lg
import os
import threading
from datetime import datetime as dt
from http.server import BaseHTTPRequestHandler, HTTPServer

from decouple import config

import functions

today = dt.today().strftime('%Y-%m-%d')
logdir = str(config("logDir"))
logname = f'{logdir}/{today}.log'
if not os.path.exists(logdir):
    os.mkdir(logdir)
open(logname, 'a').close()
log_level = str(config('log_level')).upper()
lg.basicConfig(filename=logname, level=log_level,
               format='%(asctime)s : %(message)s', datefmt='%I:%M:%S')

lg.info("Starting up")

# Making a List of IPs from UTR
IPs = []
for ip in open('UTR_IPs.txt', 'r'):
    IPs.append(str(ip.replace('\n', '')))
lg.debug("Made list of IPs from UTR")

# Start the existing servers
with open("ports.json", "r") as file:
    data = json.load(file)
server_folder = config("server_folder")
for identifier in data["server_ports"].keys():
    os.system(f"screen -S {identifier} -X quit")
    os.system(
        f"screen -dmS {identifier} bash -c 'cd {server_folder}/{identifier};\
         ./auto-restart.sh'")
lg.info("Started the existing servers")


class Requests(BaseHTTPRequestHandler):

    ports = functions.ports()
    queue = []

    def __init__(self, request, client_addr, server):
        if os.path.isfile("queue.json"):
            with open("queue.json", "r") as queue_file:
                self.queue = json.load(queue_file)
                lg.debug("Loaded queue.json")
        while (len(self.ports.avail_ports) > 0 and len(self.queue) > 0):
            self.update_queue()
        super().__init__(request, client_addr, server)
        

    def do_POST(self):
        try:
            # Get message from main_server
            mess_len = int(self.headers.get("Content-Length"))
            _rfile = self.rfile.read(mess_len)
            req = json.loads(_rfile)
            lg.info("Got POST-payload, processing")
        except:
            lg.exception(
                f"An exception happened during the processing (probably because the payload was not from mainserver).\nBody:\n{_rfile}")
            self.send_response(400, "Wrong message")
        # check content
        if not set(("event", "prNumber", "repo", "modFile")) == set(req.keys()):
            lg.warning("Wrong json structure, sending 400")
            self.send_response(400, "Wrong json structure")
        if req["prNumber"] == "":
            lg.warning("No PR-Number given, sending 400")
            self.send_response(400, "No pr_number given")

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
            lg.info("Found available port")
            port = self.ports.get_port(f"{req['repo']}-{req['prNumber']}")
            x = threading.Thread(target=functions.create_server, args=(
                port, req['prNumber'], req['repo'], req['modFile']))
            x.start()
            lg.info(f"{req['repo']} ({req['prNumber']}): Started thread for creating of server")
        else:
            lg.info("No port available, adding to queue")
            self.queue.append(req)
            self.update_json()
        return port

    def delete(self, req):
        self.ports.remove_port(f"{req['repo']}-{req['prNumber']}")
        x = threading.Thread(functions.delete_server(req['prNumber'],
                                                     req['repo']))
        x.start()
        lg.info(f"{req['repo']} ({req['prNUmber']}): Started thread to delete server")
        self.update_queue()

    def update_queue(self):
        if len(self.queue) > 0 and self.ports.is_port_avail():
            nextPR = self.queue.pop(0)
            self.update(nextPR)
            self.queue.remove(nextPR)
            self.update_json()
            lg.debug("Updated queue")

    def update_json(self):
        with open("queue.json", "w") as queue_file:
            json.dump(self.queue, queue_file)
            lg.debug("Updated json")

    # GET for UTR checks
    def do_GET(self):
        if str(self.client_address[0]) in IPs:
            self.send_response(200, "OK, Test recieved!")
            self.end_headers()
            lg.info("GET-Test received, sent 200")
        else:
            self.send_response(403, "Forbidden")
            self.end_headers()
            lg.info("GET - IP of Sender not found in List of IPs; 403")

    # HEAD for UTR checks
    def do_HEAD(self):
        if str(self.client_address[0]) in IPs:
            self.send_response(200, "OK, Test recieved!")
            self.end_headers()
            lg.info("HEAD-Test received, sent 200")
        else:
            self.send_response(403, "Forbidden")
            self.end_headers()
            lg.info("HEAD - IP of Sender not found in List of IPs; 403")


httpd = HTTPServer(('0.0.0.0', 4433), Requests)
# httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
