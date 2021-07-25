import hashlib as hl
import hmac
import json
import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

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
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Date", time.strftime(" %a, %d %b %Y %H:%M:%S %Z")) #Wed, 23 Jun 2021 08:59:30 GMT
        self.send_header("Expires", "-1")
        self.send_header("Pragma", "no-cache")
        self.send_header("Strict-Transport-Security", "max-age=31536000")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("X-Xss-Protection", "1; mode=block")
        self.end_headers()


context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(config("cert_path"), config("priv_path"))
context.load_verify_locations(config("full_path"))

httpd = HTTPServer(('0.0.0.0', 4433), Requests)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
