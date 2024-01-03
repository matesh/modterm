# ModTerm
![Home](/assets/home.png)

## Introduction
ModTerm is a terminal based modbus analyser software, written in pure Python, utilising the curses UI extensions. The aim of the software is to help reverse engineering modbus data of unknown, or poorly documented modbus devices and allow registers to be written into the devices for testing and analysis purposes.


## Features
### Reading registers
ModBus registers can be read from devices connected to the computer via TCP or RTU. The registers read from the device are listed in a table, with the rows being the register numbers, and the columns being results of various register decoding methods, such as INT16, INT32, Float32, string, bits, etc. The endianness can be changed on the fly to make sense of the register contents. Supports reading registers in blocks, if the number of registers to be read is above 125, the reads are broken down to blocks of 120 register reads. Also supports reading each registers individually for the case when devices return exceptions to unsupported registers.

![Read registers](/assets/read_registers.png)
![Read registers result](/assets/registers.png)

### Writing registers
Registers with a provided encoding method can be written into one or more registers

![Write registers](/assets/write_register_menu.png)

### Scanning devices on a bus
TThis feature allows to sweep through modbus unit IDs on a connected bus and run a register read operation, in the hope of receiving a response and thus detecting a device.

![Unit sweep](/assets/unit_sweep_menu.png)
![Unit sweep results](/assets/unit_sweep_results.png)

## Requirements
The project runs best on Python 3.11 and above, but should run on any versions of Python above 3.9
The project depends on the `pymodbus` library and should install that from pypi during installation.

⚠️ The project has been tested on macOS and Linux, but not on Windows. According to the documentation of the curses module in Python, it is not included in the Windows version. The documentation mentions the UniCurses module to be used under Windows, but this has not been tested yet. This section will be updated once testing has been done. For Windows users wanting to take advantage of this software, I recommend using WSL.

## Installation and usage
- Install a version of Python 3 using your operating system's package manager, or start up a virtual environment with Python version being ideally 3.11 or above
- Issue `pip3 install modterm`
- Launch the app by issuing `modterm` in the terminal.

The menu items and configuration options are accessible via the F-keys indicated next to each option. On the main screen, pressing F1 brings up the help screen to show which features are accessible via which keys. 

## Ways to contribute
For now, please report any issues with decoding, inconsistencies, bugs and crashes.

Feel free to suggest improvements and changes that would help 

## Development path
The below describes the features planned to be added for each point release in the future. _All the below are subject to change_
### V1.0
- Testing on multiple platforms and making the initial set of features robust and bug-free enough for a proper point release.
- Add logging and proper error handling
- Multicast writes

### V1.1
- Add coil and discrete input reads/writes (where applicable)
- Sweep IP addresses for ModbusTCP responses

### V1.2
- Write float registers
- Test windows compatibility

### V1.3
- Read modbus device information registers