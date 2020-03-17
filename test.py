import wmi

hardware_monitor = wmi.WMI(namespace=r"root\OpenHardwareMonitor")

for i in range(0, 10):
    sensors_temp = hardware_monitor.Sensor(["Name", "Parent", "Value", "Identifier"], SensorType="Temperature")
    # print(sensors_temp)
    sensors_load = hardware_monitor.Sensor(SensorType="Load")
    # print(sensors_load)

    for temperature in sensors_temp:
        if (temperature.Identifier.find("ram") == -1) and (temperature.Identifier.find("hdd") == -1) and (
                temperature.Name.find("Package") == -1):
            print(temperature.value)

    for load in sensors_load:
        if (load.Identifier.find("ram") == -1) and (load.Identifier.find("hdd") == -1) and (
                load.Name.find("Total") == -1):
            print(load.value)
