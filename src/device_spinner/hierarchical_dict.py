"""Hierarchical dict whose nested values are addressable as child nodes."""

from collections import UserDict
from typing import Any, Dict, List, Optional

KeyPath = List[str]


class HierarchicalDict(UserDict[str, Any]):
    """A dict that recursively wraps nested plain dicts as child nodes of the same type.

    Each node holds a reference to its parent, allowing any node to compute
    its full key path from the root via ``_path_from_root()``. The class is
    persistence-agnostic; subclasses can use the path information to implement
    scoped save/load operations.
    """

    def __init__(
        self,
        *args: Any,
        _parent: Optional["HierarchicalDict"] = None,
        _key_in_parent: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self._parent: Optional["HierarchicalDict"] = _parent
        self._key_in_parent: Optional[str] = _key_in_parent
        super().__init__(dict(*args, **kwargs))
        self._convert_nested()

    def _make_child(self, key: str, value: Dict[str, Any]) -> "HierarchicalDict":
        """Wrap a plain dict value as a child node. Subclasses override this
        to produce child instances of their own type."""
        return HierarchicalDict(value, _parent=self, _key_in_parent=key)

    @property
    def is_root(self) -> bool:
        """True if this node has no parent."""
        return self._parent is None

    def _path_from_root(self) -> KeyPath:
        """Return this node's key path from the root.

        The root node returns an empty list. Non-root nodes always have a
        string ``_key_in_parent`` assigned by ``_make_child``.
        """
        current: Optional["HierarchicalDict"] = self
        path: KeyPath = []
        while current is not None and current._parent is not None:
            assert current._key_in_parent is not None
            path.append(current._key_in_parent)
            current = current._parent
        path.reverse()
        return path

    def _convert_nested(self) -> None:
        """Wrap plain dicts already in self.data as child nodes."""
        for key, value in list(self.data.items()):
            if isinstance(value, dict) and not isinstance(value, HierarchicalDict):
                self.data[key] = self._make_child(key, value)

    def __setitem__(self, key: str, value: Any) -> None:
        """Wrap plain dict values as child nodes before storing."""
        if isinstance(value, dict) and not isinstance(value, HierarchicalDict):
            value = self._make_child(key, value)
        super().__setitem__(key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Recursively convert to a plain dict."""
        result: Dict[str, Any] = {}
        for key, value in self.data.items():
            if isinstance(value, HierarchicalDict):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result
