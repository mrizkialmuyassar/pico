import socket
import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import datetime


class ChatClientGUI:
    def __init__(self, root, client_id):
        self.root = root
        self.client_id = client_id
        self.client_socket = None
        self.running = True

        self.root.title(f"Chat Client - {client_id}")
        self.root.geometry("600x450")

        # Text area untuk log chat
        self.text_area = scrolledtext.ScrolledText(root, height=20, width=70)
        self.text_area.pack(padx=10, pady=10)

        # Frame input
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(pady=5)

        # Input ID penerima
        tk.Label(self.input_frame, text="Kepada (ID):").pack(
            side=tk.LEFT, padx=5
        )
        self.target_entry = tk.Entry(self.input_frame, width=20)
        self.target_entry.pack(side=tk.LEFT, padx=5)

        # Input pesan
        tk.Label(self.input_frame, text="Pesan:").pack(
            side=tk.LEFT, padx=5
        )
        self.message_entry = tk.Entry(self.input_frame, width=30)
        self.message_entry.pack(side=tk.LEFT, padx=5)

        # Tombol connect
        self.connect_button = tk.Button(
            root, text="Connect to Server", command=self.connect_to_server
        )
        self.connect_button.pack(pady=5)

        self.log_file = f"client_{client_id}_log.txt"

    def log_message(self, message):
        """Mencatat pesan ke GUI dan file log"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.text_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.text_area.see(tk.END)
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")

    def receive_messages(self):
        """Menerima pesan dari server"""
        while self.running:
            try:
                data = self.client_socket.recv(1024).decode("ascii")
                if not data:
                    self.log_message("Server mengakhiri koneksi")
                    self.running = False
                    break
                self.log_message(f"Diterima: {data}")
            except Exception as e:
                self.log_message(f"Error menerima: {e}")
                self.running = False
                break

    def send_message(self, event=None):
        """Mengirim pesan private ke server"""
        target_id = self.target_entry.get().strip()
        message = self.message_entry.get().strip()

        if target_id and message and self.client_socket:
            try:
                start_time = time.time()
                if target_id.upper() == "ALL":
                    full_message = f"ALL:{message}"
                else:
                    full_message = f"TO:{target_id}:{message}"
                self.client_socket.send(full_message.encode("ascii"))

                rtt = (time.time() - start_time) * 1000
                ascii_codes = [ord(c) for c in message]

                self.log_message(
                    f"Terkirim ke {target_id}: {message} "
                    f"(ASCII: {ascii_codes}, RTT: {rtt:.2f} ms)"
                )

                if message.lower() == "exit":
                    self.running = False
                    self.client_socket.close()
                    self.client_socket = None
                    self.log_message("Koneksi ditutup")

                self.message_entry.delete(0, tk.END)

            except Exception as e:
                self.log_message(f"Error mengirim: {e}")
        else:
            self.log_message("Error: Isi ID penerima dan pesan")

    def connect_to_server(self, host="192.168.1.10", port=12345):
        """Menghubungkan ke server"""
        try:
            self.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            )
            self.client_socket.connect((host, port))

            # Kirim ID client ke server
            self.client_socket.send(self.client_id.encode("ascii"))

            self.log_message(f"Terhubung ke server {host}:{port}")
            self.connect_button.config(state="disabled")

            # Enter untuk kirim pesan
            self.message_entry.bind("<Return>", self.send_message)

            threading.Thread(
                target=self.receive_messages, daemon=True
            ).start()

        except Exception as e:
            self.log_message(f"Error koneksi: {e}")


if __name__ == "__main__":
    print("=== Chat Client Lokal (Private Messaging) ===")
    client_id = input("Masukkan ID client (misalnya: Client1): ")

    root = tk.Tk()
    app = ChatClientGUI(root, client_id)
    root.mainloop()