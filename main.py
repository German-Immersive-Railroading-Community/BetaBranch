from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
from decouple import config

class Requests(BaseHTTPRequestHandler):
    pass

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(config("cert_path"), config("priv_path"))
context.load_verify_locations(config("full_path"))

httpd = HTTPServer(('0.0.0.0', 4433), Requests)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)