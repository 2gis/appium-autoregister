# coding: utf-8

import os
import sys
import asyncio
import logging

from os import environ, path
from subprocess import Popen, PIPE


ENCODING = sys.getdefaultencoding()

log = logging.getLogger(__name__)


async def adb_command(device, params, asynchronous=False):
    assert device is not None

    if isinstance(params, str):
        params = params.split(" ")

    android_home = os.environ.get("ANDROID_HOME", None)
    if android_home is not None:
        adb = os.path.join(android_home, 'platform-tools', 'adb')
    else:
        # if we don't have ANDROID_HOME set, let's just hope adb is in PATH
        adb = 'adb'
    command = [adb, '-s', device, '-H', 'localhost'] + params
    p = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        env=os.environ.copy())
    setattr(p, 'command', command)
    if not asynchronous:
        await p.wait()
    return p


async def until_adb_output(device_name, command, result):
    _result = None
    while _result != result:
        _process = await adb_command(device_name, command)
        _result = (await _process.stdout.read()).strip()

    _process = await adb_command(device_name, command)
    log.info("%s is %s" % (" ".join(_process.command), result))


def get_command_output(p):
    return p.stdout.read().decode(ENCODING).strip()


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
        return cls._popen(["devices"]).stdout.readlines()

    def getprop(self, prop=""):
        p = self._popen(["-s", self.device_name, "shell", "getprop", prop])
        return get_command_output(p)

    def pm_list_has_package(self, package):
        p = self._popen(["-s", self.device_name, "shell", "pm", "list", "packages", package])
        return get_command_output(p)
