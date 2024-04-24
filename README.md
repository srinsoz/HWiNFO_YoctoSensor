# YoctoHWiNFO 

This is a small script that will publish all Yoctopuce sensors on [HWiNFO application](https://www.hwinfo.com/) software.
It use the [Yoctopuce Python library](https://github.com/yoctopuce/yoctolib_python) to detect to Yoctopuce devices and 
create the corresponding [HWiNFO custom user sensors](https://www.hwinfo.com/forum/threads/custom-user-sensors-in-hwinfo.5817/)


## Options
````
-h, --help            show this help message and exit
-r REMOTE_HUB, --remote_hub REMOTE_HUB
                    Uses remote IP devices (or VirtalHub), instead of local USB.
--use_HKEY_LOCAL_MACHINE
                    Use HKEY_LOCAL_MACHINE instead of HKEY_CURRENT_USER for HWiNFO custom sensors.
-v {0,1}, --verbose {0,1}
                    Verbose level: 0=silent, 1=verbose, 2=debug.
````


## Installation

This script use Yoctopuce python library which can be installed with pip:

````
pip install yoctopuce
````

