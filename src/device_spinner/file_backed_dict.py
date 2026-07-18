from pathlib import Path
import json
import yaml
import secrets

from device_spinner.persistent_dict import AbstractPersistentDict, SaverCallback, KeyPath
from typing import Any, Dict, Union


class FileBackedDict(AbstractPersistentDict):
    """File-system implementation handling JSON/YAML string formats."""

    def __init__(self, filepath: Union[str, Path], *args: Any, **kwargs: Any) -> None:
        self.filepath = Path(filepath)
        # Pass extra configs down cleanly without poisoning parent signature
        super().__init__(*args, **kwargs)

    def _wrap(self, value: Any, _root_saver: SaverCallback | None, _key_path: KeyPath | None) -> Any:
        if isinstance(value, dict) and not isinstance(value, FileBackedDict):
            # Dynamically instantiate the exact matching subclass from saved
            # init args & kwargs.
            return self.__class__(self.filepath, value, _root_saver=_root_saver, _key_path=_key_path)
        return value

    def _get_format(self) -> str:
        ext = self.filepath.suffix.lower()
        if ext == '.json': return 'json'
        if ext in ('.yaml', '.yml'): return 'yaml'
        raise ValueError(f"Unsupported format: {ext}")

    def _load_backend_root(self) -> Dict[str, Any]:
        if not self.filepath.exists():
            return {}
        try:
            content = self.filepath.read_text(encoding='utf-8')
            if not content.strip():
                return {}
            fmt = self._get_format()
            data = json.loads(content) if fmt == 'json' else yaml.safe_load(content)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_to_backend(self, data: dict) -> None:
        # Serialize
        fmt = self._get_format()
        output = json.dumps(data, indent=4) if fmt == 'json' else yaml.safe_dump(data, default_flow_style=False, sort_keys=False)

        # Atomic Write
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.filepath.with_suffix(self.filepath.suffix + f".tmp_{secrets.token_hex(4)}")
        try:
            temp_file.write_text(output, encoding='utf-8')
            try:
                temp_file.replace(self.filepath)
            except PermissionError:
                if self.filepath.exists():
                    self.filepath.unlink()
                temp_file.rename(self.filepath)
        except Exception:
            if temp_file.exists():
                temp_file.unlink()
            raise
