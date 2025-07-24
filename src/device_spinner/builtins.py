"""List constructor to create list from *args"""
from typing import List


def to_list(*elements) -> List:
    """Factory function to return list from *args.

    This is a workaround to support creating lists from `DeviceSpinner` that
    use dependency injection to replace instance name strings with the actual
    instances.
    """
    return list(elements)

