"""Nested Saveable Dict vibe-coded with Gemini"""
from collections import UserDict
from pathlib import Path
import secrets
from typing import Any, Callable, Dict, List, Literal, Optional, Union
import json
import yaml

# Define types for paths and saving callbacks
KeyPath = List[str]
SaverCallback = Callable[[Optional[KeyPath], Optional[Dict[str, Any]]], None]
SupportedFormat = Literal['json', 'yaml']

class FileBackedDict(UserDict[str, Any]):
    """Dict with a `save()` method that propagates to subdicts originating from
    the same file source.
    """
    def __init__(self, filepath: Union[str, Path], *args: Any,
                 _root_saver: Optional[SaverCallback] = None,
                 _key_path: Optional[KeyPath] = None, **kwargs: Any) -> None:
        self.filepath: Path = Path(filepath)
        self._root_saver: Optional[SaverCallback] = _root_saver
        self._key_path: KeyPath = _key_path or []

        initial_data: Dict[str, Any] = {}
        if _root_saver is not None:
            initial_data = {}
        elif self.filepath.exists():
            initial_data = self._load_from_file()
        else:
            initial_data = {}

        initial_data.update(dict(*args, **kwargs))
        super().__init__(initial_data)
        self._convert_nested()

    def _get_format(self) -> SupportedFormat:
        """Detects format based on file extension using pathlib."""
        ext: str = self.filepath.suffix.lower()
        if ext == '.json':
            return 'json'
        elif ext in ('.yaml', '.yml'):
            return 'yaml'
        raise ValueError(f"Unsupported file extension: '{ext}'. Use .json, .yaml, or .yml")

    def _load_from_file(self) -> Dict[str, Any]:
        """Reads and parses data based on the file type."""
        fmt: SupportedFormat = self._get_format()
        try:
            content: str = self.filepath.read_text(encoding='utf-8')
            if fmt == 'json':
                data = json.loads(content)
                return data if isinstance(data, dict) else {}
            elif fmt == 'yaml':
                data = yaml.safe_load(content)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, yaml.YAMLError, OSError):
            return {}
        return {}

    def _convert_nested(self) -> None:
        """Wraps plain dictionaries inside this dict as child instances."""
        saver: SaverCallback = self._root_saver if self._root_saver else self._save_partial
        for key, value in list(self.data.items()):
            if isinstance(value, dict) and not isinstance(value, FileBackedDict):
                child_path: KeyPath = self._key_path + [key]
                self.data[key] = FileBackedDict(
                    self.filepath, value, _root_saver=saver, _key_path=child_path
                )

    def __setitem__(self, key: str, value: Any) -> None:
        saver: SaverCallback = self._root_saver if self._root_saver else self._save_partial
        if isinstance(value, dict) and not isinstance(value, FileBackedDict):
            child_path: KeyPath = self._key_path + [key]
            value = FileBackedDict(self.filepath, value, _root_saver=saver, _key_path=child_path)
        super().__setitem__(key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Recursively converts FileBackedDict instances back to primitive dictionaries."""
        result: Dict[str, Any] = {}
        for key, value in self.data.items():
            if isinstance(value, FileBackedDict):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result

    def _save_partial(self, target_path: Optional[KeyPath] = None, partial_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Loads the file from disk, updates only the targeted subset fields,
        and saves it back using an atomic write strategy.
        """
        full_data: Dict[str, Any] = self._load_from_file() if self.filepath.exists() else {}

        if target_path and partial_data is not None:
            current: Any = full_data
            for step in target_path[:-1]:
                if step not in current or not isinstance(current[step], dict):
                    current[step] = {}
                current = current[step]

            if target_path:
                current[target_path[-1]] = partial_data
        else:
            full_data = self.to_dict()

        fmt: SupportedFormat = self._get_format()

        if fmt == 'json':
            output: str = json.dumps(full_data, indent=4)
        elif fmt == 'yaml':
            output = yaml.safe_dump(full_data, default_flow_style=False, sort_keys=False)

        # Ensure target directory exists
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # --- ATOMIC WRITE ---
        # Generate a unique temp file name in the target directory to guarantee
        # they're on the same filesystem
        temp_suffix = f".tmp_{secrets.token_hex(4)}"
        temp_file = self.filepath.with_suffix(self.filepath.suffix + temp_suffix)

        try:
            # 1. Write data to the temporary file completely
            temp_file.write_text(output, encoding='utf-8')

            # 2. Atomically swap/replace the temp file over the target destination file
            temp_file.replace(self.filepath)
        except Exception:
            # Clean up the temp file if the write process itself failed
            if temp_file.exists():
                temp_file.unlink()
            raise

    def save(self) -> None:
        """Triggers a partial save targeting only this instance's keys."""
        if self._root_saver:
            self._root_saver(self._key_path, self.to_dict())
        else:
            self._save_partial()
