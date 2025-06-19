"""Class for constructing devices from a yaml file with the factory pattern."""

import copy
import importlib
import logging
from pathlib import Path
from typing import Union, Any

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
CONSTRUCTOR = "constructor" # Optional if __init__ is sufficient to
                            # instantiate the class.


class DeviceSpinner:

    def __init__(self):
        self.devices = {}
        self.instance_names = set()
        self.log = logging.getLogger(f"{self.__class__.__name__}")
        pass

    def create_devices_from_specs(self, spec_trees: dict):
        # Construct all devices in device_list.
        self.instance_names = set(spec_trees.keys())
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
        constructor = cls
        # Take classmethod constructor if specified.
        constructor_name = device_spec.get(CONSTRUCTOR, None)
        if constructor_name is not None:
            constructor = getattr(cls, constructor_name)
        # Populate args and kwds with any dependencies from device_list.
        # Build this instance's positional argument dependencies.
        args = self._create_args(args, argvals_to_skip, spec_trees,
                                 _print_level+1)
        # Build this instance's keyword argument dependencies.
        kwds = self._create_kwargs(kwds, kwdvals_to_skip, spec_trees,
                                   _print_level+1)
        # Instantiate class.
        self.log.debug(f"{2*_print_level*' '}"
                       f"{instance_name} = {cls.__name__}("
                       f"{', '.join([str(a) for a in args])}"
                       f"{', ' if (len(args) and len(kwds)) else ''}"
                       f"{', '.join([str(k)+'='+str(v) for k,v in kwds.items()])})")
        return constructor(*args, **kwds)

    def _create_args(self, args, args_to_skip, spec_trees, _print_level=0):
        built_args = []
        for arg in args:
            built_args.append(self._create_nested_arg_value(arg,
                                                            args_to_skip,
                                                            spec_trees,
                                                            _print_level + 1))
        return built_args

    def _create_kwargs(self, kwargs, args_to_skip, spec_trees, _print_level=0):
        built_kwargs = {}
        for kwarg_name, kwarg_value in kwargs.items():
            built_kwargs[kwarg_name] = self._create_nested_arg_value(kwarg_value,
                                                                     args_to_skip,
                                                                     spec_trees,
                                                                     _print_level + 1)
        return built_kwargs

    def _create_nested_arg_value(self, arg_val: Union[str, Any],
                                 argvals_to_skip: list, spec_trees: dict,
                                 _print_level: int = 0):
        """Take a nested list or dictionary and return it with
            named instances replaced with their instances. Populate
            :attr:`~.DeviceSpinner.devices` with any built instances along the
            way. Recursive.

        :param arg_val: input argument value from the device spec for which to
            populate as an arg when instantiating an object.
            Strings with object instances of the same name in the device tree
            will be replaced with the instantiated object.
        :param argvals_to_skip: strings in `argval` with names in this list
            will not be populated with object instances of the same name.
        :param spec_trees: dictionary of one or more trees containing object
            instance names, dependencies, and parameters specifying how to
            instantiate them.
        :param _print_level: for debug output logs, this value specifies the
            indentation level to better represent the tree structures.
        """
        if not isinstance(arg_val, str):  # Only replace string matching instance name
            return arg_val
        if arg_val not in self.instance_names:
            return arg_val
        if arg_val in argvals_to_skip:
            return arg_val
        # Base case. Build the flat argument value or return the original as-is.
        device_spec = spec_trees[arg_val]
        self.devices[arg_val] = self._create_device(arg_val, device_spec,
                                                    spec_trees,
                                                    _print_level+1)
        return self.devices[arg_val]

