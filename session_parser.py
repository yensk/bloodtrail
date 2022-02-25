from dataclasses import dataclass
import os
import collections
from zipfile import ZipFile
import json
import log

sid_to_computer = {}
sid_to_user = {}

parsed_user_sessions = None
parsed_computer_sessions = None

def parse(filepath):
    global parsed_user_sessions
    global parsed_computer_sessions

    data_exists = False

    for root, dirs, files in os.walk(filepath):
        for file in files:
            if file.lower().endswith("bloodhound.zip"):
                data_exists = True

    if not data_exists:
        log.logger.error(f"[E] No Bloodhound files found at '{filepath}'")
        exit()

    parse_computers(filepath)
    parse_users(filepath)
    parsed_user_sessions, parsed_computer_sessions= parse_sessions(filepath)

def get_computer_name(sid):
    if sid in sid_to_computer:
        return sid_to_computer[sid]
    return sid

def get_user_name(sid):
    if sid in sid_to_user:
        return sid_to_user[sid]
    return sid

def parse_users(filepath):
    log.logger.debug(f"[ ] Start parsing users in path: {filepath}")
    global sid_to_user

    for root, dirs, files in os.walk(filepath):
        for file in files:
            if file.endswith(".zip"):
                timestamp = file.split("_")[0]
                zip = ZipFile(os.path.join(root,file))

                for fname in zip.namelist():
                    if fname.endswith("_users.json"):
                        log.logger.debug(f"    [ ] Parsing file: {os.path.join(root,file)}")
                        content = zip.read(fname)
                        cjson = json.loads(content)
                        for user in cjson["users"]:
                            sid_to_user[user["ObjectIdentifier"]] = user["Properties"]["name"]

def parse_computers(filepath):
    log.logger.debug(f"[ ] Start parsing computers in path: {filepath}")
    global sid_to_computer

    for root, dirs, files in os.walk(filepath):
        for file in files:
            if file.endswith(".zip"):
                timestamp = file.split("_")[0]
                zip = ZipFile(os.path.join(root,file))

                for fname in zip.namelist():
                    if fname.endswith("_computers.json"):
                        log.logger.debug(f"    [ ] Parsing file: {os.path.join(root,file)}")
                        content = zip.read(fname)
                        cjson = json.loads(content)
                        for computer in cjson["computers"]:
                            sid_to_computer[computer["ObjectIdentifier"]] = computer["Properties"]["name"]

def parse_sessions(filepath):
    log.logger.debug(f"[ ] Start parsing sessions in path: {filepath}")
    global sid_to_computer

    sessions = []

    for root, dirs, files in os.walk(filepath):
        for file in files:
            if file.endswith(".zip"):
                log.logger.debug(f"    [ ] Parsing file: {os.path.join(root,file)}")
                timestamp = file.split("_")[0]
                zip = ZipFile(os.path.join(root,file))

                for fname in zip.namelist():
                    if not fname.endswith("computers.json"):
                        continue
                    content = zip.read(fname)
                    cjson = json.loads(content)
                    for computer in cjson["computers"]:
                        for session in computer["Sessions"]:
                            session["timestamp"] = timestamp
                            sessions.append(session)

    user_sessions = collections.defaultdict(dict)
    computer_sessions = collections.defaultdict(dict)
    
    for session in sessions:
        tmp = user_sessions[get_user_name(session["UserId"])]
        cname = get_computer_name(session["ComputerId"])
        if not cname in tmp:
            timestamps = []
            tmp[cname] = timestamps
        timestamps = tmp[cname]

        timestamps.append(session["timestamp"])

        tmp = computer_sessions[get_computer_name(session["ComputerId"])]
        uname = get_user_name(session["UserId"])
        if not uname in tmp:
            timestamps = []
            tmp[uname] = timestamps
        timestamps = tmp[uname]

        timestamps.append(session["timestamp"])

    return user_sessions, computer_sessions
