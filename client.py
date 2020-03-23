""" UDP Client """

import socket
import json
import tkinter as tk
import threading
import queue
import time

queue_1 = queue.Queue(maxsize=1)  # queue for user instruction to send to server.py
queue_2 = queue.Queue(maxsize=20)  # queue for received data to be added and to be accessed to write to json


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
            print("request sent to server")


class ReceiveData(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.UDP_IP = "localhost"
        self.UDP_PORT = 5006
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(30)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.UDP_IP, self.UDP_PORT))

    def run(self):
        print("receive_data: started")
        x = 0
        try:
            for i in range(0, 100):
                data, addr = self.sock.recvfrom(1024)
                print(f'received data: {data}')
                # data = data.decode()
                queue_2.put(data)
                print("receive data placed in queue")
                x += 1
                if x == int(instructions['num']):
                    break
        except socket.timeout:
            print("didn't receive any data (ReceiveData)")
            self.sock.close()
            print("receive socket closed")


class WriteToJSON(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.results = {}

    def run(self):
        # if not queue_2.empty():
        # exception if no attributes were selected
        print('json_thread: STARTED')
        with open('data.json', 'w') as file:
            for i in range(0, int(instructions['num'])):
                data = queue_2.get()
                data = str(data.decode("utf-8"))
                # print(data)
                # json_data = json.dumps(data) + '\n'
                parsed = json.loads(data)
                json.dump(parsed, file, indent=4, sort_keys=True, separators=(',', ': '))

        print('json_thread: ENDED')


class GraphicalUserInterface:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Open Hardware Monitor")
        self.window.geometry('400x250')
        self.instructions = {'temperature': False, 'load': False, 'fan': False}
        self.entry = None

    def instruction_collector(self):
        label = tk.Label(master=self.window, text="Select the data you would like from OpenHardwareMonitor:")
        label.pack()

        temp_button = tk.Button(command=self.button_click_temp, master=self.window, text='temperature')
        temp_button.pack(side="top")

        load_button = tk.Button(command=self.button_click_load, master=self.window, text='load')
        load_button.pack(side="top")

        fan_button = tk.Button(command=self.button_click_fan, master=self.window, text='fan speed')
        fan_button.pack(side="top")

        self.entry = tk.Entry()
        self.entry.pack()

        tk.Button(master=self.window, text='get results', command=self.quit).pack(side='top')

        self.window.mainloop()
        return self.instructions

    def button_click_temp(self):
        self.instructions['temperature'] = True

    def button_click_load(self):
        self.instructions['load'] = True

    def button_click_fan(self):
        self.instructions['fan'] = True

    def num_results(self):
        self.instructions['num'] = self.entry.get()

    def quit(self):
        self.num_results()
        self.window.destroy()


if __name__ == '__main__':
    gui = GraphicalUserInterface()
    sender = SendInstructions()
    receiver = ReceiveData()
    json_writer = WriteToJSON()

    instructions = gui.instruction_collector()

    print(instructions)

    queue_1.put(instructions)
    sender.start()

    time.sleep(5)

    receiver.start()
    json_writer.start()
