from multiprocessing import Value

from functools import cached_property
from pydantic import BaseModel, RootModel, Field, model_validator
from typing import Optional, Any, Self
import importlib

class DeviceSpec(BaseModel):
    module_name: Optional[str] = Field(alias="module", default=None)
    class_name: Optional[str] = Field(alias="class", default=None)
    factory: Optional[str] = None

    args: Optional[list[Any]] = None
    kwds: Optional[dict[str, Any]] = None

    skip_args: Optional[list[str]] = None
    skip_kwds: Optional[list[str]] = None

    constructor: Optional[str] = None

    @cached_property  # compute once.
    def module_path(self) -> str:
        module_path = ""
        if self.module_name is None:
            if self.class_name is not None:
                module_path, _ = self.class_name.rsplit(".", 1)
            elif self.factory is not None:
                module_path, _ = self.class_name.rsplit(".", 1)
        else:
            module_path = self.module_name
        return module_path

    @model_validator(mode='after')
    def validate_class_or_factory(self) -> Self:
        if (self.class_name is None) and (self.factory is None):
            raise ValueError("Either 'class' or 'factory' must be specified.")
        return self

    @model_validator(mode='after')
    def validate_factory_path_shorthand(self) -> Self:
        """If module field is omitted, and module-and-class or module-and-factory
        are combined, validate that a module path can be deduced."""
        # Bail early.
        if self.module_name is not None:  # Does not apply.
            return self
        if ((self.class_name is not None and "." not in self.class_name) or
            (self.factory is not None and "." not in self.factory)):
            raise ValueError("'module' field can only be omitted if module "
                             "path is prepended to either 'class' or factory "
                             "field and separated with a '.' character.")
        # Validate that shorthand is EITHER OR
        if ((self.class_name is not None) and (self.factory is not None) and
            ("." in self.class_name) and ("." in self.factory)):
            raise ValueError("Ambiguous module path!")
        return self # return self by "after" model validator convention.

    @model_validator(mode='after')
    def validate_module_import(self) -> Self:
        try:
            importlib.import_module(self.module_path)
        except ImportError:
            raise ValueError(f"module: {self.module_path} does not exist.")
        return self

    # TODO: Validate constructor exists.
    # TODO: Validate input arg/kwarg types.
    # TODO: Validate signature.


class DeviceTrees(RootModel[dict[str, DeviceSpec]]):
    pass
