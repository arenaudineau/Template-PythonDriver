from cmath import e
import sys

"""
Script to generate the Python enum associated with the C ones
Usage:
	python utils/gen_enums.py {path_to_stm32cube_project_root} {path_to_python_library_root}
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
				enum_content = []
				enum_line = f.readline()

				enum_prefix = None
				prefix_provided = False
				prefix_len = None

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
									prefix_len = i - 1

									if enum_prefix.endswith('_'):
										enum_prefix = enum_prefix[:-1]
									
								break
					
					enum_content.append(enum_line)

					enum_line = f.readline()

				enum_items = []
				is_flag = False
				last_val = None
				for enum_line in enum_content:
					split = list(map(str.strip, enum_line.split('=')))

					name = split[0][prefix_len:]
					val = None if len(split) == 1 else split[1]

					enum_items.append((name, val))

					if not (last_val is None or last_val == 0):
						try:
							if '<<' in val:
								is_flag = True
							elif float(val) == 2 * float(last_val):
								is_flag = True
						except ValueError: # Failed to parse as float
							pass

					last_val = val

				enums.append((enum_prefix, is_flag, enum_items))
		
		elif line.startswith('// uc enums and flags'):
			read_content = True

		last_line = line

	return enums

def generate_python(enums):
	content = str()
	for name, is_flag, items in enums:
		content += f"class {name}"
		content += "(IntFlag)" if is_flag else "(IntEnum)"
		content += ":\n"

		max_item_len = max(map(len, map(lambda x: x[0], items)))
		for item_name, item_val in items:
			if item_val is None:
				item_val = "en_auto()"

			content += f"\t{item_name}" + (' ' * (max_item_len - len(item_name))) + f" = {item_val}\n"
		content += "\n"
		content += f"{name}_LIST = list({name}.__members__.values())\n"

		if name == "ACK":
			content += "ACK_ALL = reduce(or_, ACK_LIST)\n"
		else:
			content += f"{name}_COUNT = len({name}_LIST)\n"
		content += "\n"

	content += "### END C enums and flags ###\n\n"
	return content

if __name__ == '__main__':
	if len(sys.argv) != 3:
		raise ValueError("Invalid argument count, expected 2, got {}".format(len(sys.argv) - 1))
		exit(1)
	
	stm_path    = sys.argv[1]
	python_path = '.'

	if len(sys.argv) >= 3:
		if len(sys.argv) > 3:
			print("Unrecognized arguments:", sys.argv[3:])
		
		python_path = sys.argv[2]

	enums = []
	with open(stm_path + '/Core/Inc/main.h', 'r') as f:
		enums.extend(parse_file(f))

	with open(stm_path + '/USB_DEVICE/App/usbd_cdc_if.h', 'r') as f:
		enums.extend(parse_file(f))

	with open(python_path + '/mcd.py', 'r') as f:
		content = str()
		search_section_end = False
		while True:
			line = f.readline()
			if line == '':
				break

			if search_section_end:
				if line.startswith('### END C enums and flags ###'):
					search_section_end = False
				continue
			elif line.startswith('# C enums and flags'):
				search_section_end = True
				content += '# C enums and flags\n'
				content += '###################\n\n'
				content += generate_python(enums)
				continue

			content += line

	print(content)