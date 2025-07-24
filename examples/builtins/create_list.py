#!/usr/bin/env python3
"""Instantiate list with *args."""

from device_spinner.device_spinner import DeviceSpinner
import pprint

import logging
logging.basicConfig(level=logging.DEBUG)


device_specs = \
{
    "my_list":
        {
            "factory": "device_spinner.builtins.to_list",
            "args":
            [
                0,
                1,
                2
            ]
        },
}
factory = DeviceSpinner()
device_trees = factory.create_devices_from_specs(device_specs)
