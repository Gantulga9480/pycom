# Github Gantulga1234
from network import WLAN
from mqtt import MQTTClient
import machine
import time
import pycom
from lib.GridEye import GridEye

SENSOR_START = False
TRY = True
SENSOR = 5

def sub_cb(topic, msg):
    global SENSOR_START, TRY
    if msg == b'2':
        SENSOR_START = True
        time.sleep(0.1)
        pycom.rgbled(0x00ff00)
        time.sleep(0.1)
    elif msg == b'1':
        SENSOR_START = False
        time.sleep(0.1)
        pycom.rgbled(0x0000ff)
        time.sleep(0.1)
    elif msg == b'0':
         TRY = False

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

# client connection
client = MQTTClient("wipy{}".format(SENSOR), "192.168.1.2", port=1883) 
client.set_callback(sub_cb)
client.connect()
# client connected
time.sleep(0.1)
pycom.rgbled(0x0000ff)
time.sleep(0.1)
client.subscribe(topic="wipy/sensor-start", qos=0)
time.sleep(0.1)
# using GridEye to get readings
ge = GridEye()
time.sleep(5)

int_table= ge.get_interrupts(reset=True)

time.sleep(5)
ge.get_states()
ge.get_interrupts(reset=True)
time.sleep(5)
ge.get_interrupts(reset=True)
ge.get_states()

# return a 8x8 matrix + min&max heats out of them
image = ge.get_sensor_data()
ge.reset(flags_only=True)
time.sleep(0.1)

count = 0
# Publishing data
while TRY:
    if SENSOR_START:
        count = count + 1
        # return a 8x8 matrix + min&max heats out of them
        try:
            image = ge.get_sensor_data()
        except:
            client.publish("sensors/sensor{}/status".format(SENSOR), "d")
        image_data=str(image[0])
        if (count>2):
            if count == 23:
                client.publish("sensors/sensor{}/status".format(SENSOR), "c")
                count = 3
            # publish image_data to "sensors/sensor1" topic
            client.publish("sensors/sensor{}/data".format(SENSOR), image_data)
        else:
            client.publish("sensors/sensor{}/status".format(SENSOR), "c")
            time.sleep(0.1)
    else:
        count = 0
        client.publish("sensors/sensor{}/status".format(SENSOR), "w")
        time.sleep(1)
    client.check_msg()
# client disconnected
client.publish("sensors/sensor{}/status".format(SENSOR), "d")
time.sleep(0.1)
pycom.rgbled(0xff0000)
time.sleep(1)
