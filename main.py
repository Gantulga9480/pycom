from network import WLAN
import machine
import pycom
import gc
import csv

import time
from lib.GridEye import GridEye

color = [0x330033, 0x003300, 0x000033]

pycom.heartbeat(False)  # make sure that the led is off
time.sleep(0.1)         # Workaround for a bug.
pycom.rgbled(0xff0000)  # Status red = not working
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
image = ge.get_sensor_data("GRAYIMAGE")

ge.reset(flags_only=True)
print("Done!")
count = 0

# continuous reading
while True:

    # count = count + 1
    image = ge.get_sensor_data("GRAYIMAGE")
    try:    
        for i in range(len(image[0])):
            for j in range(len(image[1])):
                pass
    except:
        pass
    time.sleep(1)
