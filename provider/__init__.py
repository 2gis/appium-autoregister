# -*- coding: utf-8 -*-

import sys

ENCODING = sys.getdefaultencoding()


class AndroidProvider:

    def __init__(self):
        from android import Adb
        self.Adb = Adb

        from android import AndroidDevice
        self.AndroidDevice = AndroidDevice

    def device_names(self):
        for line in self.Adb.devices():
            try:
                device_name, state = line.decode(ENCODING).split()
            except ValueError:
                device_name, state = None, None
            if state == "device":
                yield device_name

    def get_device(self, name, platform="ANDROID"):
        return self.AndroidDevice(name, platform)
