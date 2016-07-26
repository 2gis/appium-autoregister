# coding: utf-8

from os import environ, path
from subprocess import Popen, PIPE
import logging
import copy

import sys

ENCODING = sys.getdefaultencoding()


class Adb(object):
    android_home = environ.get("ANDROID_HOME", None)
    if android_home is None:
        exit("set $ANDROID_HOME to path of your android sdk root")

    adb = path.join(android_home, "platform-tools", "adb")
    if not path.isfile(adb):
        exit("adb executable not found in %s" % adb)

    def __init__(self, device_name):
        self.device_name = device_name

    @classmethod
    def _popen(cls, args):
        args = [arg if isinstance(arg, str) else arg.decode(ENCODING) for arg in args]
        command = [cls.adb] + args
        p = Popen(command, stdout=PIPE, stderr=PIPE)
        p.wait()
        if p.returncode != 0:
            logging.warning("failed to run command %s" % " ".join(command))
        return p

    @classmethod
    def devices(cls):
        p = cls._popen(["devices"])
        return p

    def getprop(self, prop=""):
        p = self._popen(["-s", self.device_name, "shell", "getprop", prop])
        return p.stdout.read().decode(ENCODING).strip()

    def check_package(self, package):
        p = self._popen(["-s", self.device_name, "shell", "pm", "list", "packages", package])
        return p.stdout.read().decode(ENCODING).strip()


class Device(object):
    def __init__(self, name, platform):
        self.name = name
        self.platform = platform
        self.adb = Adb(self.name)
        self.version = self.adb.getprop("ro.build.version.release")
        self.model = self.adb.getprop("ro.product.model")
        self.uuid = self.adb.getprop("emu.uuid")
        self.browser = self.get_browser()

    def __str__(self):
        return "<%s %s %s emu.uuid=%s>" % (self.name, self.platform, self.version, self.uuid)

    def to_json(self):
        _json = copy.copy(self.__dict__)
        del _json['adb']
        return _json

    def get_browser(self):
        if self.adb.check_package("com.android.chrome"):
            return "chrome"
        else:
            return "unknown"


def android_devices():
    p = Adb.devices()
    devices = p.stdout.readlines()

    for line in devices:
        try:
            device_name, state = line.decode(ENCODING).split()
        except ValueError:
            device_name, state = None, None
        if state == "device":
            yield Device(device_name, "ANDROID")


def find_device_by_uuid(uuid):
    for device in android_devices():
        if device.uuid == uuid:
            return device

    return None
