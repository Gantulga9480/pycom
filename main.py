# Github Gantulga1234
from network import WLAN 
from mqtt import MQTTClient 
import machine 
import time
import pycom
from lib.GridEye import GridEye

def sub_cb(topic, msg): 
   print(msg)

pycom.heartbeat(False)
time.sleep(0.1)
pycom.rgbled(0xff0000)
wlan = WLAN(mode=WLAN.STA)
wlan.connect("Univision_83A3", auth=(WLAN.WPA2, "88640783"), timeout=5000) 
while not wlan.isconnected():  
    machine.idle()

# Wifi connected
time.sleep(0.1)
pycom.rgbled(0x7D7D00)
 
client = MQTTClient("wipy1", "192.168.1.2", port=1883) 
client.set_callback(sub_cb) 
client.connect()
# client connected
time.sleep(0.1)
pycom.rgbled(0xffff00)
time.sleep(0.1)
client.publish("status/sensor", "s-1")

# using GridEye to get readings
ge = GridEye()
time.sleep(1)
# int_table= ge.get_interrupts(reset=True)
# time.sleep(1)
# ge.get_states()
# ge.get_interrupts(reset=True)
# time.sleep(1)
# ge.get_interrupts(reset=True)
# ge.get_states()

# return a 8x8 matrix + min&max heats out of them
# image = ge.get_sensor_data("GRAYIMAGE")

ge.reset(flags_only=True)
count = 0
time.sleep(0.1)
pycom.rgbled(0x00ff00)

# Publishing data
while True:
    count = count + 1
    # return a 8x8 matrix + min&max heats out of them
    image = ge.get_sensor_data("GRAYIMAGE")
    # convert it to string to extract usefull info only [8x8 matrix]
    # image_data=str(image[0])
    # remove non-usefull informations
    # string_matrix=image_data[1:len(image_data)]
    # string_matrix=string_matrix.rsplit(",", 2)[0]
    if (count>2):
        # publish string_matrix to "sensors/sensor1" topic
        client.publish("sensors/sensor1", image[0])
        # time.sleep(0.1)
    else:
        time.sleep(1)
time.sleep(1)
