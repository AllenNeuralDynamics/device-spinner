# device-spinner
<!--
[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
[![semantic-release: angular](https://img.shields.io/badge/semantic--release-angular-e10079?logo=semantic-release)](https://github.com/semantic-release/semantic-release)
![Interrogate](https://img.shields.io/badge/interrogate-100.0%25-brightgreen)
-->
![Python](https://img.shields.io/badge/python->=3.8-blue?logo=python)


Create complex Python objects from dicts and yaml files.
This library implements the factory design pattern to create objects from a specification file.

## Why do this?
Building complex objects from a yaml file:
* simplifies simulation, where some objects can be mocked or stubbed out with a specific config.
* produces a flat view of complex hierarchical objects that take other objects as input (dependency injection).
* encourages modular, hierarchical design.

 
## Installation
To use the software, in the root directory, run
```bash
pip install -e .
```

To develop the code, run
```bash
pip install -e .[dev]
```
which will install extra dependencies for linting.

## Quickstart
To create an object from a yaml file, annotate it like this:
```yaml
devices:
    my_list:
        module: builtins
        class: dict
        kwds:
          Peach: 10,
          Mario: 5,
          Samus: 12
```
Then, in Python
```python
import yaml
from pathlib import Path

cfg_file = Path("/path/to/yaml/cfg.yaml")
cfg_content = cfg_file.open("r").read()
device_specs = yaml.safe_load(cfg_content)
devices = factory.create_devices_from_specs(device_specs["devices"])
```

## Dependency Injection
Sometimes, you need to pass an object instance into another objects instance's `__init__` (aka: [dependency injection](https://en.wikipedia.org/wiki/Dependency_injection)).
`DeviceSpinner` handles this by matching instance names.
Let's say we have a robot that requires an arm and a leg.
```python
# robot_parts.py

class Arm:
    pass

class Leg:
    pass
```

```python
# robots.py

class JumpingRobot
    def __init__(arm: Arm, leg: Leg):
        self.arm = arm
        self.leg = leg
```

In the yaml file, under `my_robot` `kwds`, we pass in the instance names
as they are named in the parent dict (`devices`).
When `DeviceSpinner` sees these names that match other object intances in the
parent dictionay, it will first build these dependencies, and then pass them in
as parameters.

```yaml
devices:
    my_robot:
        module: robot_lib.robots
        class: JumpingRobot
        kwds:
            arm: my_arm
            leg: my_leg
    my_arm:
        module: robot_lib.robot_parts
        class: Arm
    my_leg:
        module: robot_lib.robot_parts
        class: Leg

```

This works for `*args` and `**kwds` also.

### Skipping Parameters
Sometimes you don't want the above behavior, and you want to treat strings as strings.
To do so, mark them with the `skip_args` or `skip_kwds` field.

### Syntactic Sugar
By default, `DeviceSpinner` knows not to insert an instance of itself into itself during `__init__`.
So if you have have a yaml like this:
```yaml
devices:
    my_robot:
        module: robot_lib.robots
        class: TurtleBot
        kwds:
            name: my_robot
```
`DeviceSpinner` will **not** try to insert the `TurtleBot` instance into itself--even though the `name` parameter matches the outer name of the instance.


## Gotchas
This library has a workaround for creating `list`s that require dependency injection.
Here's an example that doesn't do dependency injection:

```yaml
devices
    my_legs:
        module: builtins
        class: list
        args:
        -   - left_leg  # <-- treated as a string!
            - right_leg # <-- treated as a string!
    left_leg:
        module: robot_lib.robot_parts
        class: Leg
    right_leg:
        module: robot_lib.robot_parts
        class: Leg

```

The reason for this is because the `list` constructor takes an iterable, (usually a tuple).

The fix is a custom factory function from this library that accepts any number
of arguments (i.e: `*args`) and returns a list instance.

```yaml
devices
    my_legs:
        module: device_spinner.factory_utils
        factory: to_list  # returns a list insance
        args:
        - left_leg  # <-- will be replaced by the object instance of the same name
        - right_leg # <-- will be replaced by the object instance of the same name
    left_leg:
        module: robot_lib.robot_parts
        class: Leg
    right_leg:
        module: robot_lib.robot_parts
        class: Leg

```


## Contributing

### Pull requests

For internal members, please create a branch. For external members, please fork the repository and open a pull request from the fork. We'll primarily use [Angular](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit) style for commit messages. Roughly, they should follow the pattern:
```text
<type>(<scope>): <short summary>
```

where scope (optional) describes the packages affected by the code changes and type (mandatory) is one of:

- **build**: Changes that affect build tools or external dependencies (example scopes: pyproject.toml, setup.py)
- **ci**: Changes to our CI configuration files and scripts (examples: .github/workflows/ci.yml)
- **docs**: Documentation only changes
- **feat**: A new feature
- **fix**: A bugfix
- **perf**: A code change that improves performance
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **test**: Adding missing tests or correcting existing tests

### Semantic Release

The table below, from [semantic release](https://github.com/semantic-release/semantic-release), shows which commit message gets you which release type when `semantic-release` runs (using the default configuration):

| Commit message                                                                                                                                                                                   | Release type                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| `fix(pencil): stop graphite breaking when too much pressure applied`                                                                                                                             | ~~Patch~~ Fix Release, Default release                                                                          |
| `feat(pencil): add 'graphiteWidth' option`                                                                                                                                                       | ~~Minor~~ Feature Release                                                                                       |
| `perf(pencil): remove graphiteWidth option`<br><br>`BREAKING CHANGE: The graphiteWidth option has been removed.`<br>`The default graphite width of 10mm is always used for performance reasons.` | ~~Major~~ Breaking Release <br /> (Note that the `BREAKING CHANGE: ` token must be in the footer of the commit) |

### Documentation
To generate the rst files source files for documentation, run
```bash
sphinx-apidoc -o doc_template/source/ src 
```
Then to create the documentation HTML files, run
```bash
sphinx-build -b html doc_template/source/ doc_template/build/html
```
More info on sphinx installation can be found [here](https://www.sphinx-doc.org/en/master/usage/installation.html).
