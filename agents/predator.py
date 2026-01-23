#!/usr/bin/env python3

from .agent_base import Agent


class Predator(Agent):
    def __init__(self, agent_id, shared_energy, shared_world_state, energy=50, H=30, R=80):
        super().__init__(
            agent_id = agent_id,
            agent_type = "predator",
            energy = energy,
            H = H,
            R = R,
            shared_energy = shared_energy,
            shared_world_state = shared_world_state
        )

    
    


if __name__ == "__main__":
    predator = Predator(agent_id = 1)
    predator.start()
    predator.join()
