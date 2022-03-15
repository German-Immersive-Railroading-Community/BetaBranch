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
            range(int(config("min_port")), int(config("max_port"))+1))
        self.server_ports = {}
        if os.path.isfile("ports.json"):
            with open("ports.json", "r") as file:
                data = json.load(file)
                for port in self.avail_ports:
                    if port in data["server_ports"].values():
                        self.avail_ports.remove(port)
                self.server_ports = data["server_ports"]
                lg.debug("Loaded ports")
        self.update_json()

    def is_port_avail(self):
        return not len(self.avail_ports) == 0

    def assign_port(self, pr_identifier):
        port = self.avail_ports.pop(0)
        self.server_ports[pr_identifier] = port
        self.update_json()
        lg.debug(f"{pr_identifier}: Assigned port {port}")
        return port

    def remove_port(self, pr_identifier):
        self.avail_ports.append(self.server_ports.pop(pr_identifier))
        self.update_json()
        lg.debug(f"{pr_identifier}: Removed port")

    def has_port(self, pr_identifier):
        return pr_identifier in self.server_ports.keys()

    def get_port(self, pr_identifier):
        if self.has_port(pr_identifier):
            lg.debug(
                f"{pr_identifier}: Found port, returning that")
            return self.server_ports[pr_identifier]
        else:
            lg.debug(
                f"{pr_identifier}: No port existing, assigning new")
            return self.assign_port(pr_identifier)

    def update_json(self):
        with open("ports.json", "w") as file:
            json.dump({"ports": self.avail_ports,
                       "server_ports": self.server_ports},
                      file
                      )
            lg.debug("Updated json")


def create_server(port, pr_number: str, mod: str, modfile, mc_version: str) -> None:
    """Create or update a server with given pr_number and modfile"""
    lg.info(f"{mod} ({pr_number}): Starting to create/update server")
    server_folder = config("server_folder")+f"{mod}-{pr_number}/"
    if os.path.isdir(server_folder):
        lg.info(f"{mod} ({pr_number}): Serverfiles found, updating mod")
        os.system(f"screen -S {mod}-{pr_number} -X quit")
        lg.debug(f"{mod} ({pr_number}): Stopping screen")
        os.remove(server_folder+"/mods/"+mod+".jar")
        lg.debug(f"{mod} ({pr_number}): Removed mod")
    else:
        lg.info(f"{mod} ({pr_number}): No serverfiles found, creating new")
        mc_version = "girsignals" if mod.lower() == "girsignals" else mc_version
        copypath = str(config("server_files")) + f"/{mc_version}"
        if not os.path.exists(copypath):
            lg.debug("Path does not exist, trying major version detect.")
            for dir in os.listdir(str(config("server_files"))):
                if mc_version in dir:
                    copypath = str(config("server_files")) + dir
                    lg.debug(f"Version probably is {dir}; using that")
                    break
        shutil.copytree(copypath,
                        server_folder)
        lg.debug(f"{mod} ({pr_number}): Created serverfiles")
    r = requests.get(modfile, stream=True)
    lg.debug(f"{mod} ({pr_number}): Requested modfile")
    if r.status_code == 200:
        with open(server_folder+"/mods/"+mod+".jar", 'a+b') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
            lg.info(f"{mod} ({pr_number}): Copied modfile")
    # Edit config
    content = ""
    with open(server_folder+"server.properties", "r+") as conf:
        lg.debug(f"{mod} ({pr_number}): Starting to edit config")
        content = conf.read()
        content = re.sub(r"server-port=\d{1,5}\n", f"server-port={port}\n",
                         content)
        content = re.sub(r"motd=.*\n",
                         f"motd={mod}-{pr_number}\n",
                         content)
        conf.write(content)
        lg.info(f"{mod} ({pr_number}): Edited config")
    os.system(
        f"screen -dmS {mod}-{pr_number} bash -c 'cd {server_folder};\
         ./auto-restart.sh'")
    lg.info(f"{mod} ({pr_number}): Started Screen/Server")


def delete_server(pr_number: str, mod: str) -> None:
    """Delete existing server"""
    lg.debug(f"{mod} ({pr_number}): Deleting server...")
    server_folder = config("server_folder")+f"{mod}-{pr_number}"
    os.system(f"screen -S {mod}-{pr_number} -X quit")
    lg.debug(f"{mod} ({pr_number}): Stopped server")
    shutil.rmtree(server_folder, ignore_errors=True)
    lg.info(f"{mod} ({pr_number}): Deleted server")
