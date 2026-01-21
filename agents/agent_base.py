#!/usr/bin/env python3

import socket
import json
import time
from multiprocessing import *

class Agent(Process):
    def __init__(self, agent_id, agent_type, energy, H, R,
                 env_host="localhost", env_port=6666):
        super().__init__()
        self.agent_id = agent_id
        self.agent_type = agent_type  # "predator" or "prey"
        self.energy = energy
        self.H = H
        self.R = R
        self.state = "passive"

        # socket setup
        self.env_host = env_host
        self.env_port = env_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((env_host, env_port))

    # ---------- state logic ----------
    def update_state(self):
        if self.energy < self.H:
            self.state = "active"
        else:
            self.state = "passive"

    # ---------- communication helpers ----------
    def send_request(self, request_type):
        message = {
            "type": request_type,
            "agent_type": self.agent_type,
            "agent_id": self.agent_id,
            "energy": self.energy
        }
        self.sock.sendall(json.dumps(message).encode())

    # ---------- action requests ----------
    def request_eat(self):
        self.send_request("request_eat")

    def request_reproduce(self):
        self.send_request("request_reproduce")

    def notify_death(self):
        self.send_request("notify_death")

    # ---------- main loop ----------
    def run(self, dt=1):
        while True:
            time.sleep(dt)

            # energy decay
            self.energy -= 1
            self.update_state()

            print(f"[{self.agent_type} {self.agent_id}] "
                  f"energy={self.energy}, state={self.state}")

            if self.state == "active":
                self.request_eat()

            if self.energy > self.R:
                self.request_reproduce()

            if self.energy < 0:
                self.notify_death()
                print(f"[{self.agent_type} {self.agent_id}] died")
                break

        self.sock.close()
