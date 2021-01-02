import logging
import os

from anki import hooks

from .const import ADDON_NAME
from .spacy_packages import (
  installed_spacy_version,
  installed_model_packages,
  filter_compatible,
  create_spacy_package, SpacyPackage, ModelPackage
)

logger = logging.getLogger(f'{ADDON_NAME}.{__name__}')


spacy_hook_prefix = 'AnkiSpacy'
spacy_installed_hook_name = f'{spacy_hook_prefix}.spacyInstalled'
spacy_uninstalled_hook_name = f'{spacy_hook_prefix}.spacyUninstalled'
model_available_hook_name = f'{spacy_hook_prefix}.modelAvailable'
model_unavailable_hook_name = f'{spacy_hook_prefix}.modelUnavailable'


def send_current_state_hooks(spacy_info):
  if installed_spacy_version():
    spacy_installed_hooks(spacy_info, create_spacy_package(spacy_info))


def spacy_installed_hooks(spacy_info, spacy_package):
  _send_spacy_installed(spacy_package)
  _send_available_models(spacy_info, spacy_package)


def spacy_uninstalled_hooks(spacy_info, spacy_package, version):
  _send_spacy_uninstalled(spacy_package)
  _send_unavailable_models(spacy_info, version)


def model_installed_hooks(spacy_info, model):
  _model_changed_hooks(spacy_info, model, model.installed, model_available_hook_name)


def model_removed_hooks(spacy_info, model, uninstalled_version):
  _model_changed_hooks(spacy_info, model, uninstalled_version, model_unavailable_hook_name)


def _send_spacy_installed(spacy_package):
  payload = _create_payload(spacy_package)
  logger.debug(f"Sending hook {spacy_installed_hook_name} with payload {payload}")
  hooks.runHook(spacy_installed_hook_name, payload)


def _send_spacy_uninstalled(spacy_package):
  payload = _create_payload(spacy_package)
  logger.debug(f"Sending hook {spacy_uninstalled_hook_name} with payload {payload}")
  hooks.runHook(spacy_uninstalled_hook_name, payload)


def _send_available_models(spacy_info, spacy_package):
  _model_availability_changed(spacy_info, spacy_package.installed, model_available_hook_name)


def _send_unavailable_models(spacy_info, version):
  _model_availability_changed(spacy_info, version, model_unavailable_hook_name)


def _model_availability_changed(spacy_info, version, hook_name):
  installed_models = installed_model_packages(spacy_info)
  compatible_models = filter_compatible(spacy_info, installed_models, version)
  for model in compatible_models:
    payload = _create_payload(model)
    logger.debug(f"Sending hook {hook_name} with payload {payload}")
    hooks.runHook(hook_name, payload)


def _model_changed_hooks(spacy_info, model, model_version, hook_name):
  if spacy_version := installed_spacy_version():
    if spacy_version in spacy_info.compatible_spacy_versions(model.name, model_version):
      payload = _create_payload(model)
      logger.debug(f"Sending hook {hook_name}m with payload {payload}")
      hooks.runHook(hook_name, payload)


def _create_payload(package):
  path = os.path.join(package.install_dir, package.name)
  if type(package) == ModelPackage:
    path = os.path.join(path, f"{package.name}-{package.installed}")

  return {
    'name': package.name,
    'version': package.installed,
    'path': path
  }
