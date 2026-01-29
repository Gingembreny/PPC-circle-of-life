import os
import signal
import sysv_ipc
from multiprocessing import *
import tkinter as tk
from pathlib import Path
import math
import random
import queue

CANVA_WIDTH = 800
CANVA_HEIGHT = 600
MOVE_SPEED = 1
env_pid = -1
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
        for agent in list(self.displayAgents.values()):
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
        agent = self.displayAgents.pop(agent_id, None)
        if agent is None:
            print(f"[DISPLAY] Warning: remove_agent called for unknown id {agent_id}.")
            return
        agent.remove_from_canva()


def flush_queue(q):
    while True:
        try:
            q.get_nowait()
        except queue.Empty:
            break

def on_click_send_button(text_widget):
    global env_pid
    message = text_widget.get('1.0', 'end-1c')
    command = message.split(" ")
    if not command:
        return
    
    if command[0] == "DROUGHT":
        # If the command is a drought, use a signal rather than the message queue.
        if int(env_pid) != -1:
            if len(command) < 2 or command[1] == "true" or command[1] == "start":
                os.kill(int(env_pid), signal.SIGUSR1)
                print("[DISPLAY] DROUGHT_START signal sent")
            elif command[1] == "false" or command[1] == "end":
                os.kill(int(env_pid), signal.SIGUSR2)
                print("[DISPLAY] DROUGHT_OVER signal sent")
        else:
            print(f"[DISPLAY] env_pid not yet received. PID: {env_pid}")
    else:
        send_message_to_mq(message)
    text_widget.delete("1.0", tk.END)

def send_message_to_mq(message):
    # Sends commands to queue 128
    to_send = str(message).encode()
    mq_send.send(to_send)
    print("[DISPLAY] send_message_to_mq: " + message)


def receive_world_state(command_queue):
    # Receives the world state from the message queue 129

    global env_pid
    
    print("[DISPLAY] Listening on mq " + str(mq_receive_key))
    while True:
        try:
            message, t = mq_receive.receive()
        except sysv_ipc.ExistentialError:
            break
        
        received = message.decode()
        if received:
            # ex: [ENV] command_type
            command = received.split(" ")
            header = command[0]
            command_type = command[1]

            if header != "[ENV]":
                continue
            
            if command_type == "PID": # [ENV] PID env_pid
                env_pid = command[2]

                # Puts the command in the command queue waiting to be executed by the App   
                command_queue.put((
                command_type,
                env_pid
                ))
                print(f"[DISPLAY] Added to queue command {command_type} {env_pid}")

            if command_type == "SPAWN" or command_type == "KILL": # ex: [ENV] SPAWN predator 1
                agent_type = command[2]
                agent_id = int(command[3])

                # Puts the command in the command queue waiting to be executed by the App   
                command_queue.put((
                command_type,
                agent_type,
                agent_id
                ))
                print(f"[DISPLAY] Added to queue command {command_type} {agent_type} {agent_id}")

# Execute each command sent by child processes that are in the command queue
def handle_commands(app: App):
    global env_pid
    try:
        cmd = command_queue.get_nowait()
    except queue.Empty:
        pass
    else:
        if cmd[0] == "SPAWN":
            _, agent_type, agent_id = cmd
            if agent_id in app.displayAgents:
                print(f"[DISPLAY] Warning: spawn for existing id {agent_id} (ignoring)")
            else:
                app.add_agent(type=agent_type, agent_id=agent_id)
                print(f"[DISPLAY] Spawned {agent_type} {agent_id}")
        elif cmd[0] == "KILL":
            _, agent_type, agent_id = cmd
            app.remove_agent(agent_id=agent_id)
            print(f"[DISPLAY] Killed {agent_type} {agent_id}")
        elif cmd[0] == "PID":
            _, env_pid = cmd
            print(f"[DISPLAY] Got PID {env_pid}")

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
    flush_queue(command_queue)
    handle_commands(app)

    # TextBox for input
    txt = tk.Text(root, height=5, width=40)
    txt.pack()

    # Sends message on button click
    btn = tk.Button(root, text="SEND COMMAND", command= lambda: on_click_send_button(txt))
    btn.pack()

    p_receive_world_state = Process(target=receive_world_state, args=(command_queue,))
    p_receive_world_state.start()

    print("[DISPLAY] sending on mq " + str(mq_send_key))

    root.mainloop()
    