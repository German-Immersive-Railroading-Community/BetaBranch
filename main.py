from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
from decouple import config

httpd = HTTPServer(('0.0.0.0', 4001), SimpleHTTPRequestHandler)
httpd.socket = ssl.wrap_socket(httpd.socket, certfile=str(config("path_certfile")), server_side=True)
httpd.serve_forever()