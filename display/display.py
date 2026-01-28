import sysv_ipc
from multiprocessing import *
import tkinter as tk
from pathlib import Path
import math
import random

CANVA_WIDTH = 800
CANVA_HEIGHT = 600
MOVE_SPEED = 1
BASE_DIR = Path(__file__).resolve().parent.parent
PREDA_SPRITE_PATH = BASE_DIR / "assets" / "predator_sprite.png"
PREY_SPRITE_PATH = BASE_DIR / "assets" / "prey_sprite.png"

class DisplayAgent:
    def __init__(self, agent_id, canvas, x, y, sprite_path):
        self.agent_id = agent_id
        self.canvas = canvas
        self.x = x
        self.y = y
        self.sprite = tk.PhotoImage(file=str(sprite_path))

        self.default_time_before_dir_change = 100
        self.time_before_dir_change = self.default_time_before_dir_change
        self.dir = 0 # in degrees

        self.canva_id = canvas.create_image(self.x, self.y, image=self.sprite)

    def move(self):
        dx_ = MOVE_SPEED * math.cos(self.dir * math.pi/180)
        dy_ = MOVE_SPEED * math.sin(self.dir * math.pi/180)
        self.x += dx_
        self.y += dy_

        if self.x < 0:
            dx_ = 0
            self.x = 0
        if self.x > CANVA_WIDTH:
            dx_ = 0
            self.x = CANVA_WIDTH
        if self.y < 0:
            dy_ = 0
            self.y = 0
        if self.y > CANVA_HEIGHT:
            dy_ = 0
            self.y = CANVA_HEIGHT

        self.canvas.move(self.canva_id, dx_, dy_)

        self.time_before_dir_change -= 1
        if self.time_before_dir_change < 0:
            self.time_before_dir_change = self.default_time_before_dir_change

            # Changes direction
            self.dir = random.randint(0, 359)

    def remove_from_canva(self):
        self.canvas.delete(self.canva_id)
        self.sprite = None


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulation Tkinter")

        self.canvas = tk.Canvas(
            root,
            width=CANVA_WIDTH,
            height=CANVA_HEIGHT,
            bg="black"
        )

        self.canvas.pack()
        self.displayAgents = {} # agent = displayAgents[agent_id]

        self.update()

    # Moves every agent and updates the canva
    def update(self):
        for _, agent in self.displayAgents.items():
            agent.move()

        # boucle de jeu ~60 FPS
        self.root.after(16, self.update)

    def add_agent(self, type, agent_id):
        if type == "predator":
            agent = DisplayAgent(agent_id, self.canvas, 400, 300, PREDA_SPRITE_PATH)
        elif type == "prey":
            agent = DisplayAgent(agent_id, self.canvas, 100, 300, PREY_SPRITE_PATH)
        self.displayAgents[agent_id] = agent

    def remove_agent(self, agent_id):
        agent = self.displayAgents.pop(agent_id)
        agent.remove_from_canva()

def send_command(message):
    # Sends commands to queue 128
    to_send = str(message).encode()
    mq_send.send(to_send)
    print("display.py: send_command: " + message)


def receive_world_state(command_queue):
    # Receives the world state from the message queue 129

    print("-- display.py: Listening on " + str(mq_receive_key))
    while True:
        message, t = mq_receive.receive()
        received = message.decode()
        if received:
            # ex: [ENV] command_type
            command = received.split(" ")
            header = command[0]
            command_type = command[1]

            if header != "[ENV]":
                continue

            if command_type == "SPAWN" or command_type == "KILL": # ex: [ENV] SPAWN predator 1
                agent_type = command[2]
                agent_id = command[3]

                # Puts the command in the command queue waiting to be executed by the App   
                command_queue.put((
                command_type,
                agent_type,
                agent_id
                ))
                print(f"display.py: Command {command_type} {agent_type} {agent_id}")

# Execute each command sent by child processes that are in the command queue
def handle_commands(app: App):
    while not command_queue.empty():
        cmd = command_queue.get()

        if cmd[0] == "SPAWN":
            _, agent_type, agent_id = cmd
            app.add_agent(type=agent_type, agent_id=agent_id)
            print(f"display.py: Spawned {agent_type} {agent_id}")
        elif cmd[0] == "KILL":
            _, agent_type, agent_id = cmd
            app.remove_agent(agent_id=agent_id)
            print(f"display.py: Killed {agent_type} {agent_id}")

    app.root.after(50, lambda: handle_commands(app))

mq_send_key = 128
mq_send = sysv_ipc.MessageQueue(mq_send_key, sysv_ipc.IPC_CREAT)

mq_receive_key = 129
mq_receive = sysv_ipc.MessageQueue(mq_receive_key)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("TextBox Input")
    root.geometry('1280x720')

    app = App(root)
    command_queue = Queue()
    handle_commands(app)

    # TextBox for input
    txt = tk.Text(root, height=5, width=40)
    txt.pack()

    # Sends message on button click
    btn = tk.Button(root, text="Print", command= lambda: send_command(txt.get('1.0', 'end-1c')))
    btn.pack()

    p_receive_world_state = Process(target=receive_world_state, args=(command_queue,))
    p_receive_world_state.start()

    print("-- display sending on queue " + str(mq_send_key))

    root.mainloop()
    