"""YAML/TOML wrapper that enables edits, reloads, and manages derived params."""

import toml
from ruamel.yaml import YAML
import logging
from pathlib import Path
from typing import Union, List


class Config:

    def __init__(self, filepath: Union[str, None] = None,
                 config_template: Union[dict, None] = None,
                 create: bool = False):
        """Load an existing (TOML or YAML) config
           or create one from the specified template.

            :param filepath: location of the config if we are
                loading one from file. Default location to save to. Optional.
            :param config_template: dict with the same key structure as the
                config file. Optional. Only required if `create` is True.
            :param create: if True, create a config object from the specified
                `config_template`.
            :note: comments and file order are not preserved for toml files but
                *are* preserved in yaml files. This is a quirk of the libraries
                used to read/write them.
        """
        self.cfg = None  # The actual type will vary but it can be treated
                         # as a dict.
        self.handlers = {"yaml": YAML(), "toml": toml}
        self.path = Path(filepath) if filepath else None
        self.template = config_template
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # User specified existing config.
        if self.path and self.path.exists():
            self.log.info(f"Loading: {self.path.resolve()}")
            self.load(self.path)
        # User specified existing config but it does not exist.
        elif self.path and not self.path.exists() and not create:
            raise ValueError(f"Configuration file at "
                             f"{str(self.path.absolute())} does not exist.")
        # User specified create new config at specified path.
        elif self.path and config_template and create:
            self.log.info(f"Creating: {self.path.resolve()} from template.")
            self.load_from_template()
        # No config specified; not creating.
        else:
            raise ValueError("No configuration was specified.")
        self.doc_name = self.path.name

    def load_from_template(self, config_template: dict = None):
        """Create a config from a template if one was specified on __init__.

        .. code-block:: python

            cfg.load_from_template() # Optional dict may be passed in if one was
                                     # not specified in the init.
            cfg.save("./config.toml")  # Save the config made from the template.

        """
        if config_template:
            self.template = config_template
        if self.template is None:
            raise ValueError("Error: No template was specified from which to "
                             "create the configuration.")
        # This will destroy anything that we loaded.
        self.cfg = toml.loads(toml.dumps(self.template))

    def derive_template(self, filepath: Path = None):
        """Generate a template from the loaded config containing a YAML
           of identical field structure with unpopulated values."""
        raise NotImplementedError("This function has not been implemented.")

    def load(self, filepath: Path = None):
        """Load a config from file specified in filepath or __init__."""
        if filepath:
            self.path = filepath
        if not (self.path.is_file() and self.path.exists()):
            raise AssertionError(f"Config does not exist at provided "
                                 f"filepath: {self.path}.")
        file_type = self.path.name.split(".")[-1].lower()
        cfg_handler = self.handlers.get(file_type, None)
        if cfg_handler is None:
            raise RuntimeError("Config file extension not recognized."
                               "File must have a *.yaml or *.toml suffix.")
        with open(filepath, 'r') as cfg_file:
            self.cfg = cfg_handler.load(cfg_file)
        self.doc_name = self.path.name
        if not self.template:
            return
        # TODO: template comparison. possibly with deepdiff.
        #  https://github.com/seperman/deepdiff

    def reload(self):
        """Reload the config from the file we loaded the config from.

        Take all the new changes.
        """
        # This will error out if the config never existed in the first place.
        self.load(self.path)

    def save(self, filepath: str = None, overwrite: bool = True):
        """Save config to specified file, or overwrite if no file specified.

        :param filepath: can be a path to a folder or a file.
            If folder, we use the original filename (or default filename
            if filename never specified).
            If file, we use the specified filename.
            If no path specified, we overwrite unless flagged not to do so.
            File extension (yaml or toml) dictates what type of file is
            saved.
        :param overwrite: bool to indicate if we overwrite an existing file.
            Defaults to True so that we can save() over a previous file.
        """
        # if filepath unspecified, overwrite the original.
        write_path = Path(filepath) if filepath else self.path
        # if file name is unspecified, use the original.
        if write_path.is_dir():
            write_path = write_path / self.doc_name
        file_type = write_path.name.split(".")[-1].lower()
        cfg_handler = self.handlers.get(file_type, None)
        if cfg_handler is None:
            raise ValueError("Config file extension not recognized."
                               "File must have a *.yaml or *.toml suffix.")
        with write_path.open("w") as f:
            cfg_handler.dump(self.cfg, f)

    def validate(self):
        """Confirm that config fields have values that are in the right ranges.
        """
        raise NotImplementedError("Must be implemented by the child class.")
