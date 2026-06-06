from _pytest.nodes import File
from device_spinner.file_backed_dict import FileBackedDict


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
