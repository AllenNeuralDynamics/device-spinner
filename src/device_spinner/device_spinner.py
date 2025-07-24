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
FACTORY = "factory"
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
        # Bail early: if the instance already exists, return it.
        if instance_name in self.devices:
            return self.devices[instance_name]
        # Otherwise, create the instance and its dependencies.
        self.log.debug(f"{2*_print_level*' '}"
                       f"Creating {instance_name}")
        args = copy.deepcopy(device_spec.get(ARGUMENTS, []))
        argvals_to_skip = device_spec.get(SKIP_ARGUMENTS, [])
        kwdvals_to_skip = device_spec.get(SKIP_KEYWORDS, [])
        kwds = copy.deepcopy(device_spec.get(KEYWORDS, {}))
        factory = self._get_factory(device_spec)
        # Populate args and kwds with any dependencies from device_list.
        # Build this instance's positional argument dependencies.
        args = self._create_args(instance_name, args, argvals_to_skip,
                                 spec_trees, _print_level)
        # Build this instance's keyword argument dependencies.
        kwds = self._create_kwargs(instance_name, kwds, kwdvals_to_skip,
                                   spec_trees, _print_level)
        # Instantiate class.
        self.log.debug(f"{2*_print_level*' '}"
                       f"{instance_name} = {factory.__name__}("
                       f"{', '.join([str(a) for a in args])}"
                       f"{', ' if (len(args) and len(kwds)) else ''}"
                       f"{', '.join([str(k)+'='+str(v) for k,v in kwds.items()])})")
        return factory(*args, **kwds)

    def _get_factory(self, device_spec):
        """return a callable instantiates a class instance.
        Callable may be: (1) a factory function, (2) the class constructor,
        (3) a factory method (factory function that belongs to the class)
        """
        # We're trying to do one of these 3 things:
        #   from module import factory function.
        #   from module import class.
        #   from module import class; from class get factory method.
        # Conscise case: MODULE and CLASS or FACTORY are smushed together.
        if MODULE not in device_spec:
            # Identify the suffix: class or factory function
            if CLASS in device_spec:
                suffix = CLASS
            elif FACTORY in device_spec:
                suffix = FACTORY
            else:
                msg = f"Cannot extract module name from class or factory path. " \
                      f"Either {MODULE} or {CLASS} must be defined prefixed " \
                      f"by the module path."
                raise ValueError(msg)
            try:  # module and class defined together as "class".
                module_name, factory_name = device_spec[suffix].rsplit(".", 1)
                module = importlib.import_module(module_name)
                factory = getattr(module, factory_name)
            except (ImportError, AttributeError) as e:
                msg = f"Module name not specified correctly. Cannot extract " \
                      f"module name from class or factory path: " \
                      f"{device_spec[suffix]}."
                e.args = (f"{msg} " + str(e))
                raise
        else: # Verbose case: MODULE and CLASS or FACTORY are separated.
            # Identify what to import: class or factory function
            if CLASS in device_spec:
                callable_name = CLASS
            elif FACTORY in device_spec:
                callable_name = FACTORY
            module = importlib.import_module(device_spec[MODULE])
            factory = getattr(module, device_spec[callable_name])
        # Override: Take classmethod constructor over class.__init__.
        if CONSTRUCTOR in device_spec and CLASS in device_spec:
            constructor_name = device_spec[CONSTRUCTOR]
            factory = getattr(factory, constructor_name)
        return factory

    def _create_args(self, instance_name: str, args: list, args_to_skip: list,
                     spec_trees: dict, _print_level=0):
        built_args = []
        for arg in args:
            # Edge case: Check against instance name to prevent `_create_device`
            # from recursively stuffing an instance of itself into its own
            # __init__ because a field happens to match its own instance name.
            if arg in args_to_skip or arg == instance_name:
                built_args.append(arg)
                continue
            built_args.append(self._create_nested_arg_value(arg,
                                                            spec_trees,
                                                            _print_level))
        return built_args

    def _create_kwargs(self, instance_name: str, kwargs: dict,
                       kwds_to_skip: list, spec_trees: dict, _print_level=0):
        built_kwargs = {}
        for kwarg_name, kwarg_value in kwargs.items():
            # Edge case: Check against instance name to prevent `_create_device`
            # from recursively stuffing an instance of itself into its own
            # __init__ because a field happens to match its own instance name.
            if kwarg_name in kwds_to_skip or kwarg_value == instance_name:
                built_kwargs[kwarg_name] = kwarg_value
                continue
            built_kwargs[kwarg_name] = self._create_nested_arg_value(kwarg_value,
                                                                     spec_trees,
                                                                     _print_level)
        return built_kwargs

    def _create_nested_arg_value(self, arg_val: Union[str, Any],
                                 spec_trees: dict, _print_level: int = 0):
        """Take a nested list or dictionary and return it with
            named instances replaced with their instances. Populate
            :attr:`~.DeviceSpinner.devices` with any built instances along the
            way. Recursive.

        :param arg_val: input argument value from the device spec for which to
            populate as an arg when instantiating an object.
            Strings with object instances of the same name in the device tree
            will be replaced with the instantiated object.
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
        # Base case. Build the flat argument value or return the original as-is.
        device_spec = spec_trees[arg_val]
        self.devices[arg_val] = self._create_device(arg_val, device_spec,
                                                    spec_trees,
                                                    _print_level+1)
        return self.devices[arg_val]

