import distutils
import logging
import logging.config
import logging.handlers
import os
import sys
from logging.handlers import RotatingFileHandler

import pkg_resources
from PyQt5.QtWidgets import QAction
from aqt import mw, gui_hooks

from .const import ADDON_NAME
from .fs_util import ensureDirExists
from .hooks import (
  send_current_state_hooks,
  spacy_installed_hooks,
  model_installed_hooks,
  spacy_uninstalled_hooks,
  model_removed_hooks)
from .package_util import load_packages, reload_packages
from .spacy_info import SpacyInfoLoader
from .spacy_packages import SpacyPackage, ModelPackage
from .spacy_paths import vendor_dir, log_file, user_files


logger = logging.getLogger(ADDON_NAME)


def init():
  init_user_files()
  init_logging()
  init_vendor()
  load_packages()
  init_menu()
  logger.info("AnkiSpacy init complete.")


def init_user_files():
  ensureDirExists(user_files)


def init_logging():
  config = mw.addonManager.getConfig(__name__)
  level = config['logging']['level']

  stdout_handler = logging.StreamHandler(sys.stdout)
  file_handler = RotatingFileHandler(log_file, maxBytes=2000000, backupCount=1, delay=True)

  formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(filename)s:%(funcName)s:%(lineno)s | %(message)s')
  file_handler.setFormatter(formatter)
  stdout_handler.setFormatter(formatter)

  logger.addHandler(file_handler)
  logger.addHandler(stdout_handler)

  logger.setLevel(level)

def init_menu():
  from .ui.spacy_dialog import SpacyDialog
  dialog = SpacyDialog(mw)

  spacy_info_loader = SpacyInfoLoader()
  spacy_info_loader.status_updated.connect(dialog.update_overlay_text)
  spacy_info_loader.loaded.connect(lambda spacy_info: _on_spacy_info_loaded(spacy_info, dialog))
  spacy_info_loader.load()

  action = QAction("Manage SpaCy...", mw)
  action.triggered.connect(lambda: dialog.exec_())
  mw.form.menuTools.addAction(action)

def init_vendor():
  logger.debug(f'Adding {vendor_dir} to sys.path')
  if vendor_dir not in sys.path:
    sys.path.append(vendor_dir)
    pkg_resources.working_set.add_entry(vendor_dir)

  distutils.__path__.append(os.path.join(vendor_dir, "distutils"))


def _on_spacy_info_loaded(spacy_info, dialog):
  dialog.set_spacy_info(spacy_info)
  dialog.package_installed.connect(
    lambda package: _on_package_installed(spacy_info, package))
  dialog.package_uninstalled.connect(
    lambda package, uninstalled_version:
    _on_package_uninstalled(spacy_info, package, uninstalled_version))

  send_current_state_hooks(spacy_info)


def _on_package_installed(spacy_info, package):
  reload_packages()
  if type(package) is SpacyPackage:
    spacy_installed_hooks(spacy_info, package)
  elif type(package) is ModelPackage:
    model_installed_hooks(spacy_info, package)


def _on_package_uninstalled(spacy_info, package, version):
  reload_packages()
  if type(package) is SpacyPackage:
    spacy_uninstalled_hooks(spacy_info, package, version)
  elif type(package) is ModelPackage:
    model_removed_hooks(spacy_info, package, version)


gui_hooks.main_window_did_init.append(init)
