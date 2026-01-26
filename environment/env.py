#!/usr/bin/env python3

import socket
import json
import threading
import time
from multiprocessing import Manager
from agents.predator import Predator
from agents.prey import Prey

HOST = "localhost"
PORT = 6666

nb_predators = 0
nb_preys = 0
grass_quantity = 0
grass_growth_rate = 5
predator_eat_gain = 30
prey_eat_gain = 10
predator_reproduce_threshold = 80
prey_reproduce_threshold = 60
reproduce_cost = 30
next_agent_id = 0
alive_agents = set()
agent_types = {}
process_table ={}
energy_ledger = {}
world_lock = threading.Lock()

def print_world_state():
	global nb_predators, nb_preys, grass_quantity
	print(f"[ENV] World state: predators={nb_predators}, preys={nb_preys}, grass={grass_quantity}")

def allocate_agent_id():
	global next_agent_id
	agent_id = next_agent_id
	next_agent_id += 1
	return agent_id

def spawn_agent(agent_type, agent_id, shared_energy, shared_world_state):
	global process_table, agent_types
	if agent_type == "predator":
		agent = Predator(agent_id = agent_id, shared_energy = shared_energy, shared_world_state = shared_world_state)
	elif agent_type == "prey":
		agent = Prey(agent_id = agent_id, shared_energy = shared_energy, shared_world_state = shared_world_state)

	agent.start()
	agent_types[agent_id] = agent_type
	process_table[agent_id] = agent
	print(f"[ENV] Spawned {agent_type} {agent_id}")

def select_prey_id():
	global alive_agents
	for aid in alive_agents:
		if agent_types.get(aid) == "prey":
			return aid
	return None

def grass_growth_loop(max_grass, shared_world_state):
	global grass_quantity, grass_growth_rate
	while True:
		time.sleep(5)
		with world_lock:
			grass_quantity = min(max_grass, grass_quantity + grass_growth_rate)
			shared_world_state["grass"] = grass_quantity

def set_drought(is_drought):
	global grass_growth_rate
	with world_lock:
		if is_drought:
			grass_growth_rate = 1
			print("[ENV] Drought ON...")
		else:
			grass_growth_rate = 5
			print("[ENV] Drought OFF...")

def handle_agent(conn, addr, shared_energy, shared_world_state):
	global nb_predators, nb_preys, grass_quantity, alive_agents, energy_ledger, process_table, agent_types
	
	print(f"[ENV] New connection from {addr}")

	while True:
		data = conn.recv(1024)
		if not data:
			with world_lock:
				if 'agent_id' in locals() and agent_id in alive_agents:
					alive_agents.remove(agent_id)

					if agent_type == "predator":
						nb_predators -= 1
						shared_world_state["predators"] = nb_predators
						print(f"[ENV] Predator {agent_id} disconnected")
					elif agent_type == "prey":
						nb_preys -= 1
						shared_world_state["preys"] = nb_preys
						print(f"[ENV] Prey {agent_id} disconnected")

					print_world_state()
			print(f"[ENV] Connection closed by {addr}")
			break

		try:
			message = json.loads(data.decode())
			print(f"[ENV] Received: {message}")
			msg_type = message.get("type")
			agent_type = message.get("agent_type")
			agent_id = message.get("agent_id")
			
			if msg_type == "request_eat":
				victim_id = None
				with world_lock:
					energy_ledger.setdefault(agent_id, 0)
					if agent_type == "predator":
						prey_id = select_prey_id()
						if prey_id is not None:
							alive_agents.remove(prey_id)
							agent_types.pop(prey_id, None)
							nb_preys -= 1
							shared_world_state["preys"] = nb_preys
								
							energy_ledger[agent_id] += predator_eat_gain
							shared_energy[agent_id] = energy_ledger[agent_id]
							victim_id = prey_id
							print(f"[ENV] Predator {agent_id} eats a prey (+{predator_eat_gain})")
						else:
							print("[ENV] No prey alive")
					
					elif agent_type == "prey":
						if grass_quantity > 0:
							grass_quantity -= 1
							shared_world_state["grass"] = grass_quantity
							energy_ledger[agent_id] += prey_eat_gain
							shared_energy[agent_id] = energy_ledger[agent_id]
							print(f"[ENV] Prey {agent_id} eats grass (+{prey_eat_gain})")
						else:
							print("[ENV] No grass available")
					
					print_world_state()
				
				if victim_id is not None:
					prey_process = process_table.pop(victim_id, None)
					if prey_process:
						prey_process.terminate()
						prey_process.join()

			if msg_type == "notify_birth":
				with world_lock:
					if agent_id not in alive_agents:
						alive_agents.add(agent_id)
						agent_types[agent_id] = agent_type

						if agent_type == "predator":
							nb_predators += 1
							shared_world_state["predators"] = nb_predators
							print(f"[ENV] New born predator {agent_id}")
						elif agent_type == "prey":
							nb_preys += 1
							shared_world_state["preys"] = nb_preys
							print(f"[ENV] New born prey {agent_id}")
					print_world_state()
				
			if msg_type == "notify_death":
				with world_lock:
					if agent_id in alive_agents:
						alive_agents.remove(agent_id)
						agent_types.pop(agent_id, None)

						if agent_type == "predator":
							nb_predators -= 1
							shared_world_state["predators"] = nb_predators
							print(f"[ENV] Predator {agent_id} died (natural)")
						elif agent_type == "prey":
							nb_preys -= 1
							shared_world_state["preys"] = nb_preys
							print(f"[ENV] Prey {agent_id} died (natural)")

					print_world_state()

			if msg_type == "request_reproduce":
				with world_lock:
					energy_ledger.setdefault(agent_id, 0)

					if agent_type == "predator":
						allowed = (energy_ledger.get(agent_id, 0) >= predator_reproduce_threshold)
					elif agent_type == "prey":
						allowed = (energy_ledger.get(agent_id, 0) >= prey_reproduce_threshold)
					else:
						allowed = False

					if allowed:
						energy_ledger[agent_id] -= reproduce_cost
						shared_energy[agent_id] = energy_ledger[agent_id]

						new_id = allocate_agent_id()
						spawn_agent(agent_type, new_id, shared_energy, shared_world_state)
						print(f"[ENV] Reproduction approved, spawning {agent_type} {new_id}")

					else:
						print(f"[ENV] {agent_type} {agent_id} reproduction denied (energy too low)")

		except json.JSONDecodeError:
			print("[ENV] Received invalid JSON")

	conn.close()


def main():
	manager = Manager()
	shared_energy = manager.dict()
	shared_world_state = manager.dict()
	shared_world_state["predators"] = nb_predators
	shared_world_state["preys"] = nb_preys
	shared_world_state["grass"] = grass_quantity
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind((HOST, PORT))
	server_socket.listen()

	print(f"[ENV] Server listening on {HOST}:{PORT}")

	max_grass_quantity = 100
	grass = threading.Thread(target=grass_growth_loop, args=(max_grass_quantity, shared_world_state), daemon = True)
	grass.start()

	while True:
		conn, addr = server_socket.accept()
		thread = threading.Thread(target = handle_agent, args = (conn, addr, shared_energy, shared_world_state), daemon = True)
		thread.start()


if __name__ == "__main__":
	main()
