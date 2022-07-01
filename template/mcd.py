import serial
import serial.tools.list_ports

from enum import IntEnum, IntFlag
from enum import auto as en_auto
from functools import reduce
from operator import or_
from typing import List

###########################
# Shift Register state code
###########################
class State(IntEnum):
	SET   = 0x01
	RESET = 0x00

	def __eq__(self, other):
		if other == b'\x01' or other == True:
			return int(self) == 1
		elif other == b'\x00' or other == False:
			return int(self) == 0
		
		raise ValueError(f"Invalid comparaison between a state and an unknown value '{other}'")

###################
# C enums and flags
###################

# Command list
class CMD(IntEnum):
	SET_SR     = 0
	SET_CS     = en_auto()

	CLK        = en_auto()

	ACK_MODE   = en_auto()

	DEBUG_ECHO = en_auto()
	DEBUG_LED  = en_auto()

CMD_LIST  = list(CMD.__members__.values())
CMD_COUNT = len(CMD_LIST)

# Acknowledge Mode Flags
class ACK(IntFlag):
	NONE      = 0x00
	SET_SR    = en_auto()
	SET_CS    = en_auto()
	CLK       = en_auto()

ACK_LIST = list(ACK.__members__.values())
ACK_ALL = reduce(or_, ACK_LIST)

# Control Signals
class CS(IntEnum):
	DUMMY = 0
	
CS_LIST  = list(CS.__members__.values())
CS_COUNT = len(CS_LIST)

### END C enums and flags ###

#################
# Utils function
#################
def as_int(b: bytes) -> int:
	return int.from_bytes(b, 'little')

def as_bytes(i: int) -> bytes:
	return i.to_bytes(max((i.bit_length() + 7) // 8, 1), 'little')

##############
# Driver class
##############
class MCDriver:
	"""
	µc driver for the Awesome Array Python Driver.

	Attributes
	-----------
	ser : serial.Serial
		serial port associated with the µc

	uc_ack_mode : ACK
		stores the actual ack_mode of the µc
	
	"""
	DEFAULT_PID = 22336

	def __new__(cls, *args, **kwargs):
		self = super().__new__(cls)  

		def gen_command_fn(command):
			return lambda *c_args: self.call_command(command, *c_args)

		for cmd in CMD.__members__:
			setattr(self, cmd.lower(), gen_command_fn(CMD.__members__[cmd]))

		return self

	def __init__(self, pid = DEFAULT_PID):
		"""
		Creates the driver.

		Details:
			It will search for the µc using the PID value 'DEFAULT_PID' or the one provided in argument.
			Takes the first found if many have the same PID.
			RAISE if not found.

		Arguments:
			pid: optional, the pid to search for.
		"""
		self.ser = serial.Serial()
		self.ser.baudrate = 921600
		self.uc_ack_mode = ACK.NONE

		ports = serial.tools.list_ports.comports()
		st_port = None

		for port in ports:
			# If there are multiple serial ports with the same PID, we just use the first one
			if port.pid == pid:
				st_port = port.device
				break

		if st_port is None:
			raise Exception("µc not found, please verify its connection or specify its PID")

		self.ser.port = st_port
		self.ser.open()

	def __del__(self):
		"""Closes the serial port if still open."""
		self.ser.close()
	
	@staticmethod
	def list_ports():
		"""Returns a list of all the serial ports recognized by the OS."""
		return serial.tools.list_ports.comports()

	@staticmethod
	def print_ports():
		"""Prints out the useful info about the serial ports recognized by the OS."""
		ports = serial.tools.list_ports.comports()
		if len(ports) == 0:
			print("❌ No serial ports found")
		else:
			for port in serial.tools.list_ports.comports():
				print(port, "| PID: ", port.pid)

	def send_command(self, command, *args, wait_for_ack=False):
		"""
		Sends a command to the µc with the optionnaly provided arguments.

		Parameters:
			command: The command to send (see CMD_LIST)
			*args: The provided arguments, which will be converted to bytes

		Returns:
			The actual number of bytes sent.

		Details:
			The µc cannot receive more than 64 bytes in one shot, this function will split the arguments and send them by packets of 64 bytes max
		"""
		if not self.ser.is_open:
			raise Exception("Serial port not open")

		if command == CMD.ACK_MODE:
			self.uc_ack_mode = args[0]
	
		command_bytes = as_bytes(command)
		bytes_sent_count = 0

		split_args = []
		max_bytes = 64 - 3 # 64 bytes - '0xAA' - 'command-bytes' - '0xAA'/'0xAB'
		while len(args) > max_bytes:
			split_args.append(args[:max_bytes])
			args = args[max_bytes:]

			# After first loop:
			max_bytes = 64 - 1 # 64 bytes - '0xAA'/'0xAB'

		split_args.append(args[:])

		# Words sent for instance:
		#  0xAA, CMD, data0 ... data60, 0xAB
		#  data61 .. data123, 0xAB
		#  data124 .. data130, 0xAA
		for i, args in enumerate(split_args):
			cmd = b'\xAA' + command_bytes if i == 0 else b''
			
			for arg in args:
				if isinstance(arg, int):
					cmd += as_bytes(arg)
				elif isinstance(arg, List):
					raise ValueError("Please unpack lists in argument: '*[...]'")
				else:
					cmd += bytes(arg)

			cmd += b'\xAA' if i + 1 == len(split_args) else b'\xAB'
			
			bytes_sent_count += self.ser.write(cmd)

		if wait_for_ack:
			ack = self.read(2, flush_rest=False)
			if ack != b'\xAA' + command_bytes:
				raise Exception(f"Expected ack for command '{command}', got '{ack}'")

		return bytes_sent_count

	def read(self, size=None, wait_for=True, flush_rest=True):
		"""
		Reads from the µc.

		Parameters:
			size:       The number of bytes to read. If None, reads everything.
			wait_for:   When size=None, if True, waits for input ; When size!=None, wait_for is True
			flush_rest: If True, flushes the input buffer if non-empty after {size} bytes have been read.
		
		Returns:
			The bytes read.
		"""
		if not self.ser.is_open:
			raise Exception("Serial port not open")

		if size is None:
			out = b''

			# Block or not until something is in
			while wait_for and not self.ser.in_waiting:
				pass

			# Read everything until the buffer is empty
			while self.ser.in_waiting:
				out += self.ser.read()
			return out
		
		# else
		out = self.ser.read(size)
		if flush_rest:
			self.flush_input()
		return out

	def call_command(self, command, *args):
		"""
		Send a command and waits for a return value if needed

		Parameters:
			command: The command to send (see CMD_LIST)
			*args: The provided arguments, which will be converted to bytes

		Returns:
			The return value of the corresponding command or None

		Details:
			Will expect an ack if set with the corresponding 'action' command (driver.ack_mode(ACK.XXX)) (RAISE if expected and not received)
			Will return the value received if the command is a 'get' command
		"""

		cmd_name = str(command)[4:] # str(command) == CMD.XXX => str(command)[4:] == XXX
		wait_for_ack = (cmd_name in str(self.uc_ack_mode))
		cmd_returns = (cmd_name not in str(ACK_ALL)) and command != CMD.ACK_MODE # If the commands does not have an associated ack, it is because it returns something

		if command == CMD.ACK_MODE and args[0] != ACK.NONE:
			wait_for_ack = True
			cmd_returns = False
		
		self.send_command(command, *args, wait_for_ack=wait_for_ack)

		return self.read() if cmd_returns else None

	def flush_input(self):
		"""Flushes the input buffer."""
		while self.ser.in_waiting:
				self.ser.read()