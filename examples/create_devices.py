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


device_specs = \
{
    "MyDict":
        {
            "class": "builtins.dict",
            "kwds": {"key0": "MyVal"},
        },
    "MyVal":
        {
            "class": "builtins.str",
            "args": ["my_val"],
        },
}
factory = DeviceSpinner()
device_trees = factory.create_devices_from_specs(device_specs)
