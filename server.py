# test
""" UDP Server """

import socket
import time
import wmi
import threading
import queue

queue_1 = queue.Queue(maxsize=1)  # queue for received instructions to dictate OHM data
queue_2 = queue.Queue(maxsize=1)  # queue for OHM data to be used when sending data


class ReceiveInstructions(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 5005
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.UDP_IP, self.UDP_PORT))

    def run(self):
        if not queue_1.full():
            data, addr = self.sock.recvfrom(1024)
            # data = data.decode()
            print(data)
            queue_1.put(data)


class DataSender(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 5006
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        while True:
            data = queue_2.get()
            print(data)
            self.sock.sendto(bytes(str(data), "utf-8"), (self.UDP_IP, self.UDP_PORT))
            time.sleep(1)


class OpenHardwareMonitor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.hardware_monitor = wmi.WMI(namespace=r"root\OpenHardwareMonitor")
        self.temperature = None
        self.load = None

    def run(self):
        data = queue_1.get()
        # temperature, load = data

        for _ in data:

            if 'temperature':
                sensors_temp = self.hardware_monitor.Sensor(["Name", "Parent", "Value", "Identifier"],
                                                            SensorType="Temperature")

                for temperature in sensors_temp:
                    if (temperature.Identifier.find("ram") == -1) and (temperature.Identifier.find("hdd") == -1) and (
                            temperature.Name.find("Package") == -1):
                        self.temperature = temperature.value

            if 'load':
                sensors_load = self.hardware_monitor.Sensor(SensorType="Load")
                for load in sensors_load:
                    if (load.identifier.find("ram") == -1) and (load.identifier("hdd") == -1) and (
                            load.Name.find("Total") == -1):
                        self.load = load.value

        data = self.temperature, self.load
        queue_2.put(data)
        '''
        for value in data:
            if not value is None:
                queue_2.put(value + time.time())
                '''

        '''
        queue_1.get()
        if load == True:
                    for load in sensors_load:
            if (load.Identifier.find("ram") == -1) and (load.Identifier.find("hdd") == -1) and (
                    load.Name.find("Total") == -1):
                # print(load.value)
                self.load = load.value
        '''


if __name__ == '__main__':
    receiver = ReceiveInstructions()
    OHM = OpenHardwareMonitor()
    sender = DataSender()
    receiver.start()
    time.sleep(3)
    sender.start()
    OHM.run()
