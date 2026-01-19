#!/usr/bin/env python3

from agent_base import Agent


class Predator(Agent):
    def __init__(self, agent_id, energy=50, H=20, R=80):
        super().__init__(
            agent_id = agent_id,
            agent_type = "predator",
            energy = energy,
            H = H,
            R = R
        )


if __name__ == "__main__":
    predator = Predator(agent_id = 1)
    predator.run()
