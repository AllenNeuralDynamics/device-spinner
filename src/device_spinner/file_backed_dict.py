"""File-backed persistence utilities for HierarchicalDict."""

from pathlib import Path
import secrets
from typing import Any, Dict, Literal, Union
import json
import yaml

from .hierarchical_dict import (
    HierarchicalDict,
    KeyPath,
)


## File I/O utilities


def _set_nested(data: Dict[str, Any], path: KeyPath, value: Any) -> None:
    """Modify data by assigning value into the nested path, creating intermediate dicts as needed."""
    for key in path[:-1]:
        if not isinstance(data.get(key), dict):
            data[key] = {}
        data = data[key]
    data[path[-1]] = value


SupportedFormat = Literal["json", "yaml"]


def _get_format(filepath: Path) -> SupportedFormat:
    """Detect serialisation format from file extension."""
    ext: str = filepath.suffix.lower()
    if ext == ".json":
        return "json"
    if ext in (".yaml", ".yml"):
        return "yaml"
    raise ValueError(f"Unsupported file extension: '{ext}'. Use .json, .yaml, or .yml")


def _load_dict_from_file(filepath: Path) -> Dict[str, Any]:
    """Load top-level mapping from a json/yaml file."""
    fmt: SupportedFormat = _get_format(filepath)
    try:
        content: str = filepath.read_text(encoding="utf-8")
        if fmt == "json":
            data = json.loads(content)
            return data if isinstance(data, dict) else {}
        data = yaml.safe_load(content)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, yaml.YAMLError, OSError):
        return {}


def _dump_dict_to_file(filepath: Path, full_data: Dict[str, Any]) -> None:
    """Atomically write a mapping to a json/yaml file."""
    fmt: SupportedFormat = _get_format(filepath)
    if fmt == "json":
        output: str = json.dumps(full_data, indent=4)
    else:
        output = yaml.safe_dump(full_data, default_flow_style=False, sort_keys=False)

    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + f".tmp_{secrets.token_hex(4)}")
    try:
        temp_file.write_text(output, encoding="utf-8")
        temp_file.replace(filepath)
    except Exception:
        if temp_file.exists():
            temp_file.unlink()
        raise


class FileBackedDict(HierarchicalDict):
    """HierarchicalDict bound to a json/yaml file.

    All dict behaviour is inherited from ``HierarchicalDict``. Only
    file-loading, child-creation, and persistence are overridden.

    Use ``FileBackedDict.init_root(filepath)`` to create an instance.
    Call ``.save()`` to write changes back and ``.load()`` to pull in
    changes from disk.
    """

    @classmethod
    def init_root(
        cls, filepath: Union[str, Path], *args: Any, **kwargs: Any
    ) -> "FileBackedDict":
        """Create a root FileBackedDict backed by a file.

        Loads existing file contents, then applies any extra keyword or
        positional arguments as an overlay (same semantics as ``dict.update``).
        """
        instance = cls()
        instance._filepath = Path(filepath)
        instance.load()
        if args or kwargs:
            instance.update(dict(*args, **kwargs))
        return instance

    @property
    def filepath(self) -> Path:
        """Path to the backing file. Owned by the root; children delegate upward."""
        if self.is_root:
            return self._filepath
        return self._parent.filepath  # type: ignore[union-attr]

    def _make_child(self, key: str, value: Dict[str, Any]) -> "FileBackedDict":
        """Override to keep children as FileBackedDict so they share filepath."""
        return FileBackedDict(value, _parent=self, _key_in_parent=key)

    def load(self, *, replace: bool = True) -> None:
        """Load/reload this node's scope from file.

        Root node operates on the full tree; a child node operates only on its
        own scope, leaving sibling keys in memory untouched.

        Args:
            replace: If True (default), clear in-memory keys before applying
                file data so the result exactly mirrors the file. If False,
                merge file data on top of memory, leaving keys absent from the
                file untouched.
        """
        file_data: Dict[str, Any] = (
            _load_dict_from_file(self.filepath) if self.filepath.exists() else {}
        )
        if not self.is_root:
            for key in self._path_from_root():
                file_data = file_data.get(key, {})
        if replace:
            self.data.clear()
        self.update(file_data)

    def save(self) -> None:
        """Save this node's scope back to file.

        Root node writes the full tree; a child node merges only its scope
        into the existing file, leaving sibling keys untouched.
        """
        path = self.filepath
        full_data = _load_dict_from_file(path) if path.exists() else {}
        if self.is_root:
            full_data = self.to_dict()
        else:
            _set_nested(full_data, self._path_from_root(), self.to_dict())
        _dump_dict_to_file(path, full_data)
