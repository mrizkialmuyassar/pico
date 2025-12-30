import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
import datetime


class ChatServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Server - Lokal")
        self.root.geometry("600x400")

        self.text_area = scrolledtext.ScrolledText(root, height=20, width=70)
        self.text_area.pack(padx=10, pady=10)

        self.start_button = tk.Button(
            root, text="Start Server", command=self.start_server
        )
        self.start_button.pack(pady=5)

        self.server_socket = None
        self.clients = {}  
        self.client_lock = threading.Lock()
        self.log_file = "server_log.txt"

    def log_message(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.text_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.text_area.see(tk.END)

    def send_private_message(self, message, target_id):
        with self.client_lock:
            if target_id in self.clients:
                try:
                    self.clients[target_id].send(message.encode("ascii"))
                    return True
                except Exception as e:
                    self.log_message(f"Error mengirim ke {target_id}: {e}")
        return False

    def send_broadcast_message(self, message, sender_id):
        with self.client_lock:
            for cid, csock in self.clients.items():
                if cid != sender_id:
                    try:
                        csock.send(message.encode("ascii"))
                    except Exception as e:
                        self.log_message(f"Error broadcast ke {cid}: {e}")

    def handle_client(self, client_socket, client_address, client_id):
        self.log_message(f"Koneksi dari {client_address} | ID: {client_id}")

        with self.client_lock:
            self.clients[client_id] = client_socket

        try:
            while True:
                data = client_socket.recv(1024).decode("ascii")
                if not data or data.lower() == "exit":
                    break

                if data.startswith("ALL:"):
                    message = data[4:]
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    full_msg = f"[{timestamp}] {client_id} (Broadcast): {message}"
                    self.log_message(full_msg)
                    self.send_broadcast_message(full_msg, client_id)

                elif data.startswith("TO:"):
                    _, target_id, message = data.split(":", 2)
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    full_msg = f"[{timestamp}] Dari {client_id} ke {target_id}: {message}"

                    if not self.send_private_message(full_msg, target_id):
                        client_socket.send(
                            f"Error: Client {target_id} tidak ditemukan"
                            .encode("ascii")
                        )

                else:
                    client_socket.send(
                        "Error: Gunakan TO:target_id:message atau ALL:message"
                        .encode("ascii")
                    )

        except Exception as e:
            self.log_message(f"Error client {client_id}: {e}")

        finally:
            with self.client_lock:
                if client_id in self.clients:
                    del self.clients[client_id]
            client_socket.close()

    def accept_connections(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            client_id = client_socket.recv(1024).decode("ascii")
            threading.Thread(
                target=self.handle_client,
                args=(client_socket, client_address, client_id),
                daemon=True,
            ).start()

    def start_server(self, host="0.0.0.0", port=12345):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)

        self.log_message(f"Server berjalan di {host}:{port}")
        self.start_button.config(state="disabled")

        threading.Thread(
            target=self.accept_connections, daemon=True
        ).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatServerGUI(root)
    root.mainloop()