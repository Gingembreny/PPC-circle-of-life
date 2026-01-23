#!/usr/bin/env python3

import socket
import json
import time
from multiprocessing import *

class Agent(Process):
    def __init__(self, agent_id, agent_type, energy, shared_energy, shared_world_state, H, R,
                 env_host="localhost", env_port=6666):
        super().__init__()
        self.agent_id = agent_id
        self.agent_type = agent_type  # "predator" or "prey"
        self.energy = energy
        self.shared_energy = shared_energy
        self.shared_world_state = shared_world_state
        self.H = H
        self.R = R
        self.state = "passive"

        # socket setup
        self.env_host = env_host
        self.env_port = env_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((env_host, env_port))
        self.send_request("notify_birth")

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

    # ---------- pull gain from environment ----------
    def consume_energy_from_env(self):
        delta = self.shared_energy.get(self.agent_id, 0)
        if delta != 0:
            self.energy += delta
            self.shared_energy[self.agent_id] = 0

    # ---------- pull world state form environment ----------
    def perceive_world(self):
        predators = self.shared_world.get("predators", 0)
        preys = self.shared_world.get("preys", 0)
        grass = self.shared_world.get("grass", 0)
        return predators, preys, grass

    # ---------- main loop ----------
    def run(self, dt=1):
        while True:
            time.sleep(dt)

            # energy decay
            self.consume_energy_from_env()
            self.energy -= 1
            self.update_state()

            print(f"[{self.agent_type} {self.agent_id}] "
                  f"energy={self.energy}, state={self.state}")

            if self.state == "active":
                self.request_eat()

            if self.energy > self.R:
                self.request_reproduce()

            if self.energy <= 0:
                self.notify_death()
                print(f"[{self.agent_type} {self.agent_id}] died")
                break

            predators, preys, grass = self.perceive_world()
            print(f"[AGENT {self.agent_id}] sees world: Predators={predators}, Preys={preys}, Grass:{grass}")

        self.sock.close()
