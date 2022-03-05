#!/usr/bin/python3
import RPi.GPIO as GPIO
import serial

import time
import datetime as dt
import logging
import json
import socket
import os
from pprint import pprint

from hasura import HasuraClient

import Adafruit_DHT  # temperature (Air & Humidity)
from ds18b20 import DS18B20  # soil temperature sensors

# set GPIO Mode to BCM
GPIO.setmode(GPIO.BCM)

# base dir and paths
BASE_DIR = os.getcwd()
# logging paths
IRRIGATION_LOG = os.path.join(BASE_DIR, "logs/irrigation.log")
# tracking files
LAST_IRRIGATED = os.path.join(BASE_DIR, "logs/last_irrigated.txt")
LAST_SENSOR_DATA_UPDATED = os.path.join(BASE_DIR, "logs/last_sensor_data_updated.txt")
# pending files
PENDING_UPDATE = os.path.join(BASE_DIR, "logs/pending_update.txt")
# datan files
IRRIGATION_TIME = os.path.join(BASE_DIR, "logs/irrigation_time.json")
IRRIGATION_MODE = os.path.join(BASE_DIR, "logs/irrigation_mode.json")
PLANT_STATUS = os.path.join(BASE_DIR, "logs/plant_mapping.json")
MANUAL_CONTROL = os.path.join(BASE_DIR, "logs/manual_control.json")

# set up logging configuration
logging.basicConfig(
    filename=IRRIGATION_LOG,
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

# declare imp variables

U_UUID = "0538f99b-b6b3-4c78-8b37-da93249fd4f0"
url = "https://relieved-asp-16.hasura.app/v1/graphql"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwNTM4Zjk5Yi1iNmIzLTRjNzgtOGIzNy1kYTkzMjQ5ZmQ0ZjAiLCJpYXQiOjE2MDQ5MTQ3OTEuOTUyLCJlbWFpbCI6InJhc2htaWxwODMzQGdtYWlsLmNvbSIsInJvbGVzIjpbInVzZXIiXSwiaHR0cHM6Ly9oYXN1cmEuaW8vand0L2NsYWltcyI6eyJ4LWhhc3VyYS1hbGxvd2VkLXJvbGVzIjpbInVzZXIiXSwieC1oYXN1cmEtZGVmYXVsdC1yb2xlIjoidXNlciIsIngtaGFzdXJhLXVzZXItaWQiOiIwNTM4Zjk5Yi1iNmIzLTRjNzgtOGIzNy1kYTkzMjQ5ZmQ0ZjAiLCJ4LWhhc3VyYS1vcmctaWQiOiJnYXJkdWlubyIsIngtaGFzdXJhLWFkbWluLXNlY3JldCI6ImFkbWluLXNlY3JldCJ9LCJleHAiOjE2MzY0NTA3OTF9.2HJ14CJ1ShUsU7YqqsD3smRKbx2FJjF_xI6vG1-ZKBc"
}


# flags
manual_mode = False
manual_control_flag = False
auto_control_flag = False
network_status = False

# get last modified time in seconds at the start of the script
manual_file_last_modified = 0
timing_file_last_modified = 0
sensor_mapping_last_modified = 0
manual_control_file_last_modified = 0

try:
    # set up serial communication on port ACM0 at 9600 baud rate
    ser = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
    ser.flush()
except Exception as e:
    print("Arduino not present at /dev/ttyACM0")
    logging.error("Arduino not present at /dev/ttyACM0")

# DHT22
DHT_sensor = Adafruit_DHT.DHT22
DHT_pin = 18

# ds18b20
try:
    soil_temp_sensor = DS18B20()
    soil_temp_sensor.find_sensors()
except KeyboardInterrupt:
    print("Keyboard interrupt")

# init list with pin numbers
pin_list = [21, 20, 16, 26]
plants = ["Hall", "Tomato:Raddish:Tulsi", "Pepper", "Ajma:Dragon_F"]

# pin mapping
pin_map = {k: v for k, v in zip(pin_list, plants)}
inverse_pin_map = {v: k for k, v in zip(pin_list, plants)}
sensor_mappings = {}
inverse_sensor_mappings = {}
manual_control_data = {}

# defining time intervals and schedule
time_interval_list = [50, 30, 25, 15]
water_schedule = ["08", "13", "18"]
sensor_update_timings = ["00", "03", "06", "09", "12", "15", "18", "21"]

# try creating remote handler
try:
    remote = HasuraClient(url=url, headers=headers, U_UUID=U_UUID)
except Exception as e:
    if e.__class__.__name__ == "ConnectionError":
        logging.error("Connection Error, Could not create remote handler.")
    else:
        logging.error(repr(e))
    remote = None

# set the last irrigated value from the file at the start of the script
with open(LAST_IRRIGATED, "r") as f:
    data = f.readline()
last_irrigated = data

# set the last updated sensor values from the file at the start of the script
with open(LAST_SENSOR_DATA_UPDATED, "r") as f:
    data = f.readline()
last_updated_sensor_data = data

# function to set up the board and pins
def setup(pin_list):
    # loop through pins and set mode and state to 'low'
    GPIO.setup(pin_list, GPIO.OUT, initial=GPIO.HIGH)


##################### Sensor Reading Functions Block Start #####################

# function to read temp and humidity in air
def read_DHT22(DHT_sensor, DHT_pin):
    hum, temp = Adafruit_DHT.read(DHT_sensor, DHT_pin)
    if hum is None and temp is None:
        while hum is None and temp is None:
            hum, temp = Adafruit_DHT.read(DHT_sensor, DHT_pin)
            time.sleep(1)
    return hum, temp


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


def collect_data(DHT_sensor, DHT_pin, soil_temp_sensor, sensor_mappings):
    air_humidity, air_temp = read_DHT22(DHT_sensor, DHT_pin)
    soil_moisture = read_avg_soilMoisture(
        10, testing=False, fetch_max=True, fetch_avg=False, ts=0.5
    )
    data_points = []

    for p_id, sensors in sensor_mappings.items():
        soil_temp = soil_temp_sensor.read_1_temp(sensors[0])
        if soil_temp is not None:
            soil_temp = round(soil_temp, 2)
            data_points.append(
                dict(
                    {
                        "timestamp": str(dt.datetime.now()),
                        "soil_temp": soil_temp,
                        "soil_moisture": soil_moisture[sensors[1]],
                        "air_humidity": round(air_humidity, 2),
                        "air_temperature": round(air_temp, 2),
                        "p_uuid": p_id,
                    }
                )
            )
        else:
            logging.error("Soil Temperature Sensor " + sensors[0] + " not found.")

    return data_points


##################### Sensor Reading Functions Block End #####################

##################### Syncronization Functions Block Start #####################

# function to sync the new channel reading values
def sync_irrigation_timings():
    with open(IRRIGATION_TIME) as f:
        data = json.load(f)
    new_timings = [
        value
        for key, value in data["irrigation_timings"][0].items()
        if key != "schedule"
    ]
    print("New timings:")
    pprint(new_timings)
    return new_timings


# adjusts the stack to handle irregular startups
def sync_schedule_stack():
    global water_schedule
    now = int(dt.datetime.now().strftime("%H"))
    water_time_int = [int(time) for time in water_schedule]
    for stack_top in water_time_int:
        if now > stack_top:
            water_schedule.append(water_schedule.pop(0))
        else:
            # print("Final water schedule ", water_schedule)
            return


# function to sync the schedule of watering
def sync_schedule_settings():
    global water_schedule
    global timing_file_last_modified
    modtime = os.stat(IRRIGATION_TIME)[8]
    if (modtime - timing_file_last_modified) > 0:
        print("Timing file modified, updating schedule...")
        with open(IRRIGATION_TIME) as f:
            try:
                data = json.load(f)
                water_schedule = data["irrigation_timings"][0]["schedule"].split(":")
                timing_file_last_modified = modtime
                sync_schedule_stack()
            except Exception as e:
                print("Error Syncing timing file.")
                print(e)


# function to sync the plant to sensor setting
def sync_sensor_status():
    global sensor_mappings
    global sensor_mapping_last_modified
    global inverse_sensor_mappings
    modtime = os.stat(PLANT_STATUS)[8]
    if (modtime - sensor_mapping_last_modified) > 0:
        print("Sensor Status changed, Updating...")
        with open(PLANT_STATUS) as f:
            try:
                data = json.load(f)
                sensor_mappings = {
                    value["p_uuid"]: [
                        value["sensor_mapping"]["temp_sensor"],
                        value["sensor_mapping"]["alias"],
                        value["sensor_mapping"]["pin_num"],
                    ]
                    for value in data["plant_sensor_mapping"]
                }
                inverse_sensor_mappings = {
                    value["sensor_mapping"]["alias"]: {
                        "pin_num": value["sensor_mapping"]["pin_num"],
                        "p_uuid": value["p_uuid"],
                    }
                    for value in data["plant_sensor_mapping"]
                }
                sensor_mapping_last_modified = modtime
                print("Sensor Mappings:")
                pprint(sensor_mappings)
                print("\nInverse Sensor Mappings:")
                pprint(inverse_sensor_mappings)
                print()
            except Exception as e:
                print(e)


# function to sync manual settings from the json file only when the the file has been modified
def sync_manual_settings():
    global manual_mode
    global manual_file_last_modified
    modtime = os.stat(IRRIGATION_MODE)[8]
    if (modtime - manual_file_last_modified) > 0:
        print("\nManual file config modified, updating parameter")
        with open(IRRIGATION_MODE) as f:
            try:
                data = json.load(f)
                manual_mode = data["irrigation_mode"][0]["manual"]
                manual_file_last_modified = modtime
                print("Manual Mode: ", manual_mode)
            except Exception as e:
                print(e)


# function to sync the manual watering timings
def sync_manual_control_settings():
    global manual_control_data
    global manual_control_file_last_modified
    modtime = os.stat(MANUAL_CONTROL)[8]
    if (modtime - manual_control_file_last_modified) > 0:
        print("Manual Control modified, executing...\n")
        with open(MANUAL_CONTROL) as f:
            try:
                data = json.load(f)
                manual_control_data = data["irrigation_mode"][0]
                manual_control_file_last_modified = modtime
                pprint(manual_control_data)
                print()
            except Exception as e:
                print(e)


def reset_manual_ctrl_settings():
    global manual_control_data
    global manual_control_file_last_modified
    # reset the dictionary of settings to 0 seconds and update the file
    for key, value in manual_control_data.items():
        manual_control_data[key] = 0
    with open(MANUAL_CONTROL, "w") as f:
        try:
            f.truncate()
            json.dump({"irrigation_mode": [manual_control_data]}, f)
            manual_control_file_last_modified = os.stat(MANUAL_CONTROL)[8]
            print("Manual Control file reset complete...")
        except Exception as e:
            print("Error in resetting the file")
            print(e)


##################### Syncronization Functions Block End #####################

##################### Some Helper Functions Block Start #####################

# Cleanup function incase of hard exit
def cleanup():
    for i in pin_list:
        GPIO.output(i, GPIO.HIGH)
    GPIO.cleanup()


# function to ring buzzer
def ring_buzzer(tone):
    if tone == "manual":
        ser.write(b"manual\n")
    elif tone == "water":
        ser.write(b"water\n")
    elif tone == "auto":
        ser.write(b"auto\n")


##################### Some Helper Functions Block End #####################

# Iterate over the pin list and irrigate the plants
def irrigate():
    for pin, t in zip(pin_list, time_interval_list):
        GPIO.output(pin, GPIO.LOW)
        # print("Irrigating: " + pin_map[pin] + " for " + str(t) + "s")
        logging.info(" Irrigating: " + pin_map[pin] + " for " + str(t) + "s")
        print(" Irrigating: " + pin_map[pin] + " for " + str(t) + " seconds")
        time.sleep(t)
        GPIO.output(pin, GPIO.HIGH)


# Function to collect all the sensor data and to update it to the remote host using the Hasura Client class


def update_sensor_values():
    global DHT_sensor
    global DHT_pin
    global soil_temp_sensor
    global sensor_mappings
    global remote
    global last_updated_sensor_data

    print(
        (dt.datetime.now().strftime("%H") in sensor_update_timings)
        and (last_updated_sensor_data != dt.datetime.now().strftime("%D %H"))
    )
    # update the sensor values only when the min values are 15 or 45
    if (dt.datetime.now().strftime("%H") in sensor_update_timings) and (
        last_updated_sensor_data != dt.datetime.now().strftime("%D %H")
    ):
        # sync sensor status
        sync_sensor_status()
        ### collect sensor data
        collected_data = collect_data(
            DHT_sensor=DHT_sensor,
            DHT_pin=DHT_pin,
            soil_temp_sensor=soil_temp_sensor,
            sensor_mappings=sensor_mappings,
        )
        print("\nCollected Data:\n")
        pprint(collected_data)
        print()
        try:
            if remote is None:
                remote = HasuraClient(url=url, headers=headers, U_UUID=U_UUID)
            remote.insert_sensor_data(collected_data)
            print("Sensor Data updated...")
            logging.info("Sensor Data Updated . . .")
            # update the last updated data in a file
            last_updated_sensor_data = dt.datetime.now().strftime("%D %H")
            with open(LAST_SENSOR_DATA_UPDATED, "w") as f:
                f.write(last_updated_sensor_data)
            print("Write to last_sensor_data_updated.txt complete...\n")

        except Exception as e:
            print("There was an error in updating the remote...")
            print(e)
            logging.error("Could not update the remote with sensor data")


# main scheduled irrigation function
def water_by_schedule():
    global time_interval_list
    global last_irrigated
    global water_schedule
    global remote
    global network_status
    global DHT_sensor
    global DHT_pin
    global soil_temp_sensor
    global sensor_mappings
    global auto_control_flag

    # update the water schedule timings and then check
    sync_schedule_settings()

    if not auto_control_flag:
        print("\nSwitched to auto Mode...\n")
        time.sleep(2)
        ring_buzzer("auto")
        auto_control_flag = True

    if (
        dt.datetime.now().strftime("%H") == water_schedule[0]
        and last_irrigated != dt.datetime.now().strftime("%D ") + water_schedule[0]
    ):

        ### Syncing Phase Start ###
        logging.info("syncing...")
        print("\nSyncing irrigation timings...")
        time_interval_list = sync_irrigation_timings()
        time.sleep(0.5)

        sync_sensor_status()
        ### Syncing Phase End ###

        ### Data Collection Phase Start ###

        # collected_data = collect_data(
        #     DHT_sensor=DHT_sensor,
        #     DHT_pin=DHT_pin,
        #     soil_temp_sensor=soil_temp_sensor,
        #     sensor_mappings=sensor_mappings,
        # )

        # perfom decisions and pass the irrigation list to the function here

        ### Irrigation Phase Start ###
        logging.info("Irrigating")
        print("\nIrrigating...")

        # notify the user of the start of irrigation.
        try:
            ring_buzzer("water")
        except Exception as e:
            logging.error("Can't write to serial port /dev/ttyACM0 not connected")
            print("Can't write to serial port /dev/ttyACM0 not connected!")

        irrigate()
        print("\nIrrigation complete...")
        ### Irrigation Phase End ###

        # update the last_irrigated variable to avoid repeated watering on same day at the same hour
        last_irrigated = dt.datetime.now().strftime("%D %H")
        with open(LAST_IRRIGATED, "w") as f:
            f.write(last_irrigated)
        print("Write to last_irrigated.txt complete...")

        # update the watering time array
        water_schedule.append(water_schedule.pop(0))
        print("Update to Schedule Stack complete...")

        ### Remote Update Phase Start ###
        try:
            if remote is None:
                remote = HasuraClient(url=url, headers=headers, U_UUID=U_UUID)
            remote.update_irrigation_log(time=str(dt.datetime.now()), mode="Automatic")
            print("Update to remote complete...")
            network_status = True

        except Exception as e:
            with open(PENDING_UPDATE, "a") as f:
                f.write(str(dt.datetime.now()) + "\n")
            logging.error("Connection error, could not update the remote log.")
            print("Connection error, could not update the remote log...")
            print(e)
            logging.error(repr(e))
            return
        ### Remote Update Phase End ###

        if network_status:
            ### Pending Updates Upload Phase Start ###
            try:
                # Update the remote with any pending updates to be made
                with open(PENDING_UPDATE, "r+") as f:
                    pending = f.readlines()
                    # print("before modification, ",pending)
                    if len(pending) != 0:
                        print("Pending updates found, updating the remote...")
                        pending = [time.replace("\n", "").strip() for time in pending]
                        # print("after modification, ",pending)
                        for _ in range(len(pending)):
                            remote.update_irrigation_log(
                                time=pending[0], mode="Automatic"
                            )
                            time.sleep(1)
                            pending.pop(0)
                        f.truncate(0)
                network_status = False
            except Exception as e:
                print(e)
            ### Pending Updates Upload Phase End ###

    else:
        if last_irrigated == dt.datetime.now().strftime("%D ") + water_schedule[0]:
            water_schedule.append(water_schedule.pop(0))
        # snooze_time = 60*(60 - int(dt.datetime.now().strftime("%M"))) - int(dt.datetime.now().strftime("%S"))
        # print("sleeping for ",snooze_time)
        # time.sleep(snooze_time)


# function to irrigate a particular pin for a particular time
def irrigate_1(pin, t):
    GPIO.output(pin, GPIO.LOW)
    print("Irrigating: " + pin_map[pin])
    time.sleep(t)
    GPIO.output(pin, GPIO.HIGH)


# function to water the plant manually
def manual_watering():
    global manual_control_flag
    global manual_control_data
    global sensor_mappings
    global inverse_sensor_mappings
    global remote

    if not manual_control_flag:
        time.sleep(2)
        print("\nSwitched to manual Mode")
        ring_buzzer("manual")
        manual_control_flag = True

    sync_manual_control_settings()

    # if the count of zeroes in the value field of the manual settings is not equal to the number of channels
    # then perform irrigation on the field which has the value
    if list(manual_control_data.values()).count(0) != len(manual_control_data.values()):
        to_irrigate = dict(
            filter(lambda elem: elem[1] != 0, manual_control_data.items())
        )
        # print(list(to_irrigate.keys())[0])
        # pprint(inverse_sensor_mappings)
        pin_num = inverse_sensor_mappings[list(to_irrigate.keys())[0]]["pin_num"]
        print("Irrigating the pin requested: ", pin_num)
        try:
            assert isinstance(pin_num, int), "Pin number not an Integer"
            assert isinstance(
                list(to_irrigate.values())[0], int
            ), "Entered time is not an Integer"
            irrigate_1(pin_num, list(to_irrigate.values())[0])
        except Exception as e:
            print("Error orrurred while trying to irrigate pin: ", pin_num)
            print(e)

        # after irrigation it is important to update the file with all the entries as zeores
        reset_manual_ctrl_settings()

        ### Remote Update Phase Start ###
        try:
            if remote is None:
                remote = HasuraClient(url=url, headers=headers, U_UUID=U_UUID)
            remote.update_irrigation_log(time=str(dt.datetime.now()), mode="Manual")
            print("Update to remote complete...")

        except Exception as e:
            logging.error("Connection error, could not update the remote log.")
            print("Connection error, could not update the remote log...")
            logging.error(repr(e))
            return
        ### Remote Update Phase End ###


if __name__ == "__main__":
    try:
        # run these commands to enable/start onewire communication
        os.system("modprobe w1-gpio")
        os.system("sudo modprobe w1-therm")

        # Initialize all the pins
        setup(pin_list)
        print("Starting Irrigation Module with following settings:\n")
        pprint("U_UUID: " + U_UUID)
        print()
        pprint("URL: " + url)
        print()

        # perform initial sync so that latest data can be used to perform irrigation
        # if no internet available then the script will use default settings and perfom automatic irrigation to all valves
        sync_schedule_settings()
        print("Water Schedule:")
        pprint(water_schedule)
        print()

        # sync the Sensor status from the file
        # sync_sensor_status()

        # main loop
        while True:
            # regularly check for manual mode enable/disable signal
            sync_manual_settings()

            # keep track of sensor mappings
            # update_sensor_values()

            # if the user sets the garden to auto mode then onlu execute this block of code else perform manual watering
            if not manual_mode:
                water_by_schedule()
                manual_control_flag = False
            else:
                manual_watering()
                auto_control_flag = False
        cleanup()
    except KeyboardInterrupt:
        print("Quit")
        # Reset GPIO settings
        cleanup()
        quit()
