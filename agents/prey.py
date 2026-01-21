#!/usr/bin/env python3

from agent_base import Agent


class Prey(Agent):
    def __init__(self, agent_id, energy=30, H=15, R=60):
        super().__init__(
            agent_id = agent_id,
            agent_type = "prey",
            energy = energy,
            H = H,
            R = R
        )


if __name__ == "__main__":
    prey = Prey(agent_id =1 )
    prey.start()
    prey.join()
