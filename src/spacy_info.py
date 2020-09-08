import fnmatch
import json
import logging
import os
import tempfile
import zipfile

from PyQt5.QtCore import QObject, pyqtSignal
from aqt import mw
from packaging import version
from packaging.version import parse

from .const import ADDON_NAME, EARLIEST_SPACY_VERSION, SPACY_PACKAGE_INFO_URL, SPACY_MODEL_REPO_URL
from .http_util import get
from .spacy_packages import installed_spacy_version
from .spacy_paths import (
  spacy_info_file,
  spacy_compatibility_file,
  model_info_path,
  spacy_models_etag_file,
  spacy_model_cache_dir,
  spacy_cache_dir,
  spacy_etag_file,
  info_cache_dir
)


logger = logging.getLogger(f'{ADDON_NAME}.{__name__}')


class SpacyInfoLoader(QObject):
  """
  Caches data about spacy and its packages. Calling load will start a background task to
  1. Make sure the cache directories are created.
  2. Download latest spacy package info from pypi
  3. Download latest spacy model info from spacy's model github repository.
  Because this can be an expensive operation, etags are used to determine if the cache is
  out of date.

  Progress updates are emitted through the status_updated signal and can be used to notify
  the user what steps are currently being executed.

  After the cache has been updated the loaded signal is fired containing a SpacyInfo instance.
  """
  status_updated = pyqtSignal(str)
  loaded = pyqtSignal(object)

  def __init__(self, parent=None):
    super(SpacyInfoLoader, self).__init__(parent)

  def load(self):
    """
    Downloads/Updates the spacy cache. This cache contains info about
    spacy and its models. On completion emits the loaded signal with an
    instance of SpacyInfo.
    """
    mw.taskman.run_in_background(
      self._update_cache,
      on_done=lambda f: self._on_loaded(f)
    )

  def _on_loaded(self, f):
    f.result()
    self.loaded.emit(create_spacy_info())

  def _update_cache(self):
    logger.info("Checking spacy info cache for updates.")

    self.status_updated.emit("Creating cache directories...")
    self._ensure_cache_created()
    self.status_updated.emit("Checking pypi for newer spacy package info...")
    self._update_spacy_package_info()
    self.status_updated.emit("Checking spacy models for updates...")
    self._update_spacy_model_package_info()

  def _ensure_cache_created(self):
    logger.debug("Creating info cache directory if missing.")
    self.status_updated.emit("Creating info cache directory if missing.")
    os.makedirs(info_cache_dir, exist_ok=True)

    logger.debug("Creating spacy info cache directory if missing.")
    self.status_updated.emit("Creating spacy info cache directory if missing.")
    os.makedirs(spacy_cache_dir, exist_ok=True)

    logger.debug("Creating spacy model info cache directory if missing.")
    self.status_updated.emit("Creating spacy model info cache directory if missing.")
    os.makedirs(spacy_model_cache_dir, exist_ok=True)

  def _update_spacy_package_info(self):
    logger.info("Checking for updated spacy info from pypi.")

    self._handle_spacy_info_response(get(
      SPACY_PACKAGE_INFO_URL,
      allow_redirects=True,
      headers={
        'Accept-Encoding': 'identity',
        'If-None-Match': f'"{SpacyInfoLoader._load_etag(spacy_etag_file)}"'
      }))

  def _update_spacy_model_package_info(self):
    logger.info("Checking for latest spacy model info.")
    self.status_updated.emit("Checking for latest spacy model info...")

    self._handle_model_info_response(get(
      SPACY_MODEL_REPO_URL,
      allow_redirects=True,
      stream=True,
      headers={
        'Accept': 'application/vnd.github.v3+json',
        'Accept-Encoding': 'identity',
        'If-None-Match': f'"{SpacyInfoLoader._load_etag(spacy_models_etag_file)}"'
      }))

  def _handle_spacy_info_response(self, response):
    if response.status_code == 200:
      logger.debug("Downloading latest spacy.json from pypi...")
      self.status_updated.emit("Downloading latest spacy.json from pypi...")
      with open(spacy_info_file, 'w') as f:
        logger.debug(f"Writing spacy info to {spacy_info_file}")
        f.write(response.text)

      self.status_updated.emit("Writing updated etag for spacy info...")
      with open(spacy_etag_file, 'w') as f:
        etag = response.headers['etag'].strip('\"')
        logger.debug(f"Writing updated etag {etag} to file {spacy_etag_file}.")
        f.write(etag)

    else:
      logger.debug(f"Spacy info is current.")
      self.status_updated.emit("Spacy info is current...")

  def _handle_model_info_response(self, response):
    if response.status_code == 200:
      logger.debug("Downloading latest model package info.")
      self.status_updated.emit("Downloading latest model package info...")

      with tempfile.TemporaryDirectory() as tmpdirname:
        zip_path = os.path.join(tmpdirname, 'spacy-models.zip')

        with open(zip_path, 'wb') as fd:
          logger.debug(f"Writing model zip file")
          for chunk in response.iter_content(chunk_size=1024):
            fd.write(chunk)

        logger.debug("Downloading latest model package info.")
        self.status_updated.emit("Extracting latest model package info...")

        with zipfile.ZipFile(zip_path, 'r') as zf:
          for member in zf.infolist():
            if member.filename[-1] == '/':
              continue
            elif fnmatch.fnmatch(member.filename, "**/meta/*"):
              member.filename = os.path.basename(member.filename)
              zf.extract(member, spacy_model_cache_dir)
            elif fnmatch.fnmatch(member.filename, "**/compatibility.json"):
              member.filename = os.path.basename(member.filename)
              zf.extract(member, spacy_cache_dir)

      self.status_updated.emit("Writing updated etag for model info.")
      with open(spacy_models_etag_file, 'w') as f:
        etag = response.headers['ETag'].strip('\"')
        logger.debug(f"Writing updated etag {etag} to file {spacy_etag_file}.")
        f.write(etag)

    else:
      logger.debug(f"Spacy model info is current.")
      self.status_updated.emit("Spacy model info is current.")

  @staticmethod
  def _load_etag(etag_path):
    if os.path.exists(etag_path):
      with open(etag_path, 'r') as reader:
        return reader.read().strip()
    else:
      return None


def create_spacy_info():
  with open(spacy_info_file) as spacy, open(spacy_compatibility_file) as models:
    return SpacyInfo(json.load(spacy), json.load(models))


class SpacyInfo:
  """
  Using the local cache of spacy and spacy model info, answers common questions about
  spacy.
  """

  def __init__(self, spacy_pypi_dict, model_compatibility):
    super(SpacyInfo, self).__init__()
    self.spacy_pypi_dict = spacy_pypi_dict
    self.model_compatibility = self._parse_model_compatibility(model_compatibility['spacy'])
    self.earliest = parse(EARLIEST_SPACY_VERSION)

  def spacy_versions(self, pre_release=False):
    """
    Returns a sorted list of Version for spacy releases.
    Versions start at 'earliest'.
    Versions only contain release versions unless pre_release=True
    """
    versions = map(version.parse, self.spacy_pypi_dict["releases"].keys())
    if not pre_release:
      versions = filter(lambda v: not v.is_prerelease, versions)

    versions = filter(lambda v: v > self.earliest, versions)
    versions = list(versions)
    versions.sort(reverse=True)

    return versions

  def model_names(self, pre_release=False):
    """
    Returns a list of spacy model names. If pre_release is False any model that only has
    pre-release version will be filtered out.
    """
    names = list(self.model_compatibility.keys())
    names.sort()
    return list(
      filter(
        lambda m: self._has_versions_available(m, pre_release), names))

  def is_model(self, name):
    """
    Given a name determine if it is a spacy model.
    """
    return name in self.model_compatibility

  def is_model_compatible(self, name, version):
    """
    Given a model name and model version determine if the model is compatible with the
    installed spacy version.
    """
    return installed_spacy_version() in self.compatible_spacy_versions(name, version)

  def compatible_spacy_versions(self, model_name, model_version):
    """
    Given a model name and a model version return a list of Version for spacy which
    are compatible.
    """
    versions = self.model_compatibility[model_name][model_version]
    return sorted(versions, reverse=True)

  def versions_for_model(self, model_name, pre_release=False):
    """
    Given a spacy model name return a list of all versions available for that name.
    """
    versions = self.model_compatibility[model_name].keys()

    if not pre_release:
      versions = filter(lambda v: not v.is_prerelease, versions)

    return sorted(versions, reverse=True)

  @staticmethod
  def _parse_model_compatibility(model_compatibility, earliest=parse('2.0.0')):
    """
      Parses the compatibility.json for spacy models into the following format.
      { model_name: { version1: {spacy_version1, spacy_version2} }
    """
    output = {}
    for (spacy_version, models) in model_compatibility.items():
      spacy_version = parse(spacy_version)
      if spacy_version < earliest:
        continue
      for (model_name, versions) in models.items():
        model_entry = output.get(model_name, {})
        for version in map(parse, versions):
          spacy_versions_entry = model_entry.get(version, set())
          model_entry[version] = spacy_versions_entry | {spacy_version}

        output[model_name] = model_entry
    return output

  @staticmethod
  def load_model_info(name, version):
    with open(model_info_path(name, version)) as f:
      return json.load(f)

  def _has_versions_available(self, model_name, pre_release=False):
    return len(self.versions_for_model(model_name, pre_release)) > 0
