#!/usr/bin/python3
import RPi.GPIO as GPIO
import serial

import time
import datetime as dt
import logging
import json
import socket
import os

from hasura import HasuraClient

# set GPIO Mode to BCM
GPIO.setmode(GPIO.BCM)

# base dir and paths
BASE_DIR = os.getcwd()
IRRIGATION_LOG = os.path.join(BASE_DIR, 'logs/irrigation.log')
LAST_IRRIGATED = os.path.join(BASE_DIR, "logs/last_irrigated.txt")
IRRIGATION_TIME = os.path.join(BASE_DIR, "logs/irrigation_time.json")
IRRIGATION_MODE = os.path.join(BASE_DIR, "logs/irrigation_mode.json")
PENDING_UPDATE = os.path.join(BASE_DIR, "logs/pending_update.txt")

# set up logging configuration
logging.basicConfig(filename=IRRIGATION_LOG , level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# declare imp variables

U_UUID = "0538f99b-b6b3-4c78-8b37-da93249fd4f0"
url = "https://relieved-asp-16.hasura.app/v1/graphql"
headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwNTM4Zjk5Yi1iNmIzLTRjNzgtOGIzNy1kYTkzMjQ5ZmQ0ZjAiLCJpYXQiOjE2MDQ5MTQ3OTEuOTUyLCJlbWFpbCI6InJhc2htaWxwODMzQGdtYWlsLmNvbSIsInJvbGVzIjpbInVzZXIiXSwiaHR0cHM6Ly9oYXN1cmEuaW8vand0L2NsYWltcyI6eyJ4LWhhc3VyYS1hbGxvd2VkLXJvbGVzIjpbInVzZXIiXSwieC1oYXN1cmEtZGVmYXVsdC1yb2xlIjoidXNlciIsIngtaGFzdXJhLXVzZXItaWQiOiIwNTM4Zjk5Yi1iNmIzLTRjNzgtOGIzNy1kYTkzMjQ5ZmQ0ZjAiLCJ4LWhhc3VyYS1vcmctaWQiOiJnYXJkdWlubyIsIngtaGFzdXJhLWFkbWluLXNlY3JldCI6ImFkbWluLXNlY3JldCJ9LCJleHAiOjE2MzY0NTA3OTF9.2HJ14CJ1ShUsU7YqqsD3smRKbx2FJjF_xI6vG1-ZKBc'}

# flags
first_run = True
manual_mode = False
dummy = False
network_status = False

# get last modified time in seconds at the start of the script
manual_file_last_modified = 0
timing_file_last_modified = 0

try:
    # set up serial communication on port ACM0 at 9600 baud rate
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    ser.flush()
except Exception as e:
    print("Arduino not present at /dev/ttyACM0")
    logging.error("Arduino not present at /dev/ttyACM0")

# init list with pin numbers
pin_list = [21, 20, 16, 26]
plants = ["Hall", "Tomato:Raddish:Tulsi", "Pepper", "Ajma:Dragon_F"]

# pin mapping
pin_map = {k: v for k, v in zip(pin_list, plants)}
inverse_pin_map = {v: k for k, v in zip(pin_list, plants)}

# defining time intervals and schedule
time_interval_list = [50, 30, 25, 15]
water_schedule = ["08","13", "18"]

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
with open(LAST_IRRIGATED,"r") as f:
    data = f.readline()
last_irrigated = data

# function to set up the board and pins
def setup(pin_list):
    # loop through pins and set mode and state to 'low'
    GPIO.setup(pin_list, GPIO.OUT, initial=GPIO.HIGH)

# function to sync the new channel reading values
def sync_irrigation_timings():
    with open(IRRIGATION_TIME) as f:
        data = json.load(f)
    new_timings = [value for key,value in data["irrigation_timings"][0].items() if key != "schedule"]
    print("New timings ",new_timings)
    return new_timings

# function to sync manual settings from the json file only when the the file has been modified
def sync_manual_settings():
    global manual_mode
    global manual_file_last_modified
    modtime = os.stat(IRRIGATION_MODE)[8]
    if (modtime - manual_file_last_modified) > 0: 
        print("Manual file config modified, updating parameter")   
        with open(IRRIGATION_MODE) as f:
            try:
                data = json.load(f)
                manual_mode = data["irrigation_mode"][0]["manual"]
                manual_file_last_modified = modtime
                print("Manual Mode: ", manual_mode)
            except Exception as e:
                print(e)

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
        print("Timing file modified, updating schedule")
        with open(IRRIGATION_TIME) as f:
            try:
                data = json.load(f)
                water_schedule = data["irrigation_timings"][0]["schedule"].split(":")
                timing_file_last_modified = modtime
                sync_schedule_stack()
            except Exception as e:
                print("Error Syncing timing file")
                print(e)

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

# Iterate over the pin list and irrigate the plants
def irrigate():
    for pin, t in zip(pin_list, time_interval_list):
        GPIO.output(pin, GPIO.LOW)
        # print("Irrigating: " + pin_map[pin] + " for " + str(t) + "s")
        logging.info(" Irrigating: " + pin_map[pin] + " for " + str(t) + "s")
        print(" Irrigating: " + pin_map[pin] + " for " + str(t) + "s")
        time.sleep(t)
        GPIO.output(pin, GPIO.HIGH)

# main scheduled irrigation
def water_by_schedule():
    global time_interval_list
    global last_irrigated
    global water_schedule
    global remote
    global network_status
    
    # updete the water schedule timings and then check 
    sync_schedule_settings()
    if dt.datetime.now().strftime("%H") == water_schedule[0] and last_irrigated != dt.datetime.now().strftime("%D ") + water_schedule[0]:
        
        ### Syncing Phase Start ###
        logging.info("syncing...")
        print("Syncing irrigation timings...")
        time_interval_list = sync_irrigation_timings()
        time.sleep(0.5)
        ### Syncing Phase End ###

        ### Irrigation Phase Start ###
        logging.info("Irrigating")
        print("Irrigating")

        # notify the user of the start of irrigation.
        try:
            ring_buzzer("water")
        except Exception as e:
            logging.error("Can't write to serial port /dev/ttyACM0 not connected")
            print("Can't write to serial port /dev/ttyACM0 not connecte")
        
        irrigate()
        print("Irrigation complete")
        ### Irrigation Phase End ###

        # update the last_irrigated variable to avoid repeated watering on same day at the same hour
        last_irrigated = dt.datetime.now().strftime("%D %H")
        with open(LAST_IRRIGATED,"w") as f:
            f.write(last_irrigated)
        print("Write to last_irrigated.txt complete")

        # update the watering time array
        water_schedule.append(water_schedule.pop(0))
        print("Update to Schedule Stack complete")

        ### Remote Update Phase Start ###
        try:
            if remote is None:
                remote = HasuraClient(url=url, headers=headers, U_UUID=U_UUID)
            remote.update_irrigation_log(time=str(dt.datetime.now()))
            print("Update to remote complete")
            network_status = True

        except Exception as e:
            with open(PENDING_UPDATE,"a") as f:
                f.write(str(dt.datetime.now()) + "\n")
            logging.error("Connection error, could not update the remote log.")
            print("Connection error, could not update the remote log")
            logging.error(repr(e))
            return
        ### Remote Update Phase End ###

        if network_status:
            ### Pending Updates Upload Phase Start ###
            try:
                # Update the remote with any pending updates to be made
                with open(PENDING_UPDATE,"r+") as f:
                    pending = f.readlines()
                    # print("before modification, ",pending)
                    if len(pending) != 0:
                        print("Pending updates found, updating the remote.")
                        pending = [time.replace("\n","").strip() for time in pending]
                        # print("after modification, ",pending)
                        for _ in range(len(pending)):
                            remote.update_irrigation_log(time=pending[0])
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
    global dummy
    if not dummy:
        print("Switched to manual Mode")
        ring_buzzer("manual")
        dummy = True


if __name__ == "__main__":
    try:
        setup(pin_list)
        print("Starting...")
        sync_schedule_settings()
        print("Water Schedule: ",water_schedule)
        # main loop 
        while True:
            sync_manual_settings()
            if not manual_mode:
                water_by_schedule()
                dummy = False
            else:
                manual_watering()

        # water_by_schedule()
        # irrigate()
        # irrigate_1(21, 5)
        # irrigate_1(20, 5)
        # irrigate_1(16, 5)
        # irrigate_1(26, 5)
        cleanup()
    except KeyboardInterrupt:
        print("Quit")
        # Reset GPIO settings
        cleanup()
        quit()
