from network import WLAN
from mqtt import MQTTClient
import machine
import pycom
import gc

import time

wlan = WLAN(mode=WLAN.STA)

nets = wlan.scan()
for net in nets:
    if net.ssid == 'tulgaa-ThinkPad-Edge-E540':
        print('Network found!')
        wlan.connect(net.ssid, auth=(net.sec, 'cMF9d70Z'))
        while not wlan.isconnected():
            machine.idle() # save power while waiting
        print('WLAN connection succeeded!')
        break
    else:
        print("Network not found!")
        time.sleep(1) 
print("Connected to Wifi\n")
client = MQTTClient("WiPy1", "127.0.0.1", port=1883) # Enter the IP Address
client.settimeout = settimeout
client.set_callback(sub_cb)
client.connect()
print("Connected to Client\n")