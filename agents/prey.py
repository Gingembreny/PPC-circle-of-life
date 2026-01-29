#!/usr/bin/env python3

from .agent_base import Agent


class Prey(Agent):
    def __init__(self, agent_id, shared_energy, shared_world_state, energy=7, H=15, R=40):
        super().__init__(
            agent_id = agent_id,
            agent_type = "prey",
            energy = energy,
            H = H,
            R = R,
            shared_energy = shared_energy,
            shared_world_state = shared_world_state
        )