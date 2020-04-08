""" UDP Server """

import socket
import time
import wmi
import threading
import queue
import json
import pythoncom
import win32

queue_1 = queue.Queue(maxsize=1)  # queue for received instructions to dictate OHM data
queue_2 = queue.Queue(maxsize=50)  # queue for OHM data to be used when sending data


class ReceiveInstructions(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 5005
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(20)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.UDP_IP, self.UDP_PORT))

    def run(self):
        if not queue_1.full():
            # print("receive_data: started")
            try:
                data, addr = self.sock.recvfrom(1024)
                # print(f'received data: {data}')
                queue_1.put(data)
                # print("receive data placed in queue")
            except socket.timeout:
                # print("didn't receive any data (ReceiveData)")
                self.sock.close()
                # print("receive socket closed")


class DataSender(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.send = True
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 5006
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        while True:
            if not queue_2.empty():
                q_data = queue_2.get()
                s_data = json.dumps(q_data)
                # print(f"sending data - {s_data}")
                self.sock.sendto(bytes(str(s_data), "utf-8"), (self.UDP_IP, self.UDP_PORT))
                # time.sleep(1)
            if queue_2.empty():
                break


class OpenHardwareMonitor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def collect_data(self):
        pythoncom.CoInitialize()
        record_id = 1

        for i in range(int(instructions['num'])):

            data_results_temp = {}
            data_results_load = {}

            if instructions['temperature']:
                sensors_temp = hardware_monitor.Sensor(SensorType="Temperature")
                # print(sensors_temp)
                for temperature in sensors_temp:
                    if (temperature.Identifier.find("ram") == -1) and (
                                temperature.Identifier.find("hdd") == -1) and (
                                temperature.Name.find("Package") == -1):

                        data_results_temp['Record_ID'] = record_id
                        data_results_temp['Rec_Type'] = "Temp"
                        data_results_temp['Data_Value'] = temperature.value

                # only put an item on queue if it is populated
                if data_results_temp:
                    print(f'adding to queue - {data_results_temp}')
                    queue_2.put(data_results_temp)

            if instructions['load']:
                sensors_load = hardware_monitor.Sensor(SensorType="Load")
                for load in sensors_load:
                    if (load.Identifier.find("ram") == -1) and (load.Identifier.find("hdd") == -1) and (
                                load.Name.find("Total") == -1):

                        if load.name == 'CPU Core #1':
                            data_results_load['Record_ID'] = record_id
                            data_results_load['Rec_Type'] = "Load"
                            data_results_load['Data_Value'] = load.value

                    if data_results_load:
                        print(f"adding to queue - {data_results_load}")
                        queue_2.put(data_results_load)

            time.sleep(1)
            record_id += 1

        pythoncom.CoUnitialize()


if __name__ == '__main__':
    hardware_monitor = wmi.WMI(namespace=r"root\OpenHardwareMonitor")
    receiver = ReceiveInstructions()
    OHM = OpenHardwareMonitor()
    sender = DataSender()
    receiver.start()
    instructions = queue_1.get()
    instructions = json.loads(instructions)
    OHM.collect_data()
    sender.start()
