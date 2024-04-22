import winreg
from yoctopuce.yocto_api import *

REG_PATH = "Software\\HWiNFO64\\Sensors\\Custom"


def functionValueChangeCallback(fct, value):
    info = fct.get_userData()
    print(info['hwId'] + ": " + value + " " + info['unit'] + " (new value)")


class CustomHWiNFOsensor:

    def __init__(self, y_hwid: str, basekey: str, hwinfo_type: str, index: int):
        self.sensor = YSensor.FindSensor(y_hwid)
        self.funid = self.sensor.get_functionId()
        self.key_path = "%s\\%s%d" % (basekey, hwinfo_type, index)
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.key_path)
        try:
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(registry_key, "Name", 0, winreg.REG_SZ, self.funid)
            winreg.SetValueEx(registry_key, "Unit", 0, winreg.REG_SZ, self.sensor.get_unit())
            winreg.SetValueEx(registry_key, "Value", 0, winreg.REG_SZ, "%f" % self.sensor.get_currentValue())
            winreg.CloseKey(registry_key)
        except WindowsError:
            print("WTF")
        self.sensor.set_userData(self)
        self.sensor.registerValueCallback(self.update_value)

    def update_value(self, fct, value):
        try:
            print("update %s to %s" % (self.key_path, value))
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(registry_key, "Value", 0, winreg.REG_SZ, value)
            winreg.CloseKey(registry_key)
            return True
        except WindowsError:
            return False


class HWiNFO_dev:
    def __init__(self, module: YModule):
        self.dev_name = module.get_friendlyName()
        self.dev_key_path = REG_PATH + "\\" + self.dev_name
        self.hwinfo_sensors = {
            "Temp": {},
            "Volt": {},
            "Current": {},
            "Power": {},
            "Other": {}
        }

        winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.dev_key_path)
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
            HWiNfo_sensor = CustomHWiNFOsensor(hwid, self.dev_key_path, hwinfo_sensor_type, index)
            self.hwinfo_sensors[hwinfo_sensor_type][hwid] = HWiNfo_sensor


def functionValueChangeCallback(fct, value):
    print("new val:" + value)
    HWiNfo_sensor: CustomHWiNFOsensor = fct.get_userData()
    HWiNfo_sensor.update_value(value)


def deviceArrival(m):
    serial = m.get_serialNumber()
    print('Device arrival : ' + serial)
    # HWiNfo_sensor = CustomHWiNFOsensor("test", "test_id", winreg.HKEY_CURRENT_USER)
    # HWiNfo_sensor.update_value("test")
    sensor = YSensor.FirstSensor()
    while sensor:
        module = sensor.get_module()
        if module.get_serialNumber() == serial:
            hardwareId = sensor.get_hardwareId()
            print('- ' + hardwareId)
            HWiNfo_sensor = CustomHWiNFOsensor(sensor, winreg.HKEY_CURRENT_USER)
            sensor.set_userData(HWiNfo_sensor)
            sensor.registerValueCallback(functionValueChangeCallback)
        sensor = sensor.nextSensor()


def deviceRemoval(m):
    print('Device removal : ' + m.get_serialNumber())


def logfun(line):
    print('LOG : ' + line.rstrip())


def main():
    errmsg = YRefParam()
    YAPI.RegisterLogFunction(logfun)
    # Setup the API to use local USB devices
    res = YAPI.RegisterHub("usb", errmsg)
    if res == YAPI.DOUBLE_ACCES:
        print("USB access is already locked fallback to VirtualHub")
        res = YAPI.RegisterHub("127.0.0.1", errmsg)
    if res != YAPI.SUCCESS:
        sys.exit("init error" + errmsg.value)

    # YAPI.RegisterDeviceArrivalCallback(deviceArrival)
    # YAPI.RegisterDeviceRemovalCallback(deviceRemoval)
    devs = []
    sensor = YSensor.FirstSensor()
    while sensor:
        module = sensor.get_module()
        hardwareId = sensor.get_hardwareId()
        print('- ' + hardwareId)
        HWiNfo_dev = HWiNFO_dev(module)
        devs.append(HWiNfo_dev)
        sensor = sensor.nextSensor()
    print('Hit Ctrl-C to Stop ')
    while True:
        YAPI.UpdateDeviceList(errmsg)  # traps plug/unplug events
        YAPI.Sleep(500, errmsg)  # traps others events


if __name__ == "__main__":
    main()
