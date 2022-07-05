from setuptools import setup, find_packages

setup(
	name='Template-PythonDriver',
	version='0.1.0',
	packages=find_packages(),
	install_requires=[
		'pyserial',
		'B1530Lib @ https://github.com/arenaudineau/B1530Lib/archive/refs/heads/main.zip'
	]
)