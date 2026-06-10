from inspect import signature
from functools import cached_property
from pydantic import BaseModel, RootModel, Field, model_validator, ConfigDict
from typing import Optional, Any, Self, Callable
import importlib

class DeviceSpec(BaseModel):
    """
    Examples
    --------
    >>> data = {'module': 'builtins', 'class': 'dict', 'kwargs': {'key0': 'MyVal'}}
    >>> DeviceSpec.model_validate(data).model_dump(exclude_none=True)
    {'module_name': 'builtins', 'class_name': 'dict', 'kwargs': {'key0': 'MyVal'}}

    >>> data = {'module': '', 'class': 'dict', 'kwargs': {'key0': 'MyVal'}}
    >>> DeviceSpec.model_validate(data) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    pydantic_core._pydantic_core.ValidationError: ...

    >>> data = {'class': 'dict', 'kwargs': {'key0': 'MyVal'}}
    >>> DeviceSpec.model_validate(data) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    pydantic_core._pydantic_core.ValidationError: ...

    >>> data = {'class': 'builtins.dict', 'factory': 'builtins.dict', 'kwargs': {'key0': 'MyVal'}}
    >>> DeviceSpec.model_validate(data) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    pydantic_core._pydantic_core.ValidationError: ...

    >>> data = {'kwargs': {'key0': 'MyVal'}}
    >>> DeviceSpec.model_validate(data) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    pydantic_core._pydantic_core.ValidationError: ...
    """
    # Enable the model to accept either 'kwds' or 'kwargs'
    model_config = ConfigDict(populate_by_name=True)

    module_name: Optional[str] = Field(alias="module", default=None)
    class_name: Optional[str] = Field(alias="class", default=None)
    factory: Optional[str] = None
    constructor_name: Optional[str] = Field(alias="constructor", default=None)

    args: Optional[list[Any]] = None
    kwargs: Optional[dict[str, Any]] = Field(alias="kwds", default=None)

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
                module_path, _ = self.factory.rsplit(".", 1)
        else:
            module_path = self.module_name
        return module_path

    @cached_property
    def factory_fn_name(self) -> str:
        # Simple case: return factory or class field directly.
        if self.module_name is not None:
            if self.class_name is not None:
                return self.class_name
            if self.factory is not None:
                return self.factory
        else:  # Deduce it from combined paths.
            if self.class_name is not None:
                return self.class_name.rsplit(".", 1)[-1]
            if self.factory is not None:
                return self.factory.rsplit(".", 1)[-1]
        raise ValueError("Cannot deduce factory function name.")

    @cached_property
    def factory_fn(self) -> Callable[..., ...]:
        """return a callable to instantiate the class instance.
        Callable may be: (1) a factory function, (2) the class constructor,
        (3) a factory method (factory function that belongs to the class)
        """
        # We're trying to do one of these 3 things:
        #   from module import factory function.
        #   from module import class.
        #   from module import class; from class get factory method.
        module = importlib.import_module(self.module_path)
        class_or_factory = getattr(module, self.factory_fn_name)
        if self.constructor_name is not None:
            class_or_factory = getattr(class_or_factory, self.constructor_name)
        return class_or_factory

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

    @model_validator(mode='after')
    def validate_dependency_existence(self) -> Self:
        """Iterate through all entries and ensure that any arg/kwarg values
        specified as strings that are class instances in the function signature
        exist elsewhere."""
        #for instance_name, spec in self.root.items():
        #    print(f"factory function is {spec.factory_fn}")
        #    try:
        #        sig = signature(spec.factory_fn)
        #        print(sig.parameters)
        #    except ValueError:
        #        print(f"Cannot print parameters for {spec.factory_fn}.")
        #    if spec.args is not None:
        #        for index, arg in enumerate(spec.args):
        #            # Check signature for any class type.
        #            pass
        #    if spec.kwargs is not None:
        #        for name, val in spec.kwargs:
        #            # Check signature for any class type.
        #            pass
        return self
