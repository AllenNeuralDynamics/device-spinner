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


class Spoke:
    pass

class Hub:
    pass

class Rim:
    pass

class Wheel:
    def __init__(self, hub: Hub, rim: Rim, spokes: list[Spoke]):
        pass


class WheelStarArgs:
    def __init__(self, hub: Hub, rim: Rim, *spokes: Spoke):
        pass


class WheelStarKwargs:
    def __init__(self, hub: Hub, rim: Rim, **spokes: Spoke):
        pass

device_specs = \
{
    "my_bike_wheel":
        {
            "module": __name__,  # this file.
            "class": "Wheel",
            "args": ["rim_700mm", "my_hub", "spoke_list"]
        },

    "spoke_list":
        {
            "factory": "device_spinner.builtins.to_list",
            "args": ["spoke0", "spoke1", "spoke2", "spoke3"]
        },

    "my_bike_wheel_star_args":
        {
            "module": __name__,  # this file.
            "class": "WheelStarArgs",
            "args": ["rim_700mm", "my_hub", "spoke0", "spoke1", "spoke2", "spoke3"]
        },

    "my_bike_wheel_star_kwargs":
        {
            "module": __name__,  # this file.
            "class": "WheelStarKwargs",
            "args": ["rim_700mm", "my_hub"],
            "kwds":
            {
               "spokeA": "spoke0",
               "spokeB": "spoke1",
               "spokeC": "spoke2",
               "spokeD": "spoke3"
            }
        },

    "rim_700mm":
        {
            "module": __name__,
            "class": "Rim",
        },
    "my_hub":
        {
            "module": __name__,
            "class": "Hub",
        },
    "spoke0":
        {
            "module": __name__,
            "class": "Spoke",
        },
    "spoke1":
        {
            "module": __name__,
            "class": "Spoke",
        },
    "spoke2":
        {
            "module": __name__,
            "class": "Spoke",
        },
    "spoke3":
        {
            "module": __name__,
            "class": "Spoke",
        },

}
factory = DeviceSpinner()
device_trees = factory.create_devices_from_specs(device_specs)
