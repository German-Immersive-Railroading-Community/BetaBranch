#!/usr/bin/env python
import shutil
import os
import requests
from decouple import config
import json


class ports:

    def __init__(self):
        self.avail_ports = list(
            range(int(config("min_port")), int(config("max_port"))))
        self.server_ports = {}
        if os.path.isfile("ports.json"):
            self.avail_ports = list(
                range(int(config("min_port")), int(config("max_port"))))
            self.server_ports = {}
            with open("ports.json", "r") as file:
                data = json.load(file)
                self.avail_ports = data["ports"]
                self.server_ports = data["server_ports"]

    def is_port_avail(self):
        return not len(self.avail_ports) == 0

    def assign_port(self, pr_identifier):
        port = self.avail_ports.pop(0)
        self.server_ports[pr_identifier] = port
        self.update_json()
        return port

    def remove_port(self, pr_identifier):
        self.avail_ports.append(self.server_ports.pop(pr_identifier))
        self.update_json()

    def has_port(self, pr_identifier):
        return pr_identifier in self.server_ports.keys()

    def get_port(self, pr_identifier):
        if self.has_port(pr_identifier):
            return self.server_ports[pr_identifier]
        else:
            return self.assign_port(pr_identifier)

    def update_json(self):
        with open("ports.json", "w") as file:
            json.dump({"ports": self.avail_ports,
                       "server_ports": self.server_ports},
                      file
                      )


def create_server(port, pr_number: str, mod, modfile):
    # Create or update a server with given pr_number and modfile
    server_folder = config("server_folder")+f"{mod}-{pr_number}/"
    if os.path.isdir(server_folder):
        delete_server(pr_number, mod)
    shutil.rmtree(server_folder, ignore_errors=True)
    shutil.copytree(config("server_files"),
                    server_folder)
    r = requests.get(modfile, stream=True)
    if r.status_code == 200:
        with open(server_folder+"/mods/"+mod+".jar", 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    # Edit config
    with open(server_folder+"server.properties", "r") as conf:
        content = conf.readlines()
        content[29] = f"server-port={port}\n"
        content[46] = f"motd={mod}-{pr_number}\n"
    with open(server_folder+"server.properties", "w") as conf:
        conf.writelines(content)
        print("Test")
    os.system(
        f"screen -dmS {mod}-{pr_number} bash -c 'cd {server_folder};\
         ./auto-restart.sh'")


def delete_server(pr_number: str, mod: str):
    # Delete existing server
    server_folder = config("server_folder")+f"{mod}-{pr_number}"
    os.system(f"screen -X -S {mod}-{pr_number} quit")
    shutil.rmtree(server_folder, ignore_errors=True)


if __name__ == "__main__":
    create_server(
        10, "10", "GIRSignals", "https://github.com/German-Immersive-Railroading-Community/GIRSignals/releases/download/1.0.675/GIRSignals-1.0.675.jar")
