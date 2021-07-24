import hashlib as hl
import hmac
import json
import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer


from decouple import config


class Requests(BaseHTTPRequestHandler):
    def do_POST(self):
        _rfile = self.rfile.read()
        h_object = hmac.new(bytes(config("secret"), "utf8"), _rfile, hl.sha256)
        h_digest = str(h_object.hexdigest())
        h_digest = "sha256=" + h_digest
        if not h_digest == str(self.headers["X-Hub-Signature-256"]):
            self.send_error(403, "Forbidden")
            return
        self.send_response(204)
        self.end_headers()


context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(config("cert_path"), config("priv_path"))
context.load_verify_locations(config("full_path"))

httpd = HTTPServer(('0.0.0.0', 4433), Requests)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
