"""Class for constructing devices from a yaml file with the factory pattern."""

import copy
import importlib
import logging
from pathlib import Path
from typing import Union

ARGUMENTS = "args"
SKIP_ARGUMENTS = "skip_args"    # List of args with names identical to instance
                                # names in the spec_trees. These args will
                                # be left as strings and *not* replaced with the
                                # object instance of the same name.
KEYWORDS = "kwds"
SKIP_KEYWORDS = "skip_kwds" # List of kwds with names identical to instance
                            # names in the spec_trees. These kwd values will
                            # be left as strings and *not* replaced with the
                            # object instance of the same name.
MODULE = "module"
CLASS = "class"


def gen_enumerate(iterable: Union[dict, list]):
    """provide a generic way to enumerate through dictionaries and lists."""
    if isinstance(iterable, list):
        return enumerate(iterable)
    if isinstance(iterable, dict):
        return iterable.items()
    raise TypeError(f"{iterable} is not iterable.")


class DeviceSpinner:

    def __init__(self):
        self.devices = {}
        self.log = logging.getLogger(f"self.__class__.__name__")
        pass

    def create_devices_from_specs(self, spec_trees: dict):
        # Construct all devices in device_list.
        self.instance_names = spec_trees.keys()
        for instance_name, init_specifications in spec_trees.items():
            # Skip already-constructed devices.
            if instance_name in self.devices:
                continue
            self.devices[instance_name] = \
                self._create_device(instance_name, init_specifications, spec_trees)
        return self.devices

    def _create_device(self, instance_name: str, device_spec: dict,
                       spec_trees: dict, _print_level=0):
        """Instantiate device and dependendent devices and populate them in
        self.devices keyed by instance_name. Recursive.

        :param instance_name:
        :param device_spec:
        :param spec_trees:
        :param _print_level:
        """
        self.log.debug(f"{2*_print_level*' '}"
                       f"Creating {instance_name}")
        args = copy.deepcopy(device_spec.get(ARGUMENTS, []))
        argvals_to_skip = device_spec.get(SKIP_ARGUMENTS, [])
        kwdvals_to_skip = device_spec.get(SKIP_KEYWORDS, [])
        kwds = copy.deepcopy(device_spec.get(KEYWORDS, {}))
        module = importlib.import_module(device_spec[MODULE])
        cls = getattr(module, device_spec["class"])
        # Populate args and kwds with any dependencies from device_list.
        # Build this instance's positional argument dependencies.
        args = self._create_nested_arg_value(args, argvals_to_skip, spec_trees,
                                             _print_level+1)
        # Build this instance's keyword argument dependencies.
        kwds = self._create_nested_arg_value(kwds, kwdvals_to_skip, spec_trees,
                                             _print_level+1)
        # Instantiate class.
        self.log.debug(f"{2*_print_level*' '}"
                       f"{instance_name} = {cls.__name__}(" +
                       f"{', '.join([str(a) for a in args])}"
                       f"{', '.join([str(k)+'='+str(v) for k,v in kwds.items()])})")
        return cls(*args, **kwds)

    def _create_nested_arg_value(self, arg_val, argvals_to_skip, spec_trees,
                                 _print_level=0):
        """Take a nested list or dictionary and return it with
            named instances replaced with their instances. Populate
            :attr:`~.DeviceSpinner.devices` with any built instances along the
            way. Recursive.

        :param arg_val: input argument value from the device spec for which to
            populate as an arg when instantiating an object.
            Strings with object instances of the same name in the device tree
            will be replaced with the instantiate object.
        :param argvals_to_skip: strings in `argval` with names in this list
            will not be populated with object instances of the same name.
        :param spec_trees: dictionary of one or more trees containing object
            instance names, dependencies, and parameters specifying how to
            instantiate them.
        :param _print_level: for debug output logs, this value specifies the
            indentation level to better represent the tree structures.
        """
        try: #i.e: arg_val is iterable as a dict or list.
            # General case. Iterate through each arg_val and build sub-devices.
            for key, item in gen_enumerate(arg_val):
                arg_val[key] = self._create_nested_arg_value(item,
                                                             argvals_to_skip,
                                                             spec_trees,
                                                             _print_level+1)
            return arg_val
        except TypeError:
            pass
        if not isinstance(arg_val, str):
            return arg_val
        if arg_val not in self.instance_names:
            return arg_val
        if arg_val in argvals_to_skip:
            return arg_val
        # Base case. Build the flat argument value or return the original as-is.
        self.log.debug(f"{2*_print_level*' '}"
                       f"Building {arg_val}")
        device_spec = spec_trees[arg_val]
        self.devices[arg_val] = self._create_device(arg_val, device_spec,
                                                    spec_trees,
                                                    _print_level+1)
        return self.devices[arg_val]

