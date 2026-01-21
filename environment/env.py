#!/usr/bin/env python3

import socket
import json
import threading
from multiprocessing import Manager

HOST = "localhost"
PORT = 6666

nb_predators = 0
nb_preys = 0
grass_quantity = 0
predator_eat_gain = 30
prey_eat_gain = 10
alive_agents = set()
energy_ledger = {}
world_lock = threading.Lock()
manager = Manager()
shared_energy = manager.dict()

def print_world_state():
	global nb_predators, nb_preys, grass_quantity
	print(f"[ENV] World state: predators={nb_predators}, preys={nb_preys}, grass={grass_quantity}")
				

def handle_agent(conn, addr):
	global nb_predators, nb_preys, grass_quantity, alive_agents, energy_ledger
	
	print(f"[ENV] New connection from {addr}")

	while True:
		data = conn.recv(1024)
		if not data:
			with world_lock:
				if 'agent_id' in locals() and agent_id in alive_agents:
					alive_agents.remove(agent_id)

					if agent_type == "predator":
						nb_predators -= 1
						print(f"[ENV] Predator {agent_id} disconnected")
					elif agent_type == "prey":
						nb_preys -= 1
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
				with world_lock:
					energy_ledger.setdefault(agent_id, 0)
					if agent_type == "predator":
						if nb_preys > 0:
							nb_preys -= 1
							if alive_agents:
								prey_id = next(iter(alive_agents))
								alive_agents.remove(prey_id)

							energy_ledger[agent_id] += predator_eat_gain
							shared_energy[agent_id] = energy_ledger[agent_id]
							print(f"[ENV] Predator {agent_id} eats a prey (+{predator_eat_gain})")
						else:
							print("[ENV] No prey alive")
					
					elif agent_type == "prey":
						if grass_quantity > 0:
							grass_quantity -= 1
							energy_ledger[agent_id] += prey_eat_gain
							shared_energy[agent_id] = energy_ledger[agent_id]
							print(f"[ENV] Prey {agent_id} eats grass (+{prey_eat_gain})")
						else:
							print("[ENV] No grass available")
					
					print_world_state()

			if msg_type == "notify_birth":
				with world_lock:
					if agent_id not in alive_agents:
						alive_agents.add(agent_id)

						if agent_type == "predator":
							nb_predators += 1
							print(f"[ENV] New born predator {agent_id}")
						elif agent_type == "prey":
							nb_preys += 1
							print(f"[ENV] New born prey {agent_id}")
					print_world_state()
				
			if msg_type == "notify_death":
				with world_lock:
					if agent_id in alive_agents:
						alive_agents.remove(agent_id)

						if agent_type == "predator":
							nb_predators -= 1
							print(f"[ENV] Predator {agent_id} died (natural)")
						elif agent_type == "prey":
							nb_preys -= 1
							print(f"[ENV] Prey {agent_id} died (natural)")
					
					print_world_state()

		except json.JSONDecodeError:
			print("[ENV] Received invalid JSON")

	conn.close()


def main():
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind((HOST, PORT))
	server_socket.listen()

	print(f"[ENV] Server listening on {HOST}:{PORT}")

	while True:
		conn, addr = server_socket.accept()
		thread = threading.Thread(target = handle_agent, args = (conn, addr), daemon = True)
		thread.start()


if __name__ == "__main__":
	main()
