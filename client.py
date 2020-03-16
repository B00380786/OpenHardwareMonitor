""" UDP Client """

import socket
import json
from tkinter import *
import threading
import queue
import argparse
import time

queue_1 = queue.Queue(maxsize=1)  # queue for user instruction to send to server.py
queue_2 = queue.Queue(maxsize=1)  # queue for received data to be added and to be accessed to write to json


class SendInstructions(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 5005
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        while True:
            data = queue_1.get()
            data = json.dumps(data)
            self.sock.sendto(bytes(str(data), "utf-8"), (self.UDP_IP, self.UDP_PORT))


class ReceiveData(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.UDP_IP = "localhost"
        self.UDP_PORT = 5006
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(2)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.UDP_IP, self.UDP_PORT))

    def run(self):
        print("receive_data: started")
        try:
            data, addr = self.sock.recvfrom(1024)
            print(data)
            # data = data.decode()
            queue_2.put(data)
            print("receive_data: ended")
        except socket.timeout:
            print("didn't receive any data(ReceiveData)")
        finally:
            self.sock.close()


class WriteToJSON(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        if not queue_2.empty():
            # exception if no attributes were selected
            print("json_thread: started")
            data = json.loads(str(queue_2.get()))
            with open('data.json', 'a', encoding='utf-8') as f:
                json.dump(data, f)
            print("json_thread: ended")


class GraphicalUserInterface:
    def __init__(self):
        self.window = Tk()
        self.window.title("Open Hardware Monitor")
        self.window.geometry('400x250')
        self.window.mainloop()


if __name__ == '__main__':
    # gui = GraphicalUserInterface()
    sender = SendInstructions()
    receiver = ReceiveData()
    json_writer = WriteToJSON()

    instructions = {'temperature': True, 'load': True, 'fan': False}

    queue_1.put(instructions)
    sender.start()
    time.sleep(3)

    data = receiver.start()
    json_writer.start()
