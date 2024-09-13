import threading
from datetime import datetime
from pathlib import Path
import logging
from time import ctime

from flask import Flask, render_template, request, flash, redirect, url_for
import socket
import json
import os

app = Flask(__name__)
HOST = "0.0.0.0"
UDP_PORT = 5001
STORAGE_PATH = Path("storage/data.json")
STORAGE_DIR = Path("storage")


def check_json_exists():
    if not os.path.exists("STORAGE_PATH"):
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STORAGE_PATH, "w", encoding="utf-8") as file:
            json.dump([], file)
        logging.debug("Storage is created")


def save_response(new_data):
    try:
        with open(STORAGE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append(new_data)

    with open(STORAGE_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    logging.debug("file is written")


def socket_server(ip, port):
    logging.debug(f"Start thread: {ctime()}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ip, port
    server_socket.bind(server_address)
    logging.debug("Listening for UDP packets...")
    try:
        while True:
            data, address = server_socket.recvfrom(1024)
            decoded_data = json.loads(data.decode("utf-8"))
            logging.debug(f"Received data: {decoded_data} from: {address}")
            save_response(decoded_data)

    except KeyboardInterrupt:
        logging.debug(f"Destroy server")
    finally:
        server_socket.close()


def socket_client(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ip, port
    with sock as s:
        while True:
            try:
                s.connect(server_address)
                data = message
                s.sendall(data)
                break
            except ConnectionRefusedError:
                logging.debug(f"Connection is refused")
    sock.close()


check_json_exists()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/message", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        username = request.form["username"]
        message = request.form["message"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        messages = {timestamp: {"username": username, "message": message}}
        serialized_messages = json.dumps(messages)
        socket_client(HOST, UDP_PORT, serialized_messages.encode("utf-8"))
        logging.debug(f"Sent message: {messages}")
        return redirect(url_for("index"))
    return render_template("message.html")


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html")


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG, format="%(threadName)s %(message)s")
    mainApp = threading.Thread(
        target=lambda: app.run(host=HOST, port=3000, debug=True, use_reloader=False)
    )
    socketServer = threading.Thread(target=socket_server, args=(HOST, UDP_PORT))

    mainApp.start()

    socketServer.start()
    mainApp.join()
    socketServer.join()
    print("Done!")
