
from typing import List, Callable, Optional
import os.path
import sys
import yaml


# signature of progress callback function
# parameters are(current, total, tag)
ProgressCallback = Callable[[int, int, Optional[str]], None]


class SrcPath:
    """
    Handles file paths within the project source.
    """
    # Path to the project root, which is 'oec_sync' folder
    SRC_ROOT = os.path.dirname(os.path.dirname(__file__))

    MODULES = {
        'sync',
        'tests',
    }

    @staticmethod
    def abs(*parts: List[str]) -> str:
        """
        Get the absolute from a path relative to project root.
        :param parts: path from project root i.e. 'sync_config', 'NASA.yml'
        :return: absolute path.
        """
        return os.path.join(SrcPath.SRC_ROOT, *parts)


class InitError(Exception):
    """
    Initialization Error.
    """
    pass


class Helper:
    """
    routines commonly used or required by unrelated modules
    """
    @staticmethod
    def read_conf(config_file):
        """
        Load the config_file
        :param config_file:
        :return: configuration as dict
        """
        # load configuration
        config = None
        with open(config_file) as f:
            config = yaml.load(f)
        if not config:
            raise InitError(
                    "failed to read config file: " + config_file)
        return config


# add the project module paths into environment variables
for path in SrcPath.MODULES:
    module_path = os.path.normpath(SrcPath.abs(path))
    try:
        sys.path.index(module_path)
    except ValueError:
        sys.path.append(module_path)


if __name__ == "__main__":
    print(SrcPath.abs('sync_config', 'NASA.yml'))
    print(SrcPath.abs('config.yml'))
