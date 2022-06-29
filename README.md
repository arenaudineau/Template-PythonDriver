# Template-PythonDriver
Template for making a Python Driver for chips @ C2N

## Installation
This library requires:  
* ⚠️ 32 bits version of Python
* `pyserial` version 3.5 or any other compatible version
* `pyvisa` version 1.12.0 or any other compatible version
* `pandas` version 1.4.2 or any other compatible version
* The associated NI-VISA drivers, see [the official doc](https://pyvisa.readthedocs.io/en/latest/faq/getting_nivisa.html#faq-getting-nivisa). (⚠️ 32 bits version required)

### Global installation
1. Download and install the NI-VISA drivers
2. `B1530driver.py` and `B1530ErrorModule.py` are licensed and cannot be shared on GitHub, they are therefore missing on this repo.  
You must copy them at the location `extlibs/B1530Driver`, aside the `__init__.py` file.  
3. You can then go back to the root of this repo and run the command `pip install .`. The script should download the Python library and install `{template}` globally.

You can now use `aad` as a regular library, by using `import {template}` in any directory on the computer.

### Extending the driver
Same as previously but use `pip install -e .` not to have to exec the command at every change.  After the extension is done, you can `pip install .`.

---
#### **Linux users only**
Only `mcdriver` is available on Linux. In order to test it out, you will need to add your user to the `dialout` group:  
```bash
sudo usermod -aG dialout $USER
```

# Wiki
Here is a complete [wiki](../../wiki) on how to use this library.
