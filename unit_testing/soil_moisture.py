import serial
import time

try:
    # set up serial communication on port ACM0 at 9600 baud rate
    ser = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
    ser.flush()
except Exception as e:
    print("Arduino not present at /dev/ttyACM0")
    logging.error("Arduino not present at /dev/ttyACM0")


# function to read soil_moisture
def read_soil_moisture():
    ser.write(b"moisture\n")
    time.sleep(1)
    read_serial = ser.readlines()[-1].decode("UTF-8")[:-2]
    read_serial = read_serial.split(":")
    soil_moisture = {}
    for i in range(0, len(read_serial), 2):
        soil_moisture[read_serial[i]] = int(int(read_serial[i + 1]) % 100)
    return soil_moisture


def read_avg_soilMoisture(times, testing=False, fetch_max=False, fetch_avg=True, ts=1):
    keys = ["ch_1", "ch_2", "ch_3", "ch_4", "ch_5", "ch_6", "ch_7", "ch_8"]
    soil_moisture = {key: [] for key in keys}
    command = b"moisture\n"
    for _ in range(times):
        if testing:
            command = b"testing\n"
        ser.write(command)
        time.sleep(ts)
        try:
            read_serial = ser.readlines()[-1].decode("UTF-8")[:-2].split(":")
        except IndexError:
            time.sleep(1)
            continue
        for i in range(0, len(read_serial), 2):
            if testing:
                soil_moisture[read_serial[i]].append(int(int(read_serial[i + 1])))
            else:
                soil_moisture[read_serial[i]].append(
                    100 if int(read_serial[i + 1]) >= 100 else int(read_serial[i + 1])
                )
    soil_moisture_copy = {}

    for key, val in soil_moisture.items():
        if len(val) != 0:
            if fetch_avg:
                soil_moisture_copy[key] = sum(val) / len(val)
            elif fetch_max:
                soil_moisture_copy[key] = max(val)
            else:
                soil_moisture_copy[key] = min(val)

    return soil_moisture_copy


def read_raw_values():
    ser.write(b"testing\n")
    time.sleep(1)
    read_serial = ser.readlines()[-1].decode("UTF-8")[:-2]
    read_serial = read_serial.split(":")
    soil_moisture = {}
    for i in range(0, len(read_serial), 2):
        soil_moisture[read_serial[i]] = int(int(read_serial[i + 1]))
    return soil_moisture

    return soil_moisture_copy


if __name__ == "__main__":
    soil_mois = read_avg_soilMoisture(5, testing=True)
    print(soil_mois)