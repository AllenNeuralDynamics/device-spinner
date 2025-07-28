#!/usr/bin/env/python3
import pytest
from device_spinner.device_spinner import DeviceSpinner
from sys import getrecursionlimit, setrecursionlimit

def test_prevent_self_recursion():
    my_config = \
    {
        "my_dict":
        {
            "class": "builtins.dict",
            "kwds":
            {
                "name": "my_dict"  # Should not try to put my_dict into my_dict
            }
        },

        "my_list":
        {
            "factory": "device_spinner.factory_utils.to_list",
            "args": ["my_list"]
        }
    }
    old_limit = getrecursionlimit()
    try:
        setrecursionlimit(100)
        DeviceSpinner().create_devices_from_specs(my_config)
    finally:
        setrecursionlimit(old_limit)

