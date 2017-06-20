# -*- coding: utf-8 -*-

import sys

from provider.base import Provider, Device
from provider.adb import Adb

ENCODING = sys.getdefaultencoding()


class AndroidDevice(Device):
    def __init__(self, name, platform):
        self.name = name
        self.platform = platform
        self.adb = Adb(self.name)
        self.version = self.adb.getprop("ro.build.version.release")
        self.model = self.adb.getprop("ro.product.model")
        self.browsers = self.get_browsers()

    def get_browsers(self):
        browsers = list()
        if self.adb.pm_list_has_package("com.android.chrome"):
            browsers.append("chrome")
        if not browsers:
            browsers.append("")
        return browsers


class AndroidProvider(Provider):
    def __init__(self, adb_class=Adb, device_class=AndroidDevice):
        self.Adb = adb_class
        self.AndroidDevice = device_class

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
