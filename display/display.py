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
    def __init__(self, canvas, x, y, sprite_path):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.sprite = tk.PhotoImage(file=str(sprite_path))

        self.default_time_before_dir_change = 100
        self.time_before_dir_change = self.default_time_before_dir_change
        self.dir = 0 # in degrees

        self.id = canvas.create_image(self.x, self.y, image=self.sprite)

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

        self.canvas.move(self.id, dx_, dy_)

        self.time_before_dir_change -= 1
        if self.time_before_dir_change < 0:
            self.time_before_dir_change = self.default_time_before_dir_change

            # Changes direction
            self.dir = random.randint(0, 359)


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
        self.displayAgents = []
        self.add_agent("predator")
        self.add_agent("predator")
        self.add_agent("prey")

        self.update()

    def update(self):
        for agent in self.displayAgents:
            agent.move()

        # boucle de jeu ~60 FPS
        self.root.after(16, self.update)

    def add_agent(self, type):
        if type == "predator":
            agent = DisplayAgent(self.canvas, 400, 300, PREDA_SPRITE_PATH)
        else:
            agent = DisplayAgent(self.canvas, 100, 300, PREY_SPRITE_PATH)
        self.displayAgents.append(agent)

def send_command(message):
    # Sends commands to queue 128
    to_send = str(message).encode()
    mq_send.send(to_send)
    print("send_command: " + message)


def receive_world_state():
    # Receives the world state from the message queue 129

    print("-- display.py: Listening on " + str(mq_receive_key))
    while True:
        message, t = mq_receive.receive()
        received = message.decode()
        if received:
            command = received.split(" ")

            if command[0] != "[ENV]":
                continue

            if command[1] == "SPAWN":
                print(f"Spawned: {command[2]} {command[3]}")


mq_send_key = 128
mq_send = sysv_ipc.MessageQueue(mq_send_key, sysv_ipc.IPC_CREAT)

mq_receive_key = 129
mq_receive = sysv_ipc.MessageQueue(mq_receive_key)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("TextBox Input")
    root.geometry('1280x720')

    app = App(root)

    # TextBox for input
    txt = tk.Text(root, height=5, width=40)
    txt.pack()

    # Sends message on button click
    btn = tk.Button(root, text="Print", command= lambda: send_command(txt.get('1.0', 'end-1c')))
    btn.pack()

    p_receive_world_state = Process(target=receive_world_state)
    p_receive_world_state.start()

    print("-- display sending on queue " + str(mq_send_key))

    root.mainloop()
    