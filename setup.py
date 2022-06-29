from setuptools import setup, find_packages

setup(
	name='Template-PythonDriver',
	version='0.1.0',
	packages=find_packages(),
	install_requires=[
		'pyserial',
		'pyvisa',
		'pandas',
	]
)