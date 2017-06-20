# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
from provider.base import Provider, Device


class IosProvider(Provider):
    def __init__(self, idevice_id_class=iDeviceIdUtil, device_class=IosDevice):
        self.idevice_id = idevice_id_class()
        self.IosDevice = device_class

    def device_names(self):
        for udid in self.idevice_id.devices():
            yield udid

    def get_device(self, name):
        return self.IosDevice(name)


class IosDevice(Device):
    def __init__(self, name, platform="IOS"):
        self.name = name
        self.platform = platform

        # self.version = self.adb.getprop("ro.build.version.release")
        # self.model = self.adb.getprop("ro.product.model")
        # self.browsers = self.get_browsers()

    def get_browsers(self):
        return ["safari"]


class iDeviceIdUtil:

    _list_devices_command = ["idevice_id", "--list"]

    @staticmethod
    def _run_process(command):
        process = Popen(command, stdout=PIPE, stderr=PIPE)
        process.wait()
        return process

    @staticmethod
    def bytes_to_str(_bytes):
        return _bytes.decode("utf-8") if isinstance(_bytes, bytes) else _bytes

    def _execute_command(self, command):
        process = self._run_process(command)
        if process.returncode == 0:
            return self.bytes_to_str(
                process.stdout.readlines().strip()
            )
        else:
            raise Exception("Cannot execute command {}. Stderr:{}".format(
                command, process.stderr.readlines().strip())
            )

    def _get_device_list(self):
        self._execute_command(self._list_devices_command)
        return []

    def devices(self):
        return self._get_device_list()
