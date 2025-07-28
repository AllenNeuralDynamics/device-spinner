#!/usr/bin/env/python3
import pytest
from device_spinner.device_spinner import DeviceSpinner
from sys import getrecursionlimit, setrecursionlimit

def test_prevent_self_recursion():
    """
    Ensure that arg/kwarg field names whose values match the instance name do
    not get replaced by the instantiated object when not explicitly marked in
    `skip_args` or `skip_kwds`.
    """
    my_config = \
    {
        "my_dict":
        {
            "class": "builtins.dict",
            "kwds":
            {
                "name": "my_dict"  # Should not put my_dict instance into __init__
            }
        },

        "my_list":
        {
            "factory": "device_spinner.factory_utils.to_list",
            "args": ["my_list"]  # Should not put my_list instance into __init__
        }
    }
    old_limit = getrecursionlimit()
    try:
        setrecursionlimit(100)
        DeviceSpinner().create_devices_from_specs(my_config)
    finally:
        setrecursionlimit(old_limit)

