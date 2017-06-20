# -*- coding: utf-8 -*-

import copy


class Provider:
    def device_names(self):
        raise NotImplementedError

    def get_device(self, name, platform="ANDROID"):
        raise NotImplementedError


class Device:
    name = None
    platform = None
    version = None

    def __str__(self):
        return "<%s %s %s>" % (self.name, self.platform, self.version)

    def to_json(self):
        _json = copy.copy(self.__dict__)
        del _json['adb']
        return _json

    def get_browsers(self):
        raise NotImplementedError
