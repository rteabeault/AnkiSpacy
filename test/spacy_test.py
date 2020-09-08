from packaging.version import parse

from src.spacy_packages import ModelPackage, create_spacy_package
from src.spacy_packages import installed_spacy_version

def model(name, lang, installed=None, versions=None, details=None):
  return ModelPackage(
    name=name,
    lang=lang,
    installed=installed,
    versions=list(map(parse, versions)),
    details=details
  )

def test_installed_spacy_version(spacy_installed):
  assert installed_spacy_version() == parse('3.0.0')


def test_installed_spacy_version_not_installed(spacy_not_installed):
  assert installed_spacy_version() is None


def test_create_models_with_none_installed_and_no_spacy_installed(model_compat):
  m = models(model_compat, {}, None)
  assert m[0] == model('zh_core_web_sm', 'Chinese', None, ['2.3.1', '2.3.0'])

def test_models_for_spacy_version(model_compat):
  m = models(model_compat, {}, '2.3.1')
  assert m[0] == model('zh_core_web_sm', 'Chinese', None, ['2.3.1', '2.3.0'])
  assert m[1] == model('da_core_news_sm', 'Danish', None, ['2.3.0'])
  assert m[2] == model('nl_core_news_sm', 'Dutch', None, ['2.3.0'])
  assert m[3] == model('en_core_web_sm', 'English', None, ['2.3.1', '2.3.0'])
  assert m[4] == model('ja_core_news_sm', 'Japanese', None, [])

def test_create_spacy_package():
  spacy = create_spacy_package(parse('3.0.0'), [parse('2.3.2'), parse('2.3.1')])
  assert 'spaCy' == spacy.name
  assert parse('3.0.0') == spacy.installed
  assert [parse('2.3.2'), parse('2.3.1')] == spacy.versions
