# coding: utf-8
import argparse
import json
import logging
import tempfile
import signal
import time
from string import Template


from android import android_device_names, Device
from utils import get_free_port
from appium import AppiumNode


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("autoregister")


class StopAutoregister(Exception):
    pass


class Autoregister(object):
    nodes = list()

    configuration_template = Template("""
    {
        "cleanUpCycle": 2000,
        "timeout": 30000,
        "proxy": "org.openqa.grid.selenium.proxy.DefaultRemoteProxy",
        "url": "http://$appium_host:$appium_port/wd/hub",
        "host": "$appium_host",
        "port": $appium_port,
        "maxSession": 1,
        "register": true,
        "registerCycle": 5000,
        "hubPort": $grid_port,
        "hubHost": "$grid_host"
    }
    """)
    capabilities_template = Template("""
    {
        "browserName": "$browserName",
        "version": "$browserVersion",
        "maxInstances": 1,
        "platformName": "$platformName",
        "platformVersion": "$platformVersion",
        "deviceName": "$deviceName"
    }
    """)

    def __init__(self, grid_host, grid_port, appium_host, generate_bootstrap_port, additional_args):
        self.grid_host = grid_host
        self.grid_port = grid_port
        self.appium_host = appium_host
        self.generate_bootstrap_port = generate_bootstrap_port
        self.additional_args = additional_args
        signal.signal(signal.SIGTERM, self.stop_signal)

    @staticmethod
    def stop_signal(signum, frame):
        raise StopAutoregister()

    def register(self, device_name, device_platform="ANDROID"):
        device = Device(device_name, device_platform)
        config_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        port = get_free_port()
        config = self.generate_config(device, port)
        config_file.write(config)
        config_file.flush()
        node = AppiumNode(port, device, config_file.name, self.generate_bootstrap_port, self.additional_args)
        node.start()
        self.nodes.append(node)

    def unregister(self, node):
        node.stop()
        self.nodes.remove(node)

    def run(self, ):
        log.info("start registering devices...")
        try:
            while True:
                known_devices = {node.device.name: node for node in self.nodes}
                for device_name in android_device_names():
                    if device_name in known_devices.keys():
                        del known_devices[device_name]
                        continue

                    self.register(device_name)

                for node in known_devices.values():
                    self.unregister(node)

                time.sleep(0.2)
        except (StopAutoregister, KeyboardInterrupt, SystemExit):
            self.stop()

    def generate_config(self, device, appium_port):
        capabilities = []
        for browser in device.browsers:
            capabilities.append(
                json.loads(self.capabilities_template.substitute({
                    "deviceName": device.name,
                    "platformName": device.platform,
                    "platformVersion": device.version,
                    "browserName": browser,
                    "browserVersion": "",
                }))
            )
        configuration = json.loads(self.configuration_template.substitute({
            "appium_host": self.appium_host,
            "appium_port": appium_port,
            "grid_host": self.grid_host,
            "grid_port": self.grid_port,
        }))
        return json.dumps({
          'capabilities': capabilities,
          'configuration': configuration
        })

    def stop(self):
        log.info("stopping...")
        for node in self.nodes:
            node.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run appium autoregister')
    parser.add_argument('--grid-host', type=str, dest='grid_host', default="localhost",
                        help='Selenium grid host register to. Default localhost.')
    parser.add_argument('--grid-port', type=int, dest='grid_port', default=4444,
                        help='Selenium grid port register to. Default 4444.')
    parser.add_argument('--appium-host', type=str, dest='appium_host', default="localhost",
                        help='This machine host, to be discovered from grid. Default localhost.')
    parser.add_argument('--disable-bootstrap-port-generation', action='store_true', default=False,
                        help='Disable generating random free port for and providing it'
                             ' to Appium with --bootstrap-port parameter.')
    parser.add_argument('--additional-args', type=str, dest='additional_args', default='',
                        help='Additional arguments to appium, when it starts.'
                             ' Arguments should be separated by ",".'
                             ' Default no additional arguments passing')

    args = parser.parse_args()
    additional_args = None
    if args.additional_args:
        additional_args = args.additional_args.split(',')
    generate_bootstrap_port = not args.disable_bootstrap_port_generation
    autoregister = Autoregister(args.grid_host, args.grid_port, args.appium_host,
                                generate_bootstrap_port, additional_args)
    autoregister.run()
