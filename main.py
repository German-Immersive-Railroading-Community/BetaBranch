from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
from decouple import config
import json
import hashlib as hl
import hmac

class Requests(BaseHTTPRequestHandler):
    def do_POST(self):
        _rfile = self.rfile.read()
        h_object = hmac.new(config("secret"), _rfile)
        h_digest = h_object.hexdigest()
        print(h_digest)
        print(self.headers)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(config("cert_path"), config("priv_path"))
context.load_verify_locations(config("full_path"))

httpd = HTTPServer(('0.0.0.0', 4433), Requests)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()