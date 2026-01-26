import sysv_ipc
from multiprocessing import *
import tkinter as tk


def send_command(message):
    #sends to queue 128
    to_send = str(message).encode()
    mq_send.send(to_send)
    print("send_command: " + message)


def receive_world_state():
    # Receives the world state from the message queue 127

    print("-- display.py: Listening on " + str(mq_receive_key))
    while True:
        message, t = mq_receive.receive()
        received = message.decode()
        if received:
            command = received.split(" ")

            if command[0] == "[ENV]":
                print("World state received:")
                print(received)


mq_send_key = 128
mq_send = sysv_ipc.MessageQueue(mq_send_key, sysv_ipc.IPC_CREAT)

mq_receive_key = 129
mq_receive = sysv_ipc.MessageQueue(mq_receive_key)
if __name__ == "__main__":
    root = tk.Tk()
    root.title("TextBox Input")
    root.geometry('400x200')

    # TextBox for input
    txt = tk.Text(root, height=5, width=40)
    txt.pack()

    # Sends message on button click
    btn = tk.Button(root, text="Print", command= lambda: send_command(txt.get('1.0', 'end-1c')))
    btn.pack()

    p_receive_world_state = Process(target=receive_world_state)
    p_receive_world_state.start()

    root.mainloop()
    p_receive_world_state.join()
    