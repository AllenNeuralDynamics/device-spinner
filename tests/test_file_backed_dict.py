from device_spinner.file_backed_dict import FileBackedDict


def get_example_file_backed_dict(tmp_path) -> FileBackedDict:
    """Make a FileBackedDict instance from an empty config.yaml file"""
    path = tmp_path / "config.yaml"  # Empty yaml.
    config = FileBackedDict.init_root(path)
    config["users"] = {
        "Fred": {
            "age": 42,
            "fave_recipe": {
                "name": "fried strings",
                "ingredients": ["string", "strfry"],
                "instructions": ["Saute the string.", "Cool and serve."],
            },
        }
    }
    return config


def test_to_dict_comparison(tmp_path):
    path = tmp_path / "config.yaml"  # Empty yaml.
    config = FileBackedDict.init_root(path)
    config["database"] = {"host": "localhost", "port": 5432}
    config["logging"] = {"level": "INFO"}

    config_dict = {
        "database": {"host": "localhost", "port": 5432},
        "logging": {"level": "INFO"},
    }
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
    config = FileBackedDict.init_root(path)
    config["pockets"] = ["keys", "spare change", "the one ring"]
    config.save()
    # Import changes from file into a separate instance.
    config2 = FileBackedDict.init_root(path)
    assert config2.to_dict() == config.to_dict()


def test_saving_child_only_saves_child_scope_changes(tmp_path):
    config = get_example_file_backed_dict(tmp_path)
    # Make child.
    freds_fave_recipe = config["users"]["Fred"]["fave_recipe"]
    # Alter child
    freds_fave_recipe["name"] = "tomato soup"
    # Alter parent
    config["users"]["Frankie"] = {
        "age": 27,
        "fave_recipe": {
            "name": "onion soup",
            "ingredients": ["onions", "broth"],
            "instructions": ["boil for 10 mins.", "Cool and serve."],
        },
    }
    freds_fave_recipe.save()  # should not save out-of-scope changes.
    # Import changes from file into a separate instance.
    path = tmp_path / "config.yaml"  # recently-saved yaml
    config2 = FileBackedDict.init_root(path)
    assert "Frankie" not in config2.to_dict()["users"]


def test_saving_parent_also_saves_child_scope_changes(tmp_path):
    config = get_example_file_backed_dict(tmp_path)
    # Make child.
    freds_fave_recipe = config["users"]["Fred"]["fave_recipe"]
    # Alter child
    freds_fave_recipe["name"] = "tomato soup"
    # Alter parent
    config["users"]["Frankie"] = {
        "age": 27,
        "fave_recipe": {
            "name": "onion soup",
            "ingredients": ["onions", "broth"],
            "instructions": ["boil for 10 mins.", "Cool and serve."],
        },
    }
    # Alter child
    freds_fave_recipe["name"] = "string beans"
    # Save parent
    config.save()  # should save everything.
    # Import changes from file into a separate instance.
    path = tmp_path / "config.yaml"  # recently-saved yaml
    config2 = FileBackedDict.init_root(path)
    # Child changes should exist.
    assert config2["users"]["Fred"]["fave_recipe"]["name"] == "string beans"


def test_parent_pointers_compute_child_path_and_save_scope(tmp_path):
    path = tmp_path / "config.yaml"
    config = FileBackedDict.init_root(path)
    config["root"] = {"child": {"leaf": {"value": 1}}}

    leaf = config["root"]["child"]["leaf"]
    assert leaf._path_from_root() == ["root", "child", "leaf"]

    leaf["value"] = 2
    config["unsaved_sibling"] = {"x": 1}
    leaf.save()

    reloaded = FileBackedDict.init_root(path)
    assert reloaded["root"]["child"]["leaf"]["value"] == 2
    assert "unsaved_sibling" not in reloaded


def test_module_load_save_round_trip_root(tmp_path):
    path = tmp_path / "config.yaml"
    cfg = FileBackedDict.init_root(path)
    cfg["database"] = {"host": "localhost", "port": 5432}
    cfg.save()

    reloaded = FileBackedDict.init_root(path)
    assert reloaded.to_dict() == {"database": {"host": "localhost", "port": 5432}}


def test_module_save_child_scope_only(tmp_path):
    path = tmp_path / "config.yaml"
    root = FileBackedDict.init_root(path)
    root["users"] = {"Fred": {"fave_recipe": {"name": "fried strings"}}}
    root.save()

    child = root["users"]["Fred"]["fave_recipe"]
    child["name"] = "tomato soup"
    root["users"]["Frankie"] = {"fave_recipe": {"name": "onion soup"}}

    child.save()

    reloaded = FileBackedDict.init_root(path)
    assert reloaded["users"]["Fred"]["fave_recipe"]["name"] == "tomato soup"
    assert "Frankie" not in reloaded["users"]
