#!/usr/bin/env python3
"""Instantiate objects from list of dicts."""

from device_spinner.device_spinner import DeviceSpinner
import pprint

# Uncomment for some prolific log statements.
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
logger.handlers[-1].setFormatter(
   logging.Formatter(fmt='%(asctime)s:%(levelname)s: %(message)s'))


class Wheel:
    pass


class Bike:
    def __init__(self, front_wheel, back_wheel):
        pass


device_specs = \
{
    "my_bike":
        {
            "module": __name__, # the current module.
            "class": "Bike",
            "args": ["my_front_wheel", "my_back_wheel"],
        },
    "my_front_wheel":
        {
            "module": __name__,
            "class": "Wheel",
        },
    "my_back_wheel":
        {
            "module": __name__,
            "class": "Wheel",
        },

}
factory = DeviceSpinner()
device_trees = factory.create_devices_from_specs(device_specs)
