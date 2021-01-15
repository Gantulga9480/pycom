# Github Gantulga1234
from network import WLAN 
from mqtt import MQTTClient 
import machine 
import gc
import time
import pycom
from lib.GridEye import GridEye

SENSOR_START = False
SENSOR = 2

def sub_cb(topic, msg):
    global SENSOR_START
    print(msg)
    data = msg.payload.encode("utf-8")
    if data == "1":
        SENSOR_START = True
    else:
        SENSOR_START = False

# Wifi not connected
pycom.heartbeat(False)
time.sleep(0.1)
pycom.rgbled(0xff0000)
time.sleep(0.1)

# Wifi connection
wlan = WLAN(mode=WLAN.STA)
wlan.connect("Univision_83A3", auth=(WLAN.WPA2, "88640783")) 
while not wlan.isconnected():  
    machine.idle()
time.sleep(0.1)
pycom.rgbled(0x7D7D00)
time.sleep(0.1)
 
# client connection
client = MQTTClient("wipy1", "192.168.1.2", port=1883) 
client.set_callback(sub_cb) 
client.connect()
# client connected
time.sleep(0.1)
pycom.rgbled(0xffff00)
time.sleep(0.1)
client.publish("status/sensor", "s-{}-c".format(SENSOR))
client.subscribe(topic="wipy/sensor-start")
time.sleep(0.1)
while not SENSOR_START:
    client.publish("status/sensor", "sensor-{} waiting".format(SENSOR))
    time.sleep(1)

# using GridEye to get readings
ge = GridEye()
ge.reset(flags_only=True)
time.sleep(0.1)

time.sleep(0.1)
pycom.rgbled(0x00ff00)
time.sleep(0.1)
count = 0
# Publishing data
while SENSOR_START:
    count = count + 1
    # return a 8x8 matrix + min&max heats out of them
    image = ge.get_sensor_data("GRAYIMAGE")
    image_data=str(image[0])
    if (count>2):
        # publish image_data to "sensors/sensor1" topic
        client.publish("sensors/sensor{}".format(SENSOR), image_data)
        count = 3
        time.sleep(0.1)
    else:
        time.sleep(0.1)
    client.check_msg()
# client disconnected
client.publish("status/sensor", "s-{}-d".format(SENSOR))
time.sleep(0.1)
pycom.rgbled(0xff0000)
time.sleep(1)
