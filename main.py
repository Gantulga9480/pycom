# Github Gantulga1234
from network import WLAN
from mqtt import MQTTClient
import machine
import time
import pycom
from lib.GridEye import GridEye

SENSOR = 6

def sub_cb(topic, msg):
    pass

# Wifi not connected
pycom.heartbeat(False)
time.sleep(0.1)
pycom.rgbled(0xff0000)
time.sleep(0.1)

# Wifi connection
wlan = WLAN(mode=WLAN.STA)
wlan.connect("TP-Link_5FF2", auth=(WLAN.WPA2, "12345678Aa")) 
while not wlan.isconnected():  
    machine.idle()

# client connection
client = MQTTClient("wipy{}".format(SENSOR), "192.168.1.60", port=1883) 
client.set_callback(sub_cb)
client.connect()
client.publish(topic="sensor/status", msg="{} connected".format(SENSOR), retain=False, qos=0)
# using GridEye to get readings
ge = GridEye()
ge.reset(flags_only=True)
time.sleep(0.1)
pycom.rgbled(0x00ff00)
time.sleep(0.1)
count = 0
connected = True
# Publishing data
while True:
    count = count + 1
    try:
        image = ge.get_sensor_data()
    except:
        break
    image_data=str(image[0])
    if (count>3):
        if count == 33:
            count = 4
        client.publish("sensors/sensor{}/data".format(SENSOR), image_data)
        time.sleep(0.001)
    else:
        time.sleep(0.1)
# client disconnected
time.sleep(0.1)
pycom.rgbled(0xff0000)
time.sleep(5)
