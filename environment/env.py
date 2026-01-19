#!/usr/bin/env python3

import socket
import json


HOST = "localhost"
PORT = 6666


def handle_agent(conn, addr):
    print(f"[ENV] New connection from {addr}")

    while True:
        data = conn.recv(1024)
        if not data:
            print(f"[ENV] Connection closed by {addr}")
            break

        try:
            message = json.loads(data.decode())
            print(f"[ENV] Received: {message}")
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
        handle_agent(conn, addr)


if __name__ == "__main__":
    main()
