from src import ModelPackage


def test_model():
  model = ModelPackage("some_model", "install_dir")

  assert \
    model.requirement('1.0.0') == \
    "https://github.com/explosion/spacy-models/releases/download/some_model-1.0.0/some_model-1.0.0.tar.gz"

