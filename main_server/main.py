import hashlib as hl
import hmac
import json
import logging as lg
import os
import ssl
import threading as th
import time
from datetime import datetime as dt
from http.server import BaseHTTPRequestHandler, HTTPServer

import urllib3 as url
from decouple import config

# Preparing logging
today = dt.today().strftime('%Y-%m-%d')
logname = f'../logs/{today}.log'
if not os.path.exists('../logs/'):
    os.mkdir('../logs/')
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


def implement(json, data):
    lg.debug("Started 'implement'-function")
    for key, value in json.items():
        if type(value) == dict and key in data:
            data[key] = implement(value, data[key])
        else:
            data[key] = value
    lg.debug("Done with 'implement'-function")
    return data


http = url.PoolManager()
json_file = str(config("json_file")) + "beta.json"
data = {}


def json_dump(data):
    lg.debug("Dumping to json...")
    with open(json_file, "w+") as dump_file:
        json.dump(data, dump_file)
        lg.debug("Dumped to json")


with open(json_file, "r+") as _file:
    beta_json = json.loads(_file.read())
    lg.debug("Loaded beta.json")
data = implement(beta_json, data)


def postTestServer(event: str, number: str, repo: str, originRepo: str, fileURL: str = "") -> None:
    lg.info("Started to send payload to testserver")
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
        lg.info("Set up payload body, proceeding to sending")
        testResp = http.request(
            "POST", str(config("testURL")), body=data_body, headers={"Content-Length": f"{len_cont}"})
        time.sleep(5)
        if not testResp.status == 204:
            lg.warning(
                f"Request to Testserver was not OK! Code: {str(testResp.status)}. Retrying...")
            continue
        else:
            lg.info("Sending successful")
            if not event == "remove":
                data[repo][number]["port"] = testResp.reason
                lg.debug("Added port to beta.json")
            valid = True
    json_dump(data)


def verify(readfile, header, event, entry_number, repo, originRepo) -> bool:
    # Calculate hmac
    h_object = hmac.new(bytes(config("secret"), "utf8"), readfile, hl.sha256)
    h_digest = "sha256=" + str(h_object.hexdigest())
    lg.info("Calculated the hmac")
    # Check the hmac
    if not h_digest == str(header["X-Hub-Signature-256"]):
        lg.info("hmac is not right, aborting.")
        return False
    elif event == "other":
        lg.info("hmac okay, proceeding with routine 'others'")
        return True
    elif event == "remove":
        lg.info("hmac okay, proceeding with routine 'remove'")
        send_payload = th.Thread(target=postTestServer, args=(
            "remove", entry_number, repo, originRepo))
        send_payload.start()
        return True


def existing_new(readfile, header, json_rfile, repo, originRepo, entry_number) -> None:
    if not verify(readfile, header, "other", entry_number, repo, originRepo):
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
    # Sidenote: These variable names are terrible

    # getting the Artifact URL... Technically; adding that to the json
    ListEmpty = False
    while not ListEmpty:
        time.sleep(90)
        lg.info("Getting information from AppVeyor")
        resp = http.request(
            "GET", f"https://ci.appveyor.com/api/projects/MrTroble/{repo}/branch/{head_ref}", headers={"Content-Type": "application/json"})
        lg.debug(f"Requested information about the branch {head_ref}")
        json_resp = json.loads(resp.data)
        job_id = json_resp["build"]["jobs"][0]["jobId"]
        lg.debug("Extracted the buildjob-id")
        art_resp = http.request(
            "GET", f"https://ci.appveyor.com/api/buildjobs/{job_id}/artifacts")
        lg.debug(
            f"Requested the url of the artifact (file) of buildjob {job_id}")
        artifacts = json.loads(art_resp.data)
        try:
            filename = artifacts[0]["fileName"]
            lg.info("Found build, proceeding to send data to testserver")
            ListEmpty = True
        except IndexError:
            lg.warning(
                f"No build available ({repo} : {head_ref})! Retrying...")
            continue
    data[repo][number
               ]["download"] = f"https://ci.appveyor.com/api/buildjobs/{job_id}/artifacts/{filename}"
    lg.debug("Added artifact URL to the payload")
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
        lg.debug("Got POST-request, processed")
        _rfile = self.rfile.read()
        json_rfile = json.loads(_rfile)
        # Determine Repo
        try:
            originRepo = json_rfile["pull_request"]["head"]["repo"]["name"]
            repo = str(originRepo).lower()
            entry_number = str(json_rfile["number"])
            # Check if closed or not
            if json_rfile["action"] == "closed":
                lg.info("Detected that the action is 'closed'")
                verify(_rfile, self.headers, "remove",
                       entry_number, repo, originRepo)
                try:
                    del data[repo][entry_number]
                    lg.info(f"Deleted the entry ({entry_number}).")
                except KeyError:
                    lg.warning(
                        f"There was an error deleting an entry! Repo: {repo}, Entry: {entry_number}.")
                json_dump(data)
            # start the magic
            else:
                existing_new_thread = th.Thread(target=existing_new, args=(
                    _rfile, self.headers, json_rfile, repo, originRepo, entry_number))
                existing_new_thread.start()
        except:
            lg.exception(
                "An error occured while getting important variables (probably because the payload is not from GH).")

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


# Starting Webserver
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(config("cert_path"), config("priv_path"))
context.load_verify_locations(config("full_path"))

httpd = HTTPServer(('0.0.0.0', 4433), Requests)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
