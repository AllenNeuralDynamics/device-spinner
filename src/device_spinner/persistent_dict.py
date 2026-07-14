from abc import ABC, abstractmethod
from collections import UserDict
from typing import Any, Callable, Dict, List, Optional, Protocol

KeyPath = List[str]
SaverCallback = Callable[[Optional[KeyPath], Optional[Dict[str, Any]]], None]


class SaveableDict(Protocol):
    """Dict with an included save function."""
    def save(self) -> None:
        ...


class AbstractPersistentDict(UserDict[str, Any], ABC):
    """
    Abstract Base Class for scoped, nested dictionaries bound and saveable to
    persistent backends.

    Handles mutation intercepting, recursive wrapping, and partial path routing.
    Subclasses need only implement backend-specific hooks and wrapper function.
    """

    def __init__(
        self,
        *args: Any,
        _root_saver: Optional[SaverCallback] = None,
        _key_path: Optional[KeyPath] = None,
        **kwargs: Any
    ) -> None:
        self._root_saver: Optional[SaverCallback] = _root_saver
        self._key_path: KeyPath = _key_path or []

        initial_data: Dict[str, Any] = {}

        # Only fetch data from the persistent backend if this is the root node
        # and no memory-overrides are passed explicitly to __init__
        if self._root_saver is None and not args and not kwargs:
            initial_data = self._load_backend_root()
        else:
            if args:
                if len(args) > 1:
                    raise TypeError(f"expected at most 1 argument, got {len(args)}")
                initial_data.update(args[0])
            if kwargs:
                initial_data.update(kwargs)

        super().__init__(initial_data)
        self._convert_nested()

    @abstractmethod
    def _load_backend_root(self) -> Dict[str, Any]:
        """Read and return the entire baseline dictionary state from the storage backend."""
        pass

    @abstractmethod
    def _save_to_backend(self, data: dict):
        pass

    @abstractmethod
    def _wrap(self, value: Any, _root_saver: SaverCallback | None,
              _key_path: KeyPath | None) -> Any:
        pass

    def _wrap_value(self, key: str, value: Any) -> Any:
        """Wrap sub-dictionaries inside matching instance types dynamically."""
        if isinstance(value, dict) and not isinstance(value, AbstractPersistentDict):
            saver: SaverCallback = self._root_saver if self._root_saver else self._save_partial
            child_path: KeyPath = self._key_path + [key]
            # Dynamically instantiate the exact matching subclass (e.g., FileBackedDict)
            return self._wrap(value, _root_saver=saver, _key_path=child_path)
        return value

    def _save_partial(self, target_path: Optional[KeyPath], partial_data: Optional[Dict[str, Any]]) -> None:
        """Write a specific sub-path block or the full object state to the storage backend."""
        # Fetch current on-disk baseline state
        full_data = self._load_backend_root()
        # Patch specific nested layout target
        if target_path and partial_data is not None:
            current = full_data
            for step in target_path[:-1]:
                if step not in current or not isinstance(current[step], dict):
                    current[step] = {}
                current = current[step]
            current[target_path[-1]] = partial_data
        else:
            full_data = self.to_dict()
        self._save_to_backend(full_data)

    def _convert_nested(self) -> None:
        for key, value in list(self.data.items()):
            self.data[key] = self._wrap_value(key, value)

    # --- Mutation Hooks ---
    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key, self._wrap_value(key, value))

    def update(self, *args: Any, **kwargs: Any) -> None:
        other = dict(*args, **kwargs)
        for k, v in other.items():
            self[k] = v

    def setdefault(self, key: str, default: Any = None) -> Any:
        if key not in self:
            self[key] = default
        return self[key]

    # --- Dictionary Merge Bitwise Operations ---
    def __or__(self, other: Any) -> "AbstractPersistentDict":
        if not isinstance(other, dict):
            return NotImplemented
        new_data = self.to_dict()
        other_data = other.to_dict() if isinstance(other, AbstractPersistentDict) else other
        new_data.update(other_data)
        return self._wrap(new_data, _root_saver=self._root_saver, _key_path=self._key_path)

    def __ror__(self, other: Any) -> "AbstractPersistentDict":
        if not isinstance(other, dict):
            return NotImplemented
        new_data = dict(other)
        new_data.update(self.to_dict())
        return self._wrap(new_data, _root_saver=self._root_saver, _key_path=self._key_path)

    def __ior__(self, other: Any) -> "AbstractPersistentDict":
        if not isinstance(other, dict):
            return NotImplemented
        other_data = other.to_dict() if isinstance(other, AbstractPersistentDict) else other
        self.data.update(other_data)
        self._convert_nested()
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Recursively formats structures back down to generic Python dict primitives."""
        result: Dict[str, Any] = {}
        for key, value in self.data.items():
            if isinstance(value, AbstractPersistentDict):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result

    def save(self) -> None:
        """Triggers persistent writeout of this structural tree's state to storage."""
        if self._root_saver:
            self._root_saver(self._key_path, self.to_dict())
        else:
            self._save_partial(self._key_path, self.to_dict())
