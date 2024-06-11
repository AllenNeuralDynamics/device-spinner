#!/usr/bin/env python3
"""Instantiate objects from list of dicts."""

from device_spinner.config import Config
from device_spinner.device_spinner import DeviceSpinner
from typing import List

import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
logger.handlers[-1].setFormatter(
   logging.Formatter(fmt='%(asctime)s:%(levelname)s: %(message)s'))


class Laser:
    def __init__(self, serial_port: str):
        pass

class Camera:
    pass

class Microscope:
    def __init__(self, camera, lasers: List[Laser]):
        pass


device_config = Config("instrument_config.yaml")
# TODO: make a to_dict function.
device_specs = dict(device_config.cfg)
import pprint
pprint.pprint(device_specs)
# Create the objects
factory = DeviceSpinner()
device_trees = factory.create_devices_from_specs(device_specs["devices"])

