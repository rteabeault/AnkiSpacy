import os

from PyQt5.QtCore import QAbstractListModel, Qt
from PyQt5.QtGui import QIcon

from ..spacy_packages import create_spacy_package, create_model_packages
from ..spacy_paths import resources_dir


class SpacyItemListModel(QAbstractListModel):
  PackageRole = Qt.UserRole + 1000
  SpacyInfoRole = Qt.UserRole + 1001

  def __init__(self, spacy_info, *args, **kwargs):
    super(SpacyItemListModel, self).__init__(*args, **kwargs)
    self.spacy_info = spacy_info
    self.packages = []
    self.rebuild_model()

  def rebuild_model(self):
    self.beginResetModel()
    self.packages = []
    spacy = create_spacy_package(self.spacy_info)
    spacy_models = create_model_packages(self.spacy_info)

    self.packages.append(spacy)
    self.packages.extend(spacy_models)
    self.endResetModel()

  def index_for_package(self, package):
    i = next(i for i, p in enumerate(self.packages) if p.name == package.name)
    return self.createIndex(i, 0)

  def data(self, index, role=None):
    if not index.isValid():
      return None
    if role == Qt.DisplayRole:
      return self.packages[index.row()].name
    elif role == self.PackageRole:
      return self.packages[index.row()]
    elif role == Qt.DecorationRole:
      if index.row() == 0:
        return QIcon(os.path.join(resources_dir, "spacy_icon.png"))
      else:
        return None
    elif role == self.SpacyInfoRole:
      return self.spacy_info
    else:
      return None

  def rowCount(self, parent=None, *args, **kwargs):
    return len(self.packages)
