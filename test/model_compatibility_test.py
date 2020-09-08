from packaging.version import parse

from src.spacy_info import SpacyInfo

def test_return_all_unique_model_names():
  model_compat = SpacyInfo({}, {'spacy': {
    "2.3.2": {"zh_core_web_sm": ["2.3.0"], "zh_core_web_md": ["2.3.0"]},
    "2.3.1": {"zh_core_web_sm": ["2.3.0"], "da_core_news_sm": ["2.3.0"]}
  }})

  assert \
    ['zh_core_web_sm', 'zh_core_web_md', 'da_core_news_sm'] == \
    model_compat.model_names()


def test_compat_spacy_versions():
  model_compat = SpacyInfo({}, {'spacy': {
    "2.3.2": {"zh_core_web_sm": ["2.3.0"], "zh_core_web_md": ["2.3.0"]},
    "2.3.1": {"zh_core_web_sm": ["2.3.0"], "da_core_news_sm": ["2.3.0"]},
    "2.2.0": {"zh_core_web_sm": ["2.2.9"], "da_core_news_sm": ["2.3.0"]}
  }})

  assert model_compat.compatible_spacy_versions("zh_core_web_sm", '2.3.0') == \
         [parse('2.3.2'), parse('2.3.1')]

def test_compat_spacy_versions_decreasing_order():
  model_compat = SpacyInfo({}, {'spacy': {
    "2.3.1": {"zh_core_web_sm": ["2.3.0"], "da_core_news_sm": ["2.3.0"]},
    "2.3.2": {"zh_core_web_sm": ["2.3.0"], "zh_core_web_md": ["2.3.0"]},
    "2.2.0": {"zh_core_web_sm": ["2.2.9"], "da_core_news_sm": ["2.3.0"]}
  }})

  assert model_compat.compatible_spacy_versions("zh_core_web_sm", '2.3.0') == \
         [parse('2.3.2'), parse('2.3.1')]

def test_model_versions():
  model_compat = SpacyInfo({}, {'spacy': {
    "2.3.2": {"zh_core_web_sm": ['2.3.2', '2.3.1', '2.3.0'], 'zh_core_web_md': ['2.3.0']},
    "2.3.1": {"zh_core_web_sm": ['2.3.0'], 'da_core_news_sm': ['2.3.0']},
    "2.2.0": {"zh_core_web_sm": ['2.2.9'], 'da_core_news_sm': ['2.3.0']}
  }})

  assert model_compat.versions_for_model('zh_core_web_sm', '2.3.2') == \
         [parse('2.3.2'), parse('2.3.1'), parse('2.3.0')]

def test_model_versions_decreasing_order():
  model_compat = SpacyInfo({}, {'spacy': {
    "2.3.2": {"zh_core_web_sm": ['2.3.0', '2.3.2', '2.3.1'], 'zh_core_web_md': ['2.3.0']},
    "2.3.1": {"zh_core_web_sm": ['2.3.0'], 'da_core_news_sm': ['2.3.0']},
    "2.2.0": {"zh_core_web_sm": ['2.2.9'], 'da_core_news_sm': ['2.3.0']}
  }})

  assert model_compat.versions_for_model('zh_core_web_sm', '2.3.2') == \
         [parse('2.3.2'), parse('2.3.1'), parse('2.3.0')]
