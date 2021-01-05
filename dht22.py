import Adafruit_DHT
import time

DHT_sensor = Adafruit_DHT.DHT22
DHT_pin = 18

while True:
    hum, temp = Adafruit_DHT.read(DHT_sensor, DHT_pin)
    if hum is not None and temp is not None:
        print("Temp={0:0.1f}C Humidity={1:0.1f}%".format(temp, hum))
    else:
        print("Sensor failure. Check wiring.")
    time.sleep(3)
