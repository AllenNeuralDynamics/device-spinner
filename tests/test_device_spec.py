from device_spinner.models import DeviceSpec
import pytest

def test_validate_simple_case():
    device_spec = \
    {
        "module": "builtins",
        "class": "dict",
        "kwds": {"key0": "MyVal"},
    }
    DeviceSpec(**device_spec)


def test_validate_empty_module():
    device_spec = \
    {
        "module": "",  # should fail
        "class": "dict",
        "kwds": {"key0": "MyVal"},
    }
    with pytest.raises(ValueError):
        DeviceSpec(**device_spec)


def test_validate_missing_module():
    device_spec = \
    {
        "class": "dict",
        "kwds": {"key0": "MyVal"},
    }
    with pytest.raises(ValueError):
        DeviceSpec(**device_spec)

def test_validate_ambiguous_module_path():
    device_spec = \
    {
        "class": "builtins.dict",
        "factory": "builtins.dict",
        "kwds": {"key0": "MyVal"},
    }
    with pytest.raises(ValueError):
        DeviceSpec(**device_spec)


def test_validate_ambiguous_missing_class():
    device_spec = \
    {
        "kwds": {"key0": "MyVal"},
    }
    with pytest.raises(ValueError):
        DeviceSpec(**device_spec)


def test_serialize_will_exclude_unset_by_default():
    device_spec = \
    {
        "class": "builtins.dict",
        "kwds": {"key0": "MyVal"},
    }
    device_spec_model = DeviceSpec(**device_spec)
    assert device_spec_model.model_dump() == device_spec


def test_serialize_uses_alias():
    device_spec = \
    {
        "class_name": "builtins.dict",
        "kwargs": {"key0": "MyVal"},
    }
    device_spec_expected = \
    {
        "class": "builtins.dict", # use the alias
        "kwds": {"key0": "MyVal"}, # use the alias
    }
    device_spec_model = DeviceSpec(**device_spec)
    assert device_spec_model.model_dump() == device_spec_expected
