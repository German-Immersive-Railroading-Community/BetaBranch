#!/usr/bin/env python
import json
import logging as lg
import os
import re
import shutil

import requests
from decouple import config


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
                lg.debug("Loaded ports")

    def is_port_avail(self):
        return not len(self.avail_ports) == 0

    def assign_port(self, pr_identifier):
        port = self.avail_ports.pop(0)
        self.server_ports[pr_identifier] = port
        self.update_json()
        lg.debug(f"Assigned port {port}")
        return port

    def remove_port(self, pr_identifier):
        self.avail_ports.append(self.server_ports.pop(pr_identifier))
        self.update_json()
        lg.debug(f"Removed port of {pr_identifier}")

    def has_port(self, pr_identifier):
        return pr_identifier in self.server_ports.keys()

    def get_port(self, pr_identifier):
        if self.has_port(pr_identifier):
            lg.debug(f"Found port of {pr_identifier}, returning that")
            return self.server_ports[pr_identifier]
        else:
            lg.debug(f"No port existing for {pr_identifier}, assigning new")
            return self.assign_port(pr_identifier)

    def update_json(self):
        with open("ports.json", "w") as file:
            json.dump({"ports": self.avail_ports,
                       "server_ports": self.server_ports},
                      file
                      )
            lg.debug("Updated json")


def create_server(port, pr_number: str, mod, modfile):
    lg.info(f"Starting to create/update server of ")
    # Create or update a server with given pr_number and modfile
    server_folder = config("server_folder")+f"{mod}-{pr_number}/"
    if os.path.isdir(server_folder):
        lg.info(f"Serverfiles for {mod} ({pr_number}) found, updating mod")
        os.system(f"screen -S {mod}-{pr_number} -X quit")
        lg.debug(f"Stopping screen of {mod}-{pr_number}")
        os.remove(server_folder+"/mods/"+mod+".jar")
        lg.debug("Removed mod")
    else:
        lg.info(f"No serverfiles found for {mod} ({pr_number}), creating new")
        shutil.copytree(config("server_files"),
                        server_folder)
        lg.debug(f"Created serverfiles for {mod}-{pr_number})")
    r = requests.get(modfile, stream=True)
    lg.debug("Requested modfile")
    if r.status_code == 200:
        with open(server_folder+"/mods/"+mod+".jar", 'a+b') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
            lg.info("Copied modfile")
    # Edit config
    content = ""
    with open(server_folder+"server.properties", "r+") as conf:
        lg.debug("Starting to edit config")
        content = conf.read()
        content = re.sub(r"server-port=\d{1,5}\n", f"server-port={port}\n",
                         content)
        content = re.sub(r"motd=.*\n",
                         f"motd={mod}-{pr_number}\n",
                         content)
        conf.write(content)
        lg.info("Edited config")
    os.system(
        f"screen -dmS {mod}-{pr_number} bash -c 'cd {server_folder};\
         ./auto-restart.sh'")
    lg.info("Started Screen/Server")


def delete_server(pr_number: str, mod: str):
    # Delete existing server
    lg.debug(f"Deleting server of {mod} ({pr_number})")
    server_folder = config("server_folder")+f"{mod}-{pr_number}"
    os.system(f"screen -S {mod}-{pr_number} -X quit")
    lg.debug(f"Stopped server of {mod}-{pr_number}")
    shutil.rmtree(server_folder, ignore_errors=True)
    lg.info(f"Deleted server for {mod} ({pr_number})")
