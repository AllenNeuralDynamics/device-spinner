from device_spinner.models import DeviceTrees


def test_validate_simple_tree_case():
    device_specs = \
    {
        "MyDict":
            {
                "class": "builtins.dict",
                "kwds": {"key0": "MyVal"},
            },
        "MyVal":
            {
                "class": "builtins.str",
                "args": ["my_val"],
            },
    }
    DeviceTrees(**device_specs)
