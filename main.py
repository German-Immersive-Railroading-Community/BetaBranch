import hashlib as hl
import hmac
import json
import ssl
import threading as th
from http.server import BaseHTTPRequestHandler, HTTPServer

import urllib3 as url
from decouple import config

data = {}
beta_json = json.loads(open(str(config("json_file")) + "beta.json"))

def implement(json, data):
    for key, value in json.items():
        if type(value) == dict and key in dict:
            data[key] = implement(value, data[key])
        else:
            data[key] = value
    return data

print(implement(beta_json, data), "Confirm")

def calc_digest(readfile, header):
    h_object = hmac.new(bytes(config("secret"), "utf8"), readfile, hl.sha256)
    h_digest = str(h_object.hexdigest())
    h_digest = "sha256=" + h_digest
    if not h_digest == str(header["X-Hub-Signature-256"]):
        return
    json_rfile = json.loads(readfile)
    head_ref = json_rfile["pull_request"]["head"]["ref"]
    print(head_ref)
    http = url.PoolManager()
    resp = http.request(
        "GET", f"https://ci.appveyor.com/api/projects/MrTroble/girsignals/branch/{head_ref}")
    json_resp = json.loads(resp.data)
    job_id = json_resp["build"]["jobs"][0]["jobId"]
    art_resp = http.request(
        "GET", f"https://ci.appveyor.com/api/buildjobs/{job_id}/artifacts")
    artifacts = json.loads(art_resp)
    filename = artifacts[0]["filename"]


class Requests(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(204, "It worked!")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Expires", "-1")
        self.send_header("Pragma", "no-cache")
        self.send_header("Strict-Transport-Security", "max-age=31536000")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("X-Xss-Protection", "1; mode=block")
        self.send_header("Connection", "close")
        self.end_headers()
        _rfile = self.rfile.read()
        calc = th.Thread(target=calc_digest, args=(_rfile, self.headers))
        calc.start()


context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(config("cert_path"), config("priv_path"))
context.load_verify_locations(config("full_path"))

httpd = HTTPServer(('0.0.0.0', 4433), Requests)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
