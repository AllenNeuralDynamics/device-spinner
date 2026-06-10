from _pytest.nodes import File
from device_spinner.file_backed_dict import FileBackedDict
from copy import deepcopy


def get_example_file_backed_dict(tmp_path) -> FileBackedDict:
    """Make a FileBackedDict instance from an empty config.yaml file"""
    path = tmp_path / "config.yaml"  # Empty yaml.
    config = FileBackedDict(path)
    config["users"] = {"Fred": {"age": 42,
                                "fave_recipe": {"name": "fried strings",
                                                "ingredients": ["string", "strfry"],
                                                "instructions": ["Saute the string.",
                                                                 "Cool and serve."]}}}
    return config


def test_to_dict_comparison(tmp_path):
    path = tmp_path / "config.yaml"  # Empty yaml.
    config = FileBackedDict(path)
    config["database"] = {"host": "localhost", "port": 5432}
    config["logging"] = {"level": "INFO"}

    config_dict = {"database":{"host": "localhost", "port": 5432},
                   "logging": {"level": "INFO"}}
    assert config.to_dict() == config_dict


def test_parent_altering_child_scope_attributes_changes_child_attributes(tmp_path):
    config = get_example_file_backed_dict(tmp_path)
    # Make child.
    freds_fave_recipe = config["users"]["Fred"]["fave_recipe"]
    # Change child values from the parent.
    config["users"]["Fred"]["fave_recipe"]["ingredients"][1] = "strcmp"
    # Change should be reflected in the child.
    assert freds_fave_recipe["ingredients"][1] == "strcmp"


def test_child_altering_attributes_changes_same_attributes_in_parent(tmp_path):
    config = get_example_file_backed_dict(tmp_path)
    # Make child.
    freds_fave_recipe = config["users"]["Fred"]["fave_recipe"]
    # Change child values from the parent.
    config["users"]["Fred"]["fave_recipe"]["ingredients"][1] = "strcmp"
    # Change should be reflected in the child.
    assert freds_fave_recipe["ingredients"][1] == "strcmp"


def test_saving(tmp_path):
    path = tmp_path / "config.yaml"  # Empty yaml.
    config = FileBackedDict(path)
    config["pockets"] = ["keys", "spare change", "the one ring"]
    config.save()
    # Import changes from file into a separate instance.
    config2 = FileBackedDict(path)
    assert config2.to_dict() == config.to_dict()


def test_saving_child_only_saves_child_scope_changes(tmp_path):
    config = get_example_file_backed_dict(tmp_path)
    # Make child.
    freds_fave_recipe = config["users"]["Fred"]["fave_recipe"]
    # Alter child
    freds_fave_recipe["name"] = "tomato soup"
    # Alter parent
    config["users"]["Frankie"] = {"age": 27,
                                  "fave_recipe": {"name": "onion soup",
                                                  "ingredients": ["onions", "broth"],
                                                  "instructions": ["boil for 10 mins.",
                                                                   "Cool and serve."]}}
    freds_fave_recipe.save() # should not save out-of-scope changes.
    # Import changes from file into a separate instance.
    path = tmp_path / "config.yaml"  # recently-saved yaml
    config2 = FileBackedDict(path)
    assert "Frankie" not in config2.to_dict()["users"]


def test_saving_parent_also_saves_child_scope_changes(tmp_path):
    config = get_example_file_backed_dict(tmp_path)
    # Make child.
    freds_fave_recipe = config["users"]["Fred"]["fave_recipe"]
    # Alter child
    freds_fave_recipe["name"] = "tomato soup"
    # Alter parent
    config["users"]["Frankie"] = {"age": 27,
                                  "fave_recipe": {"name": "onion soup",
                                                  "ingredients": ["onions", "broth"],
                                                  "instructions": ["boil for 10 mins.",
                                                                   "Cool and serve."]}}
    # Alter child
    freds_fave_recipe["name"] = "string beans"
    # Save parent
    config.save() # should save everything.
    # Import changes from file into a separate instance.
    path = tmp_path / "config.yaml"  # recently-saved yaml
    config2 = FileBackedDict(path)
    # Child changes should exist.
    assert config2["users"]["Fred"]["fave_recipe"]["name"] == "string beans"

def test_save_child_only_before_parent_changes(tmp_path):
    """Test edge case where we add to the dict from a child and ONLY save the
    child. When we reload, none of the parent data should exist."""
    # FYI: config.yaml starts empty but has local changes in the FileBackedDict
    # data structure.
    config = get_example_file_backed_dict(tmp_path)
    config["users"]["Naomi"] = {"age": 23,
                                "fave_recipe": None}
    # Get a subset
    naomi_cfg = config["users"]["Naomi"]
    # config.yaml is still empty at this point since we've only made unsaved changes.
    # Calling save from the child should *only* save child scope changes.
    # naomi_cfg doesn't know anyting about Fred entry, and Fred entry has not
    # yet been saved. Saved config should not include Fred entry.
    naomi_cfg.save()
    # Open a copy of the same file to ensure changes persist.
    reloaded_config = FileBackedDict(tmp_path / "config.yaml")
    assert "Fred" not in reloaded_config["users"]
    assert "Naomi" in reloaded_config["users"]


def test_union_operator_new_instance(tmp_path):
    config = get_example_file_backed_dict(tmp_path)
    config_as_dict = config.to_dict()
    dict_b = {"Naomi": {"age": 23,
                        "fave_recipe": None}}

    # Check union operator both ways. Both cases should "promote" to a FileBackedDict
    result_a = config | dict_b
    assert (type(result_a) is FileBackedDict) and result_a == (config_as_dict | dict_b)
    assert id(result_a) != id(config) # Should create a new instance.

    result_b = dict_b | config
    assert (type(result_b) is FileBackedDict) and result_b == (dict_b | config_as_dict)
    assert id(result_b) != id(config) # Should create a new instance.


def test_union_operator_update_original(tmp_path):
    config = get_example_file_backed_dict(tmp_path)
    config_as_dict = config.to_dict()
    dict_b = {"Naomi": {"age": 23,
                        "fave_recipe": None}}

    # Check |= operator updating FileBackedDict
    config["users"] |= dict_b
    config_as_dict["users"] |= dict_b
    assert config.to_dict() == config_as_dict


def test_union_operator_update_dict(tmp_path):
    config = get_example_file_backed_dict(tmp_path)
    config_as_dict = config.to_dict()
    dict_b = {"Naomi": {"age": 23,
                        "fave_recipe": None}}
    dict_b2 = deepcopy(dict_b)
    # Check |= operator updating plain dict.
    dict_b |= config["users"]
    dict_b2 |= config_as_dict["users"]
    assert (type(dict_b) is dict) and (dict_b == dict_b2)

def test_union_operator_on_subset(tmp_path):
    # FYI: config.yaml starts empty but has local changes in the FileBackedDict
    # data structure.
    config = get_example_file_backed_dict(tmp_path)
    config.save()  # Save changes back to file so we don't reload empty.
    # Get a subset
    fred_cfg = config["users"]["Fred"]
    # Update subset
    new_recipe = {"fave_recipe": {"name": "pinto beans",
                                  "ingredients": ["pinto_beans", "water"],
                                  "instructions": ["soak beans overnight",
                                                   "low boil for 3 hours",
                                                   "Cool and serve."]}}
    fred_cfg |= new_recipe
    fred_cfg.save()
    # Open a copy of the same file to ensure changes persist.
    reloaded_config = FileBackedDict(tmp_path / "config.yaml")
    assert (config == reloaded_config)
