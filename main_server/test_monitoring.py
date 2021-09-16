import json
import re
import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer

from decouple import config

#This file is only for testing the monitoring service of UptimeRobot and
#will be merged as soon as it works


class Requests(BaseHTTPRequestHandler):
    def do_GET(self):
        #self.useragent = self.headers.get("User-Agent")
        #match = re.search(r"(?:UptimeRobot)", self.useragent, flags=re.MULTILINE|re.IGNORECASE)
        #if match:
        self.send_response(200, "OK, Test recieved!")
        #else:
        #    self.send_response(403, "Forbidden")

    def do_HEAD(self):
        #self.useragent = self.headers.get("User-Agent")
        #match = re.search(r"(?:UptimeRobot)", self.useragent, flags=re.MULTILINE|re.IGNORECASE)
        #if match:
        self.send_response(200, "OK, Test recieved!")
        #else:
        #    self.send_response(403, "Forbidden")
        


context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(config("cert_path"), config("priv_path"))
context.load_verify_locations(config("full_path"))

httpd = HTTPServer(('0.0.0.0', 4432), Requests)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
