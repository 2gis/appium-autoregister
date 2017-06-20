# coding: utf-8

import asyncio
import json
import os
import logging
import copy
from subprocess import Popen, PIPE, STDOUT
from threading import Thread

from utils import get_free_port, run_command


LOG_DIR = "logs"
log = logging.getLogger(__name__)


class AppiumNode:
    process = None
    process_reader = None

    appium_executable = os.environ.get("APPIUM_EXECUTABLE", None)
    if appium_executable is None:
        exit('set $APPIUM_EXECUTABLE to path of appium executable')

    def __init__(self, appium_port, device, config_file=None, generate_bootstrap_port=True,
                 generate_wda_local_port=True, additional_args=None):
        self.appium_port = appium_port
        self.device = device
        self.config_file = config_file

        self.generate_bootstrap_port = generate_bootstrap_port
        self.generate_wda_local_port = generate_wda_local_port
        self.additional_args = additional_args

        self.log = logging.getLogger(self.device.name)
        os.makedirs(LOG_DIR, exist_ok=True)
        self.logfile = os.sep.join([LOG_DIR, device.name])

        if self.generate_bootstrap_port:
            self.bootstrap_port = get_free_port()

        if self.generate_wda_local_port:
            self.wda_local_port = get_free_port()

    def to_json(self):
        _json = copy.copy(self.__dict__)
        del _json['process']
        del _json['log']
        return _json

    @property
    def _command(self):
        default_caps = {"udid": self.device.name}

        if self.generate_wda_local_port:
            default_caps["wdaLocalPort"] = self.wda_local_port

        command = [
            self.appium_executable,
            "--port", str(self.appium_port),
            "--default-capabilities", json.dumps(default_caps)
        ]

        if self.generate_bootstrap_port:
            command += ["--bootstrap-port", str(self.bootstrap_port)]

        if self.additional_args:
            command += self.additional_args

        if self.config_file:
            command += ["--nodeconfig", self.config_file]
        return command

    def start(self):
        if self.process is not None:
            return self.process

        log.info("starting appium node for %s" % self.device)
        log.info("running command %s" % " ".join(self._command))
        self.process = Popen(self._command, stderr=STDOUT, stdout=PIPE)
        self.process_reader = Thread(target=self._log_process_stdout)
        self.process_reader.daemon = True
        self.process_reader.start()
        log.info("process started with pid %s" % self.process.pid)
        return self.process

    async def start_coro(self):
        if self.process is not None:
            return self.process

        log.info("starting appium node for %s" % self.device)
        self.process = await run_command(self._command, wait_end=False)
        await self.process.stdout.read(1)
        asyncio.ensure_future(self._write_stdout())
        if self.process.returncode:
            log.warning((await self.process.communicate()))
        log.info("process started with pid %s" % self.process.pid)
        return self.process

    async def _write_stdout(self):
        with open(self.logfile, "wb") as fd:
            while self.process.returncode is None and\
                    not self.process.stdout.at_eof():
                line = await self.process.stdout.readline()
                if line:
                    fd.write(line)

    def stop(self):
        if hasattr(self.process, "poll"):
            self.process.poll()
        if self.process and not self.process.returncode:
            self.process.kill()
        if self.process_reader:
            self.process_reader.join()
        if self.config_file:
            os.remove(self.config_file)
        log.info("appium node for %s stopped" % self.device)

    async def delete(self):
        self.stop()

    def _log_process_stdout(self):
        while self.process.poll() is None:
            line = self.process.stdout.readline()
            if line:
                self.log.info("%s" % line.decode().strip("\n"))
