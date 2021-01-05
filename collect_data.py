#temperature (Air & Humidity)
import Adafruit_DHT

# soil temperature sensors
from ds18b20 import DS18B20
import time

# initialize sensors

# DHT22
DHT_sensor = Adafruit_DHT.DHT22
DHT_pin = 4

# ds18b20
try:
    s = DS18B20()
    s.find_sensors()
except KeyboardInterrupt:
    print("Keyboard interrupt")


# function to read temp and humidity in
def read_DHT22():
    hum, temp = Adafruit_DHT.read(DHT_sensor, DHT_pin)
    time.sleep(2)
    return hum, temp


def read_DS18B20():
    s.read_temp()
    soil_temp = []
    for t, n, c, f in s.log:
        soil_temp.append((n, t, c))
    return soil_temp


def collect_data():
    air_hum, air_temp = read_DHT22()
    collected_soil_temp_data = read_DS18B20()
    pots = []
    for pot in collected_soil_temp_data:
        temporary = {"timestamp": pot[1], "soil_temp": pot[2], "soil_moisture": 67,
                     "air_humidity": air_hum, "air_temperature": air_temp, "light_intensity": 90}
        pots.append(temporary)
