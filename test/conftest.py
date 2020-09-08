import json

import pytest
from pkg_resources import Distribution

from src.spacy_paths import packages_dir

def find_spacy_installed(dir_name):
  if dir_name == packages_dir:
    return [
      Distribution(project_name='foo'),
      Distribution(project_name='spacy', version='3.0.0')
    ]
  else: return None

def find_spacy_not_installed(dir_name):
  if dir_name == packages_dir:
    return [Distribution(project_name='foo')]
  else: return None

@pytest.fixture()
def spacy_installed(mocker):
  mock_pkg_resources = mocker.patch('src.spacy.pkg_resources')
  mock_pkg_resources.find_distributions.side_effect = find_spacy_installed

@pytest.fixture()
def spacy_not_installed(mocker):
  mock_pkg_resources = mocker.patch('src.spacy.pkg_resources')
  mock_pkg_resources.find_distributions.side_effect = find_spacy_not_installed

@pytest.fixture()
def model_compat():
  with open('model_compat.json') as j:
    return SpacyModelManager(json.load(j))
