import os


current_dir = os.path.dirname(os.path.realpath(__file__))

vendor_dir = os.path.join(current_dir, '_vendor')
user_files = os.path.join(current_dir, 'user_files')
packages_dir = os.path.join(user_files, 'packages')
logging_config = os.path.join(current_dir, 'logging.conf')
log_file = os.path.join(user_files, 'anki_spacy.log')

resources_dir = os.path.join(current_dir, "ui/resources")

info_cache_dir = os.path.join(user_files, '_cache')
spacy_cache_dir = os.path.join(info_cache_dir, 'spacy')
spacy_model_cache_dir = os.path.join(spacy_cache_dir, 'models')
spacy_compatibility_file = os.path.join(spacy_cache_dir, 'compatibility.json')
spacy_info_file = os.path.join(spacy_cache_dir, 'spacy.json')

spacy_etag_file = os.path.join(spacy_cache_dir, 'spacy-etag')
spacy_models_etag_file = os.path.join(spacy_cache_dir, 'spacy-models-etag')


def model_info_path(name, version):
  return os.path.join(spacy_model_cache_dir, f'{name}-{str(version)}.json')
