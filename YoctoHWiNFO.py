import argparse
import winreg
from yoctopuce.yocto_api import *

REG_PATH = "Software\\HWiNFO64\\Sensors\\Custom"


def functionValueChangeCallback(fct, value):
    info = fct.get_userData()
    # print(info['hwId'] + ": " + value + " " + info['unit'] + " (new value)")


class CustomHWiNFOsensor:

    def __init__(self, y_hwid, basekey, hwinfo_type, index, key, verbose):
        self.sensor = YSensor.FindSensor(y_hwid)
        self.funid = self.sensor.get_functionId()
        self.key_path = "%s\\%s%d" % (basekey, hwinfo_type, index)
        self.verbose = verbose
        self.y_hwid = y_hwid
        self.key = key
        try:
            winreg.CreateKey(self.key, self.key_path)
            registry_key = winreg.OpenKey(self.key, self.key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(registry_key, "Name", 0, winreg.REG_SZ, self.funid)
            winreg.SetValueEx(registry_key, "Unit", 0, winreg.REG_SZ, self.sensor.get_unit())
            winreg.SetValueEx(registry_key, "Value", 0, winreg.REG_SZ, "%f" % self.sensor.get_currentValue())
            winreg.CloseKey(registry_key)
        except WindowsError as e:
            print(e)
            sys.exit("Unable to create registry key %s on %s" % (self.key_path, self.key))
        self.sensor.set_userData(self)
        self.sensor.registerValueCallback(self.update_value)

    def update_value(self, fct, value):
        try:
            if self.verbose > 1:
                print("update %s to %s" % (self.key_path, value))
            registry_key = winreg.OpenKey(self.key, self.key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(registry_key, "Value", 0, winreg.REG_SZ, value)
            winreg.CloseKey(registry_key)
            return True
        except WindowsError as e:
            print(e)
            sys.exit("Unable to update registry key %s on %s" % (self.key_path, self.key))

    def unplug(self):
        try:
            winreg.DeleteKey(self.key, self.key_path)
        except WindowsError as e:
            print(e)
            sys.exit("unable to delete key %s" % self.key_path)


class HWiNFO_dev:
    def __init__(self, module: YModule, key, verbose=0):
        self.dev_name = module.get_friendlyName()
        self.key = key
        self.verbose = verbose
        self.dev_key_path = REG_PATH + "\\" + self.dev_name
        self.hwinfo_sensors = {
            "Temp": {},
            "Volt": {},
            "Current": {},
            "Power": {},
            "Other": {}
        }

        fctcount = module.functionCount()
        for i in range(fctcount):
            function_id = module.functionId(i)
            hwid = module.get_serialNumber() + "." + function_id
            hwinfo_sensor_type = 'Other'
            if module.functionBaseType(i) != 'Sensor':
                continue
            if function_id.startswith("temperature"):
                hwinfo_sensor_type = 'Temp'
            elif function_id.startswith("voltage"):
                hwinfo_sensor_type = 'Volt'
            elif function_id.startswith("current"):
                hwinfo_sensor_type = 'Current'
            elif function_id.startswith("power"):
                hwinfo_sensor_type = 'Power'
            elif function_id.startswith("power"):
                hwinfo_sensor_type = 'Power'
            if hwid in self.hwinfo_sensors[hwinfo_sensor_type]:
                index = self.hwinfo_sensors[hwinfo_sensor_type][hwid].getIndex()
            else:
                index = len(self.hwinfo_sensors[hwinfo_sensor_type])
            try:
                winreg.CreateKey(self.key, self.dev_key_path)
            except WindowsError as e:
                print(e)
                sys.exit("unable to create key %s" % self.dev_key_path)
            print("Sensor %s registred" % hwid)
            HWiNfo_sensor = CustomHWiNFOsensor(hwid, self.dev_key_path, hwinfo_sensor_type, index, self.key,
                                               verbose=self.verbose)
            self.hwinfo_sensors[hwinfo_sensor_type][hwid] = HWiNfo_sensor

    def unplug(self):
        for hw_type in self.hwinfo_sensors:
            for hwid in self.hwinfo_sensors[hw_type]:
                self.hwinfo_sensors[hw_type][hwid].unplug()
        try:
            winreg.DeleteKey(self.key, self.dev_key_path)
        except WindowsError:
            sys.exit("unable to delete key %s" % self.dev_key_path)


class YoctoHWiNFOApp:
    def __init__(self, args):
        self.devices = {}
        self.args = args
        if args.use_HKEY_LOCAL_MACHINE:
            if args.verbose:
                print("Using HKEY_LOCAL_MACHINE")
            self.key = winreg.HKEY_LOCAL_MACHINE
        else:
            if args.verbose:
                print("Using HKEY_CURRENT_USER")
            self.key = winreg.HKEY_CURRENT_USER

    def deviceArrival(self, module):
        serial = module.get_serialNumber()
        if self.args.verbose > 0:
            print('Device arrival : ' + serial)
        self.devices[serial] = HWiNFO_dev(module, self.key, self.args.verbose)

    def deviceRemoval(self, module):
        serial = module.get_serialNumber()
        if self.args.verbose > 0:
            print('Device removal : ' + serial)
        if serial in self.devices:
            self.devices[serial].unplug()
            del (self.devices[serial])


def logfun(line):
    print(line.rstrip())


def main():
    parser = argparse.ArgumentParser(
        prog='YoctoHWiNFO',
        description='Publish Yoctopuce sensors to HWiNFO software.'
    )
    parser.add_argument('-r', '--remote_hub', action='store', default='usb')
    parser.add_argument('--use_HKEY_LOCAL_MACHINE', action='store_true', default=False)
    parser.add_argument('-v', '--verbose', type=int, choices=range(0, 2), default=0)
    args = parser.parse_args()
    if args.verbose > 0:
        logfun('Verbose mode')
        logfun("Using Yoctopuce lib v%s"% YAPI.GetAPIVersion())
        YAPI.RegisterLogFunction(logfun)
    errmsg = YRefParam()
    # Setup the API to use local USB devices
    logfun('RegisterHub %s' % args.remote_hub)
    res = YAPI.RegisterHub(args.remote_hub, errmsg)
    if res == YAPI.DOUBLE_ACCES:
        print("USB access is already locked. Fallback to 127.0.0.1")
        res = YAPI.RegisterHub("127.0.0.1", errmsg)
    if res != YAPI.SUCCESS:
        sys.exit("init error" + errmsg.value)
    app = YoctoHWiNFOApp(args)
    YAPI.RegisterDeviceArrivalCallback(app.deviceArrival)
    YAPI.RegisterDeviceRemovalCallback(app.deviceRemoval)
    while True:
        YAPI.UpdateDeviceList(errmsg)  # traps plug/unplug events
        YAPI.Sleep(500, errmsg)  # traps others events


if __name__ == "__main__":
    main()
