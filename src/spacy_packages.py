import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional

import pkg_resources
from packaging.version import parse, Version

from .lang_util import code_to_native
from .spacy_paths import packages_dir


@dataclass(eq=True)
class PipPackage:
  name: str
  install_dir: str = None
  installed: Version = None
  versions: List[Version] = None
  details: Dict[str, str] = None
  exclude_deps: List[str] = None

  def display_name(self):
    return self.name

  def updates(self) -> Optional[List[Version]]:
    """
    All available versions newer than the installed version.
    It the installed version is None then None is returned
    """
    if not self.installed:
      return None
    else:
      return list(
        filter(lambda v: v > self.installed, self.versions)
      )

  def updates_available(self) -> bool:
    return True if self.updates() else False

  def requirement(self, version):
    return f"{self.name}=={version}"

  def uninstall_paths(self):
    return [
      f.path for f in os.scandir(self.install_dir) if f.is_dir() and f.name.startswith(self.name)
    ]

  def detail_dict(self):
    info = self.details.get('info', {})
    return {
      'Author': info['author'],
      'Email': info['author_email'],
      'Description': 'spaCy is a free, open-source library for advanced Natural Language '
                     'Processing (NLP) in Python.'
    }


@dataclass(eq=True)
class SpacyPackage(PipPackage):
  name: str = "spacy"
  install_dir: str = packages_dir


@dataclass(eq=True)
class ModelPackage(PipPackage):
  github_url = "https://github.com/explosion/spacy-models/releases/download"
  install_dir = packages_dir

  lang_code: str = field(init=False)
  lang_name: str = field(init=False)
  type: str = field(init=False)
  genre: str = field(init=False)
  size: str = field(init=False)

  def __post_init__(self):
    self.lang_code = self.details['lang']
    if self.lang_code == 'xx':
      self.lang_name = 'Multi-language'
    else:
      self.lang_name = code_to_native.get(self.lang_code)

  def display_name(self):
    return f"{self.lang_name} - {self.name}"

  def requirement(self, version):
    return f"{self.github_url}/{self.name}-{version}/{self.name}-{version}.tar.gz"

  def detail_dict(self):
    return {
      'Language': code_to_native[self.details['lang']],
      'Description': self.details['description'],
      'Author': self.details['author'],
      'Email': self.details['email'],
      'Download Size': self.details['size']
      # 'Notes': self.details['notes'],
    }


def distribution(path, name):
  for dist in distributions(path):
    if dist.project_name == name:
      return dist
  return None


def distributions(path):
  return list(pkg_resources.find_distributions(path))


def installed_spacy_version():
  if dist := distribution(packages_dir, 'spacy'):
    return parse(dist.version)
  else:
    return None


def installed_model_versions(spacy_info):
  models = {}
  for dist in distributions(packages_dir):
    underscored_name = dist.project_name.replace('-', '_')
    if spacy_info.is_model(underscored_name):
      models[underscored_name] = parse(dist.version)

  return models


def create_spacy_package(spacy_info, pre_release=False):
  return SpacyPackage(
    installed=installed_spacy_version(),
    versions=spacy_info.spacy_versions(pre_release),
    details=spacy_info.spacy_pypi_dict,
  )


def create_model_packages(spacy_info, pre_release=False):
  installed_models = installed_model_versions(spacy_info)
  model_names = spacy_info.model_names(pre_release)
  return _create_model_packages(spacy_info, model_names, installed_models)


def installed_model_packages(spacy_info):
  installed_models = installed_model_versions(spacy_info)
  installed_names = installed_models.keys()
  return _create_model_packages(spacy_info, installed_names, installed_models)


def filter_compatible(spacy_info, model_packages, spacy_version):
  return [
    model for model in model_packages
    if spacy_version in spacy_info.compatible_spacy_versions(model.name, model.installed)]


def _create_model_packages(spacy_info, model_names, installed_models, pre_release=False):
  models = []
  for model_name in model_names:
    versions = spacy_info.versions_for_model(model_name, pre_release)
    models.append(ModelPackage(
      name=model_name,
      install_dir=packages_dir,
      installed=installed_models.get(model_name, None),
      versions=versions,
      details=spacy_info.load_model_info(model_name, versions[0]),
      exclude_deps=['spacy']
    ))

  return models
