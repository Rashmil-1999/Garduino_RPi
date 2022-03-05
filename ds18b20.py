import os
import glob
import time
import datetime

# # these two lines mount the device:
# os.system('modprobe w1-gpio')
# os.system('modprobe w1-therm')


class DS18B20:
    def __init__(self):
        self.base_dir = r"/sys/bus/w1/devices/28*"
        self.sensor_path = []
        self.sensor_name = []
        self.temps = []
        self.log = []

    def find_sensors(self):
        self.sensor_path = glob.glob(self.base_dir)
        self.sensor_name = [path.split("/")[-1] for path in self.sensor_path]
        self.sensor_map = {
            key: val for key, val in zip(self.sensor_name, self.sensor_path)
        }

    def strip_string(self, temp_str):
        i = temp_str.index("t=")
        if i != -1:
            t = temp_str[i + 2 :]
            temp_c = float(t) / 1000.0
            # temp_f = temp_c * (9.0/5.0) + 32.0
        return temp_c

    def read_temp(self):
        tstamp = datetime.datetime.now()
        for sensor, path in zip(self.sensor_name, self.sensor_path):
            # open sensor file and read data
            with open(path + "/w1_slave", "r") as f:
                valid, temp = f.readlines()
            # check validity of data
            if "YES" in valid:
                self.log.append((tstamp, sensor) + self.strip_string(temp))
                time.sleep(2)
            else:
                time.sleep(0.2)

    def read_1_temp(self, sensor):
        if sensor in self.sensor_name:
            for _ in range(5):
                with open(self.sensor_map[sensor] + "/w1_slave", "r") as f:
                    valid, temp = f.readlines()
                if "YES" in valid:
                    return self.strip_string(temp)
                else:
                    time.sleep(1)
        return None

    def print_temps(self):
        print("-" * 90)
        for t, n, c, f in self.log:
            # print(f'Sensor: {n}  C={c:,.3f}  F={f:,.3f}  DateTime: {t}')
            print(f"Sensor: {n}  C={c:,.3f}  DateTime: {t}")

    def print_sensor_address(self):
        print(self.sensor_name)

    def clear_log(self):
        self.log.clear()


# try:
#     s = DS18B20()
#     s.find_sensors()

#     while True:
#         s.read_temp()
#         s.print_temps()
#         s.clear_log()
# except KeyboardInterrupt:
#     quit()

# pin0 = 28-03109779633b 28-03109779633b
# pin1 = 28-030c97944774 28-030c97944774
# pin2 = 28-030397940a2f 28-030397940a2f
# pin3 = 28-030e979457c9 28-030e979457c9
