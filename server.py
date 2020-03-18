""" UDP Server """

import socket
import time
# import wmi
import threading
import queue
import json
import logging

queue_1 = queue.Queue(maxsize=1)  # queue for received instructions to dictate OHM data
queue_2 = queue.Queue(maxsize=10)  # queue for OHM data to be used when sending data
# hardware_monitor = wmi.WMI(namespace=r"root\OpenHardwareMonitor")


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
            print(data)
            # data = data.decode()
            queue_1.put(data)


class DataSender(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 5006
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        while True:
            if not queue_2.empty():
                print("data on the queue to send")
                q_data = queue_2.get()
                s_data = json.dumps(q_data)
                print(f"sending data - {s_data}")
                self.sock.sendto(bytes(str(s_data), "utf-8"), (self.UDP_IP, self.UDP_PORT))
                print("data sent to client")
            time.sleep(1)


class OpenHardwareMonitor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        data = queue_1.get()
        data = json.loads(data)
        print(data)
        print(type(data))

        data_results_temp = {}
        data_results_load = {}
        data_results_fan = {}

        if data['temperature']:
            sensors_temp = hardware_monitor.Sensor(["Name", "Parent", "Value", "Identifier"], SensorType="Temperature")

            print(sensors_temp)
            for temperature in sensors_temp:
                if (temperature.Identifier.find("ram") == -1) and (temperature.Identifier.find("hdd") == -1) and (
                        temperature.Name.find("Package") == -1):
                    data_results_temp['Rec_Type'] = "Temp"
                    sensor_name = temperature.Name
                    data_results_temp[sensor_name] = temperature.value

                    print(temperature.value)

            # only put an item on queue if it is populated
            if data_results_temp:
                print(f'adding to queue - {data_results_temp}')
                queue_2.put(data_results_temp)

        if data['load']:
            sensors_load = hardware_monitor.Sensor(SensorType="Load")
            for load in sensors_load:
                if (load.identifier.find("ram") == -1) and (load.identifier("hdd") == -1) and (
                        load.Name.find("Total") == -1):
                    data_results_load['Rec_Type'] = 'Load'
                    sensor_name = load.name
                    data_results_load[sensor_name] = load.value

                if data_results_load:
                    print(f"adding to queue - {data_results_load}")
                    queue_2.put(data_results_load)


if __name__ == '__main__':
    receiver = ReceiveInstructions()
    OHM = OpenHardwareMonitor()
    sender = DataSender()
    receiver.start()
    time.sleep(3)
    sender.start()
    OHM.run()
