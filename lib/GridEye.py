#!/usr/bin/python
from machine import I2C
from network import Bluetooth
from machine import Timer
import math
from machine import Pin
import time
import pycom
from machine import RTC
from time import sleep

UPPER_LEVEL=40
LOWER_LEVEL=0
HYSTERESIS_LEVEL= 35
FPS = 10

ABSOLUTE_MODE = True
DIFFERENCE= 5
DIFFERENCE_RAW = True

modes = {0x00: "NORM", 0x10: "SLEEP", 0x20: "STANDBY60", 0x21: "STANDBY10"}

class GridEye():
	"""
	GridEye class for easy handling of GridEYE AMG88 i2c modules.
	Although Grid-EYE%20SPECIFICATIONS(Reference).pdf may still be helpful.
	TODO: Interrupts
	"""
	def __init__(self, i2c_address=0x69, i2c_bus = I2C(0, I2C.MASTER, baudrate=400000, pins=('P10','P11'))):
		self.i2c = {"bus": i2c_bus, "address": i2c_address}
		# print("hello 1")
		self.readfrom_mem = self.i2c["bus"].readfrom_mem
		# print("hello 2")
		self.writeto_mem = self.i2c["bus"].writeto_mem
		# print("hello 3")

		self.modes = {0x00: "NORM",
					  0x10: "SLEEP",
					  0x20: "STANDBY60",
					  0x21: "STANDBY10"
					 }
		self.reset()
		self.set_mode()
		self.set_interupt_ctrl(enabled=False)
		self.clear_states(interrupt=True, temp_overflow=True, thermistor_overflow=True)
		self.set_fps(fps=FPS)
		self.set_interrupt_limits(lower_limit=LOWER_LEVEL, upper_limit= UPPER_LEVEL, hysteresis_level = HYSTERESIS_LEVEL)
		self.set_interupt_ctrl(mode= ABSOLUTE_MODE, enabled = False)
		self.prelist=[[0 for x in range(8)] for y in range(8)]

	def get_mode(self):
		mode = self.readfrom_mem(self.i2c["address"], 0x00, 1)
		print(mode)
		return self.modes.get(mode)

	def set_mode(self, mode="NORM"):
		if isinstance(mode, str):
			mode = {v: k for k, v in self.modes.items()}.get(mode)
		self.writeto_mem(self.i2c["address"], 0x00, mode)

	def reset(self, flags_only=False):
		if flags_only:
			reset = 0x30
		else:
			reset = 0x3F
		self.writeto_mem(self.i2c["address"], 0x01, reset)

	def get_fps(self):
		fps = self.readfrom_mem(self.i2c["address"], 0x02, 1)
		if fps == b'\x00':
			return 10
		elif fps ==  b'\x01':
			return 1

	def set_fps(self, fps=10):
		if fps == 10:
			fps = 0x00
		else:
			fps = 0x01
		self.writeto_mem(self.i2c["address"], 0x02, fps)

	def get_interrupt_ctrl(self):
		"""
		returns a boolean tuple (interupt_enabled, interupt_mode)
		"""
		intc = self.readfrom_mem(self.i2c["address"], 0x03, 1)

		return ((intc == b'\x01') or (intc == b'\x03')), ((intc == b'\x02') or (intc == b'\x03'))

	def set_interupt_ctrl(self, enabled=False, mode=False):
		"""
		mode = False -> difference mode
		mode = True  -> absolute mode
		"""
		intc = 0x00
		if mode:
			intc += 2
		if enabled:
			intc += 1
		self.writeto_mem(self.i2c["address"], 0x03, intc)

	def get_states(self):
		"""
		returns a tuple of (
			Interrupt Outbreak,
			Temperature Output Overflow,
			Thermistor Temperature Output Overflow
			)
		from 0x04
		"""
		state = self.readfrom_mem(self.i2c["address"], 0x04, 1)
		print('status regiser:',state)
		#return (1 & state is 1), (2 & state is 2), (4 & state is 4)

	def clear_states(self, interrupt=False, temp_overflow=False, thermistor_overflow=False):
		clear = 0x00
		if interrupt:
			clear += 1
		if temp_overflow:
			clear += 2
		if thermistor_overflow:
			clear += 4
		self.writeto_mem(self.i2c["address"], 0x05, clear)

	def set_moving_average(self, twice=False):
		if twice:
			value = 0x20
		else:
			value = 0
		self.writeto_mem(self.i2c["address"], 0x07, value)

	def set_interrupt_limits(self, lower_limit, upper_limit, hysteresis_level):
		lower_limit = split_in_2bytes(int(lower_limit*4))
		upper_limit = split_in_2bytes(int(upper_limit*4))
		hysteresis_level = split_in_2bytes(int(hysteresis_level*4))
		self.writeto_mem(self.i2c["address"], 0x08, upper_limit[1])
		self.writeto_mem(self.i2c["address"], 0x09, upper_limit[0])

		self.writeto_mem(self.i2c["address"], 0x0A, lower_limit[1])
		self.writeto_mem(self.i2c["address"], 0x0B, lower_limit[0])
		if hysteresis_level:
			self.writeto_mem(self.i2c["address"], 0x0C, hysteresis_level[1])
			self.writeto_mem(self.i2c["address"], 0x0D, hysteresis_level[0])

	def get_interrupts(self, reset=False):
		"""
		Returns current interrupts and optionally resets the interrupt table.
		Format is a list of tuples (line, pixel in line)
		"""
		interrupts = []
		data = self.readfrom_mem(self.i2c["address"], 0x10, 8)
		for i in range(8):
			for bit in range(8):
				if data[i] & 1<<bit != 0:
					interrupts.append((i, bit))
		if reset:
			self.clear_states(interrupt=True)
		return interrupts

	def get_thermistor_temp(self, raw=False):
		"""
		returns the thermistor temperature in .25C resolution
		TODO: high res option with possible 0.0625 resolution
		"""
		upper = self.readfrom_mem(self.i2c["address"], 0x0E, 2)

		upperh = upper[1] << 8
		complete = upperh + upper[0]
		if complete & 2048:
			complete = complete - 2048
			complete = -complete
		if not raw:
			return complete / 4
		else:
			return complete / 16

	def get_sensor_data(self, interrupt=True):
		"""
		returns the sensor data, supporting different modes
		"TEMP" -> [8][8] Array of temp values
		"GRAYIMAGE" -> a 8x8 pixel image with optional remapping
		+
		min, max values as [value, x,y]
		NOTE: READ is done per line. the raspberry pi doesn't like reading 128
		bytes at once.
		"""
		lines = []
		minv = 500
		maxv = -500
		canSend = False
		for line in range(8):
			offset = 0x80+line*16
			block = self.readfrom_mem(self.i2c["address"], offset, 16)
			values = []
			for i in range(0, 16, 2):
				upper = block[i+1] << 8
				lower = block[i]
				val = upper + lower
				if 2048 & val == 2048:
					val = -(val - 2048)
				val = val/4
				"""if val < minv[0]:
					minv = [val, i//2, line]
				if val > maxv[0]:
					maxv = [val, i//2, line]"""
				if val < minv:
					minv = val
				if val > maxv:
					maxv = val
				values.append(float(val))
			values.reverse()
			lines.append(values)
		if maxv < 1:
			return None
		if interrupt:

			if ABSOLUTE_MODE == False:
				int_t =[x[:] for x in [[0] * 8] * 8]
				got = False
				pos = self.get_interrupts(True)
				for x,y in pos:
						if math.fabs(self.prelist[x][y] - lines[x][y]) > DIFFERENCE:
							int_t[x][y] = 1
							got = True
				self.prelist = lines
				if got and DIFFERENCE_RAW:
					return (int_t, 0, 1)
				if got and not DIFFERENCE_RAW:
					return (lines, minv, maxv)
				if not got:
					return None
			else:
				return (lines, minv, maxv)
		else:
			if ABSOLUTE_MODE == False:
				int_t =[x[:] for x in [[0] * 8] * 8]
				got = False
				for x in range(8):
					for y in range(8):
						if math.fabs(self.prelist[x][y] - lines[x][y]) > DIFFERENCE:
							int_t[x][y] = 1
							got = True
				self.prelist = lines
				if got and DIFFERENCE_RAW:
					return (int_t, 0, 1)
				if got and not DIFFERENCE_RAW:
					return (lines, minv, maxv)
				if not got:
					return None
			else:
				if maxv >= UPPER_LEVEL:
					return (lines, minv, maxv)
				if minv <= LOWER_LEVEL:
					return (lines, minv, maxv)


def int2twoscomplement(value, bits=12):
	"""returning a integer which is equal to value as two's complement"""
	if value > 0:
		return value
	else:
		value = -value
		return (1 << bits) + value
def split_in_2bytes(value, bits=8):
	"""
	Returns a tuple with 2 integers (upper,lower) matching the according bytes
	The AMG88 usually uses 2 byte to store 12bit values.
	"""
	upper = 0x00
	lower = 0x00
	upper = (value) >> bits
	lower = (value) & 0xFF
	return (upper, lower)

def maprange(a, b, s):
	"""remap values linear to a new range"""
	(a1, a2), (b1, b2) = a, b
	return b1 + ((s - a1) * (b2 - b1) / (a2 - a1))

if __name__ == '__main__':
	print("in main of grideye")
