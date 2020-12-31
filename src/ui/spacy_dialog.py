import logging
import os

from PyQt5.QtCore import Qt, QItemSelectionModel, pyqtSignal
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import (
  QDialog,
  QLabel,
  QVBoxLayout,
  QDialogButtonBox,
  QSplitter,
  QDataWidgetMapper,
  QItemDelegate,
  QWidget,
  QHBoxLayout)
from aqt import mw
from packaging.version import parse

from ..const import ADDON_NAME
from .package_info import PackageInfo
from .progress_indicator import QProgressIndicator
from .spacy_colors import spacy_light, spacy_dark, spacy_medium
from .spacy_list import SpacyListView
from .spacy_model import SpacyItemListModel
from .stdout_progress import StdoutProgressText
from ..fs_util import remove_path
from ..installer import PipInstaller
from ..spacy_paths import resources_dir

logger = logging.getLogger(f'{ADDON_NAME}.{__name__}')

class SpacyDialog(QDialog):
  package_installed = pyqtSignal(object)
  package_uninstalled = pyqtSignal(object, object)

  style = f"""
      QDialog {{ background-image: url({resources_dir}/pattern_blue.jpg) }}
      QPushButton {{
        background-color: {spacy_dark.name()};
        min-width: 80px;
      }}
      QPushButton:enabled {{
          color: {spacy_light.name()};
          background-color: {spacy_medium.name()};
          border: 1px solid {spacy_medium.name()};
      }}
      QPushButton:disabled {{
          color: {spacy_medium.name()};
          background-color: {spacy_dark.name()};
          border: 1px solid {spacy_medium.name()};
      }}
      QPushButton:pressed {{
          background-color: {spacy_dark.name()};
      }}
      QLabel {{
        color: {spacy_light.name()};
      }}
      QScrollBar:vertical {{
        border: none;
        background: {spacy_dark.name()};
        width: 10px;
      }}
      QScrollBar:handle:vertical {{
        background: {spacy_medium.name()};
        min-height: 0px;
      }}
      QScrollBar:add-line:vertical {{
        height: 0 px;
        subcontrol-position: bottom;
        subcontrol-origin: margin;      
      }}
      QScrollBar:sub-line:vertical {{
        height: 0 px;
        subcontrol-position: top;
        subcontrol-origin: margin;
      }}
    """

  def __init__(self, parent=None):
    super(SpacyDialog, self).__init__(parent)
    self.spacy_info = None
    self.model = QStandardItemModel()
    self.setStyleSheet(self.style)
    self.setWindowTitle("Spacy Package Manager")
    self.resize(1024, 768)

    self.layout = QVBoxLayout(self)

    self.spacy_header = QLabel(self)
    self.spacy_header.setTextFormat(Qt.MarkdownText)
    self.spacy_header.setWordWrap(True)
    header_md = os.path.join(os.path.dirname(os.path.realpath(__file__)),
      'resources/SpacyHeader.md')
    self.spacy_header.setText(open(header_md).read())
    self.layout.addWidget(self.spacy_header)

    self.management_splitter = QSplitter(self)
    self.spacy_list_view = SpacyListView(self)
    self.management_splitter.addWidget(self.spacy_list_view)

    self.package_info = PackageInfo()
    self.management_splitter.addWidget(self.package_info)
    self.layout.addWidget(self.management_splitter)
    self.layout.setStretch(1, 2)

    self.progress_text = StdoutProgressText(self)
    self.layout.addWidget(self.progress_text)

    self.buttonBox = QDialogButtonBox(self)
    self.buttonBox.setOrientation(Qt.Horizontal)
    self.buttonBox.setStandardButtons(QDialogButtonBox.Close)
    self.buttonBox.button(QDialogButtonBox.Close).setFlat(True)

    self.buttonBox.rejected.connect(self.reject)
    self.layout.addWidget(self.buttonBox)

    self.mapper = QDataWidgetMapper()

    self.package_info.install_package.connect(self.install_package)
    self.package_info.uninstall_package.connect(self.uninstall_package)

    self.loading_overlay = LoadingOverlay(self)
    self.loading_overlay.set_message("Loading...")
    self.loading_overlay.enable_overlay()

  def update_overlay_text(self, text):
    self.loading_overlay.set_message(text)

  def set_spacy_info(self, spacy_info):
    self.spacy_info = spacy_info
    self.model = SpacyItemListModel(self.spacy_info)
    self.spacy_list_view.setModel(self.model)
    self.spacy_list_view.selectionModel().currentChanged.connect(self.selection_changed)
    self.mapper.setModel(self.model)
    self.mapper.setItemDelegate(SpacyDialogMapperDelegate())
    self.mapper.addMapping(self.package_info, 0)
    self.mapper.toFirst()
    self.loading_overlay.disable_overlay()

  def selection_changed(self, index):
    self.mapper.setCurrentIndex(index.row())

  def install_package(self, package, version):
    self.progress_text.clear_text()
    self.uninstall_package(package)

    index = self.model.index_for_package(package)
    package = self.model.data(index, SpacyItemListModel.PackageRole)

    installer = PipInstaller(package, version)
    installer.signals.install_progress.connect(self.progress_text.append_text)

    self.setDisabled(True)
    mw.taskman.run_in_background(
      installer.run,
      on_done=lambda f: self.on_install_complete(f, package, version)
    )

  def on_install_complete(self, future, package, version):
    future.result()
    self.setDisabled(False)
    package.installed = parse(version)
    self.model.rebuild_model()
    self._set_current_index(self.model.index_for_package(package))
    self.package_installed.emit(package)

  def uninstall_package(self, package):
    if package.installed:
      self.setDisabled(True)
      self.progress_text.clear_text()
      self.progress_text.println(f'Uninstall {package.name}...')

      for path in package.uninstall_paths():
        remove_path(path)

      self.progress_text.println(f'{package.name} uninstall complete.')

      self.model.rebuild_model()
      self._set_current_index(self.model.index_for_package(package))

      uninstalled_version = package.installed
      package.installed = None
      self.setDisabled(False)
      self.package_uninstalled.emit(package, uninstalled_version)

  def _set_current_index(self, index):
    self.spacy_list_view.selectionModel().setCurrentIndex(index, QItemSelectionModel.ClearAndSelect)
    self.mapper.setCurrentIndex(index.row())


class SpacyDialogMapperDelegate(QItemDelegate):
  """
  Used as the delegate to map model data to the PackageInfo Widget.
  """

  def __init__(self, parent=None):
    super(SpacyDialogMapperDelegate, self).__init__(parent)

  def setModelData(self, editor, model, index) -> None:
    super().setModelData(editor, model, index)

  def setEditorData(self, editor, index):
    package = index.data(SpacyItemListModel.PackageRole)
    editor.set_package(package)


class LoadingOverlay(QWidget):
  style = """color:white;
             font-size:16pt;
             background-color:rgba(0,0,0,200);
             border: 1px solid rgba(0,0,0,200);
             border-radius:4px;"""

  def __init__(self, parent):
    self.overlay = QWidget(parent)
    self.overlay.hide()
    self.overlay.setStyleSheet('background-color: rgba(0,0,0,200)')

    super(LoadingOverlay, self).__init__(parent)

    self.setStyleSheet(self.style)
    self.layout = QHBoxLayout(self)
    self.layout.setAlignment(Qt.AlignCenter)

    self.busy = QProgressIndicator(self, "white")
    self.layout.addWidget(self.busy)

    self.label = QLabel(self)
    self.layout.addWidget(self.label)

  def enable_overlay(self):
    self.overlay.resize(self.parent().size())
    self.resize(self.parent().size())
    self.busy.busy()
    self.overlay.show()

  def disable_overlay(self):
    self.hide()
    self.overlay.hide()
    self.busy.stopAnimation()

  def set_message(self, message):
    if message:
      self.label.setText(message)
    else:
      self.label.hide()
