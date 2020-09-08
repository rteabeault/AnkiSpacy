import logging
import os
import sys

from .const import ADDON_NAME
from .spacy_paths import packages_dir


logger = logging.getLogger(f'{ADDON_NAME}.{__name__}')


def load_packages():
  """
  Add packages_dir to the sys.path
  """
  if os.path.exists(packages_dir) and packages_dir not in sys.path:
    logger.debug(f"Adding {packages_dir} to sys.path")
    sys.path.append(packages_dir)


def unload_packages():
  """
  Unload packages in packages_dir.
  """
  logger.debug(f"Unloading packages from {packages_dir}")

  if packages_dir in sys.path:
    for name in list(sys.modules):
      module = sys.modules[name]
      if hasattr(module, '__file__') and \
        module.__file__ and \
        os.path.commonprefix([module.__file__, packages_dir]) == packages_dir:

        logger.debug(f"Removing module {name} from {packages_dir}")

        del sys.modules[name]
        del module

    logger.debug(f"Removing {packages_dir} from sys.path")
    sys.path.remove(packages_dir)


def reload_packages():
  logger.debug(f"Reloading packages from {packages_dir}")
  unload_packages()
  load_packages()
