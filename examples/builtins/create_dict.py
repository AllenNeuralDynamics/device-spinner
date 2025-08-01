#!/usr/bin/env python3
"""Instantiate dict."""

from device_spinner.device_spinner import DeviceSpinner

import logging
logging.basicConfig(level=logging.DEBUG)


device_specs = \
{
    "my_dict":
        {
            "class": "builtins.dict",
            "kwds":
            {
                "a": 0,
                "b": 1,
                "c": 2
            }
        },
}
factory = DeviceSpinner()
device_trees = factory.create_devices_from_specs(device_specs)
