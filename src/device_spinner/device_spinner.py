"""Class for constructing devices from a yaml file with the factory pattern."""

from pathlib import Path
import copy
import importlib
import logging

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

class DeviceSpinner:

    def __init__(self):
        self.devices = {}
        self.print_level = 0
        self.log = logging.getLogger(f"self.__class__.name")
        pass

    def create_devices_from_specs(self, spec_trees: dict):
        # Construct all devices in device_list.
        for instance_name, init_specifications in spec_trees.items():
            # Skip already-constructed devices.
            if instance_name in self.devices:
                continue
            self.devices[instance_name] = \
                self._create_device(instance_name, init_specifications, spec_trees)
        return self.devices

    def _create_device(self, instance_name: str, device_spec: dict,
                       spec_trees: dict, print_level=0):
        instance_names = spec_trees.keys()
        args = copy.deepcopy(device_spec.get(ARGUMENTS, []))
        skip_args = device_spec.get(SKIP_ARGUMENTS, [])
        skip_kwds = device_spec.get(SKIP_KEYWORDS, [])
        kwds = copy.deepcopy(device_spec.get(KEYWORDS, {}))
        module = importlib.import_module(device_spec["module"])
        cls = getattr(module, device_spec["class"])
        # TODO: handle edge case where object arguments are iterable.
        #   i.e: MyClass([my_other_instance]) vs MyClass(my_other_instance)
        # Populate args and kwds with any dependencies from device_list.
        # Build this instance's positional argument dependencies.
        for index, arg_value in enumerate(args):
            if arg_value in instance_names and arg_value not in skip_args:
                if arg_value not in self.devices:
                    sub_device_spec = spec_trees[arg_value]
                    #print(4*(print_level+1)*" " + f"Creating {instance_name}")
                    self.devices[arg_value] = self._create_device(arg_value,
                                                                  sub_device_spec,
                                                                  spec_trees,
                                                                  print_level+1)
                # Populate the arg index with the object.
                args[index] = self.devices[arg_value]
        # Build this instance's keyword argument dependencies.
        for kwd, kwd_value in kwds.items():
            if kwd_value in instance_names and kwd_value not in skip_kwds:
                if kwd_value not in self.devices:
                    sub_device_spec = spec_trees[kwd_value]
                    #print(4*(print_level+1)*" " + f"Creating {kwd_value}")
                    self.devices[kwd_value] = self._create_device(kwd_value,
                                                                  sub_device_spec,
                                                                  spec_trees,
                                                                  print_level+1)
                # Populate keyword value with the object.
                kwds[kwd] = self.devices[kwd_value]
        # Instantiate class.
        self.log.debug(f"{4*print_level*' '}"
                       f"{instance_name} = {cls.__name__}(" +
                       f"{', '.join([str(a) for a in args])}"
                       f"{', '.join([str(k)+'='+str(v) for k,v in kwds.items()])})")
        return cls(*args, **kwds)
