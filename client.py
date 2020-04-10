""" UDP Client """

import socket
import json
import tkinter as tk
import threading
import queue
import time
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

queue_1 = queue.Queue(maxsize=1)  # queue for user instruction to send to server.py
queue_2 = queue.Queue(maxsize=50)  # queue for received data to be added and to be accessed to write to json


class SendInstructions(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 5007
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(20)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.UDP_IP, self.UDP_PORT))

    def run(self):
        try:
            while True:
                data = queue_1.get()
                # print(data)
                data = json.dumps(data)
                self.sock.sendto(bytes(str(data), "utf-8"), (self.UDP_IP, self.UDP_PORT))
                # print("request sent to server")
        except socket.timeout:
            # print("didn't receive any data (ReceiveData)")
            self.sock.close()
            # print("receive socket closed")


class ReceiveData(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.UDP_IP = "localhost"
        self.UDP_PORT = 5008
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(120)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.UDP_IP, self.UDP_PORT))

    def run(self):
        # print("receive_data: started")
        x = 0
        try:
            for i in range(0, 100):
                data, addr = self.sock.recvfrom(1024)
                # print(f'received data: {data}')
                queue_2.put(data)
                # print("receive data placed in queue")
                x += 1
                if x == int(instructions['num']):
                    break
        except socket.timeout:
            # print("didn't receive any data (ReceiveData)")
            self.sock.close()
            # print("receive socket closed")


class WriteToJSON(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        # print('json_thread: STARTED')

        with open('data.json', 'w') as file:
            data_dict = {'Data': {}}

            for i in range(0, int(instructions['num'])):
                data = queue_2.get()
                data = str(data.decode("utf-8"))
                parsed = json.loads(data)
                # data_list.append(parsed)
                data_dict['Data'][i] = parsed

            json.dump(dict(data_dict), file, indent=4, sort_keys=True, separators=(',', ': '))

        # print('json_thread: ENDED')


class GraphicalUserInterface:
    def __init__(self):
        self.window = tk.Tk()
        self.instructions = {'temperature': False, 'load': False, 'num': 0}
        self.entry = None
        self.clicked = None
        self.data_entries = []
        self.time_entries = []
        self.figure = None
        self.add_plots = None

    def instruction_collector(self):
        self.window.title("Open Hardware Monitor")
        self.window.geometry('500x300')

        label_data = tk.Label(master=self.window, text="Select the data you would like from OpenHardwareMonitor:")
        label_data.pack()

        self.clicked = tk.StringVar()
        self.clicked.set("Temperature")

        options = tk.OptionMenu(self.window, self.clicked, "Temperature", "Load")
        options.pack()

        label_num = tk.Label(master=self.window, text="Print the number of values you would like. (max=50)")
        label_num.pack()

        self.entry = tk.Entry(self.window)
        self.entry.pack()
        callback = self.window.register(self.only_numeric_input)  # registers a Tcl to Python callback
        self.entry.configure(validate="key", validatecommand=(callback, "%P"))  # enables validation

        tk.Button(master=self.window, text='get results', command=self.quit).pack(side='top')

        self.window.mainloop()
        return self.instructions

    def only_numeric_input(self, P):
        if P.isdigit():
            return True
        return False

    def get_instructions(self):
        if self.clicked.get() == 'Temperature':
            self.instructions['temperature'] = True

        elif self.clicked.get() == 'Load':
            self.instructions['load'] = True

        self.instructions['num'] = self.entry.get()

    def quit(self):
        self.get_instructions()
        self.window.destroy()

    def graph(self):
        self.window = tk.Tk()
        self.window.title('Open Hardware Monitor Results Graph')

        self.figure = Figure(figsize=(5, 5), dpi=100)
        self.add_plots = self.figure.add_subplot(111)

        self.animate()

        canvas = FigureCanvasTkAgg(self.figure, self.window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self.window)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.window.mainloop()

    def animate(self):
        with open('data.json', 'r') as file:
            file = file.read()
            # print('dict: ' + str(file))
            file = json.loads(file)
            file = dict(file)

            for i in range(int(instructions['num'])):
                self.data_entries.append(int(file['Data'][str(i)]['Data_Value']))

            for second in range(0, int(instructions['num'])):
                self.time_entries.append(second)

        self.add_plots.clear()
        self.add_plots.plot(self.time_entries, self.data_entries)
        if self.instructions['temperature']:
            self.add_plots.set_ylabel('Temperature (celsius)')
        elif self.instructions['load']:
            self.add_plots.set_ylabel('Load (%)')

        self.add_plots.set_xlabel('Time (s)')


if __name__ == '__main__':
    gui = GraphicalUserInterface()
    sender = SendInstructions()
    receiver = ReceiveData()
    json_writer = WriteToJSON()

    instructions = gui.instruction_collector()

    queue_1.put(instructions)

    sender.start()
    time.sleep(2)

    receiver.start()

    json_writer.start()
    json_writer.join()

    gui.graph()

    sender.join()
    receiver.join()
