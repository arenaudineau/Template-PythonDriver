from cmath import e
import sys

"""
Script to generate the Python enum associated with the C ones
Usage:
	python utils/gen_enums.py {path_to_stm32cube_project_root} {path_to_python_library_root (optional if already in it)}
"""

def parse_file(f):
	read_content = False
	last_line = None
	enums = []
	while True:
		line = f.readline()
		if line == '': # We reached the end
			break
		
		if read_content:
			if line.startswith('// END uc enums and flags'):
				read_content = False
				break

			if line.startswith('typedef enum'):
				enum_content = str()
				enum_line = f.readline()

				enum_prefix = None
				prefix_provided = False

				while '}' not in enum_line:
					if enum_line == '':
						print("Unexpected end of file during enum parsing")
						break
					
					enum_line = enum_line.strip()
						
					if enum_line.endswith(','):
						enum_line = enum_line[:-1]
					if enum_line == '':
						enum_line = f.readline()
						continue

					if enum_prefix is None:
						enum_prefix = enum_line
					elif not enum_line.startswith(enum_prefix) and not prefix_provided:
						for i in range(1, len(enum_prefix)+1):
							if not enum_line.startswith(enum_prefix[:i]):
								if i == 1:
									enum_prefix = input("No prefix found, please provide one for '" + last_line[:-1] + "': ")
									prefix_provided = True
								else:
									enum_prefix = enum_prefix[:i - 1]
									if enum_prefix.endswith('_'):
										enum_prefix = enum_prefix[:-1]
								break
					
					enum_content += enum_line + '\n'

					enum_line = f.readline()
		
		elif line.startswith('// uc enums and flags'):
			read_content = True

		last_line = line

	return enums

if __name__ == '__main__':
	if len(sys.argv) < 2:
		raise ValueError("Missing stm32cube path, see usage.")
		exit(1)
	
	stm_path    = sys.argv[1]
	python_path = '.'

	if len(sys.argv) >= 3:
		if len(sys.argv) > 3:
			print("Unrecognized arguments:", sys.argv[3:])
		
		python_path = sys.argv[2]

	with open(stm_path + 'Core/Inc/main.h', 'r') as f:
		parse_file(f)

	with open(stm_path + 'USB_DEVICE/App/usbd_cdc_if.h') as f:
		parse_file(f)


