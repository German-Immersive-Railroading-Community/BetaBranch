import hashlib as hl
import hmac
import json
import ssl
import threading as th
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

import urllib3 as url
from decouple import config


#Making a List of IPs from UTR
IPs = []
for ip in open('UTR_IPs.txt', 'r'):
    IPs.append(str(ip.replace('\n', '')))

def implement(json, data):
    # I really don't know how, but it works... Ask Kontiko
    for key, value in json.items():
        if type(value) == dict and key in data:
            data[key] = implement(value, data[key])
        else:
            data[key] = value
    return data


http = url.PoolManager()
json_file = str(config("json_file")) + "beta.json"
data = {}


def json_dump(data):
    with open(json_file, "w+") as dump_file:
        json.dump(data, dump_file)


with open(json_file, "r+") as _file:
    beta_json = json.loads(_file.read())
data = implement(beta_json, data)

http = url.PoolManager()


def postTestServer(event: str, number: str, repo: str, originRepo : str, fileURL: str = "") -> None:
    valid = False
    number = str(number)
    while not valid:
        testRequest = {}
        testRequest["event"] = event
        testRequest["prNumber"] = number
        testRequest["modFile"] = fileURL
        testRequest["repo"] = originRepo
        len_cont = len(str(testRequest))
        data_body = json.dumps(testRequest).encode("utf-8")
        testResp = http.request(
            "POST", str(config("testURL")), body=data_body, headers={"Content-Length": f"{len_cont}"})
        time.sleep(5)
        if not testResp.status == 204:
            t = time.strftime("%H:%M:%S", time.localtime())
            print(
                f"Request to Testserver was not OK! Code: {str(testResp.status)}, Time: {t} . Retrying...")
            continue
        else:
            if not event == "remove":
                data[repo][number]["port"] = testResp.reason
            valid = True
    json_dump(data)


def calc_digest(readfile, header, json_rfile, repo, originRepo) -> None:
    # Calculate hmac
    h_object = hmac.new(bytes(config("secret"), "utf8"), readfile, hl.sha256)
    h_digest = str(h_object.hexdigest())
    h_digest = "sha256=" + h_digest
    # Check the hmac
    if not h_digest == str(header["X-Hub-Signature-256"]):
        return

    number = str(json_rfile["number"])
    # Check if PR exists in json
    if not repo in data:
        data[repo] = {}
    if not number in data[repo]:
        data[repo][number] = {}

    # Setting the json and getting branch name
    data[repo][number
               ]["name"] = json_rfile["pull_request"]["title"]
    head_ref = json_rfile["pull_request"]["head"]["ref"]

    # getting the Artifact URL... Technically; adding that to the json
    ListEmpty = False
    while not ListEmpty:
        time.sleep(120)
        resp = http.request(
            "GET", f"https://ci.appveyor.com/api/projects/MrTroble/{repo}/branch/{head_ref}", headers={"Content-Type": "application/json"})
        json_resp = json.loads(resp.data)
        job_id = json_resp["build"]["jobs"][0]["jobId"]
        art_resp = http.request(
            "GET", f"https://ci.appveyor.com/api/buildjobs/{job_id}/artifacts")
        artifacts = json.loads(art_resp.data)
        try:
            filename = artifacts[0]["fileName"]
            ListEmpty = True
        except IndexError:
            print("No build avaiable! Retrying...")
            continue
    data[repo][number
               ]["download"] = f"https://ci.appveyor.com/api/buildjobs/{job_id}/artifacts/{filename}"
    send_payload = th.Thread(target=postTestServer, args=(
        "update", number, repo, originRepo, data[repo][number
                                                         ]["download"]))
    send_payload.start()
    json_dump(data)


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
        json_rfile = json.loads(_rfile)
        # Determine Repo
        originRepo = json_rfile["pull_request"]["head"]["repo"]["name"]
        repo = str(json_rfile["pull_request"]["head"]["repo"]["name"]).lower()
        entry_number = str(json_rfile["number"])
        # Check if closed or not
        if json_rfile["action"] == "closed":
            send_payload = th.Thread(target=postTestServer, args=(
                "remove", entry_number, repo, originRepo))
            send_payload.start()
            try:
                del data[repo][entry_number]
            except KeyError:
                t = time.strftime("%H:%M:%S", time.localtime())
                print(
                    f"There was a error deleting a entry! Repo: {repo}, Entry: {entry_number}, Time of Error: {t} .")
            json_dump(data)
        # start the magic
        else:
            calc = th.Thread(target=calc_digest, args=(
                _rfile, self.headers, json_rfile, repo, originRepo))
            calc.start()

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

# Starting Webserver
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(config("cert_path"), config("priv_path"))
context.load_verify_locations(config("full_path"))

httpd = HTTPServer(('0.0.0.0', 4433), Requests)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
