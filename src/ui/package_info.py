from PyQt5.QtCore import pyqtSlot, Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
  QWidget,
  QLabel,
  QVBoxLayout,
  QComboBox,
  QPushButton,
  QFrame,
  QGridLayout,
  QLineEdit,
  QScrollArea,
  QLayout)

from .spacy_colors import spacy_dark, spacy_light, spacy_medium


class PackageInfo(QScrollArea):
  install_package = pyqtSignal(object, str)
  uninstall_package = pyqtSignal(object)

  def __init__(self, parent=None):
    super(PackageInfo, self).__init__(parent=parent)
    self.package = None

    self.setStyleSheet(f"""
      QScrollArea {{
        background-color: {spacy_dark.name()};
      }}
      QLineEdit {{
        padding-left: 2px;
        border: 1px solid {spacy_medium.name()};
        color: {spacy_light.name()};
        background: {spacy_dark.name()};
      }}
      QComboBox {{
        padding-left: 2px;
        border: 1px solid {spacy_medium.name()};
        color: {spacy_light.name()};
        background-color: {spacy_dark.name()};
        selection-background-color: {spacy_light.name()};
        selection-color: {spacy_dark.name()}
      }}
      QComboBox QAbstractItemView {{
        padding-left: 2px;
        border: 1px solid {spacy_medium.name()};
        background-color: {spacy_dark.name()};
      }}      
      QLabel {{
        color: {spacy_light.name()};
      }}
    """)

    self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

    self.setWidgetResizable(True)

    self.layout = QVBoxLayout(self)
    self.layout.setAlignment(Qt.AlignTop)

    self.name_widget = QLabel(self)
    self.name_widget.setFont(QFont('Helvetica', 20))

    self.layout.addWidget(self.name_widget)

    self.version_layout = QGridLayout()
    self.installed_label = QLabel('Installed:', self)
    self.installed_version = QLineEdit(self)
    self.installed_version.setReadOnly(True)
    self.uninstall_button = QPushButton('Uninstall')
    self.uninstall_button.setFlat(True)
    self.uninstall_button.clicked.connect(self._on_uninstall_clicked)
    self.version_layout.addWidget(self.installed_label, 0, 0)
    self.version_layout.addWidget(self.installed_version, 0, 1)
    self.version_layout.addWidget(self.uninstall_button, 0, 2)

    self.version_label = QLabel('Version:')
    self.install_version_combo = QComboBox()
    self.install_version_combo.currentIndexChanged.connect(self._set_install_version_combo)
    self.install_version_button = QPushButton('Install')
    self.install_version_button.setFlat(True)
    self.install_version_button.clicked.connect(self._on_install_clicked)
    self.version_layout.addWidget(self.version_label, 1, 0)
    self.version_layout.addWidget(self.install_version_combo, 1, 1)
    self.version_layout.addWidget(self.install_version_button, 1, 2)

    self.layout.addLayout(self.version_layout)

    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)

    self.layout.addWidget(line)

    self.detail_widget = PackageDetail(self)
    self.layout.addWidget(self.detail_widget, alignment=Qt.AlignLeft)

  @pyqtSlot()
  def set_package(self, package):
    self.package = package
    self.name_widget.setText(package.name)
    self._set_install_versions(package)

    if package.installed:
      self.installed_version.setText(str(package.installed))
      self.uninstall_button.setEnabled(True)
    else:
      self.installed_version.setText('Not Installed')
      self.uninstall_button.setEnabled(False)

    self.detail_widget.set_package(self.package)
    self._set_install()

  def _set_install_versions(self, package):
    self.install_version_combo.clear()

    set_latest_stable = False
    for version in package.versions:
      if not version.is_prerelease and not set_latest_stable:
        self.install_version_combo.addItem(f"Latest Stable {str(version)}", str(version))
        set_latest_stable = True
      else:
        self.install_version_combo.addItem(str(version), str(version))

  def _set_install(self):
    index = self.install_version_combo.currentIndex()
    self._set_install_version_combo(index)

  def _set_install_version_combo(self, index):
    version = self.install_version_combo.itemData(index, Qt.UserRole)
    if str(self.package.installed) == version:
      self.install_version_button.setEnabled(False)
    else:
      self.install_version_button.setEnabled(True)

  def _on_install_clicked(self):
    index = self.install_version_combo.currentIndex()
    version = self.install_version_combo.itemData(index, Qt.UserRole)
    self.install_package.emit(self.package, version)

  def _on_uninstall_clicked(self):
    self.uninstall_package.emit(self.package)


class PackageDetail(QWidget):
  def __init__(self, parent=None):
    super(PackageDetail, self).__init__(parent=parent)
    self.layout = QGridLayout()
    self.setStyleSheet(f"""
      QLabel {{
        qproperty-alignment: AlignTop;
        font: 12pt 'Tahoma'
      }}
    """)

  def set_package(self, package):
    QWidget().setLayout(self.layout)
    self.layout = QGridLayout()
    self.layout.setSizeConstraint(QLayout.SetMinimumSize)
    self.setLayout(self.layout)

    for i, (key, value) in enumerate(package.detail_dict().items()):
      key_label = QLabel('<b>' + key + ':</b>')

      value_label = QLabel(value)
      value_label.setWordWrap(True)
      value_label.adjustSize()
      self.layout.addWidget(key_label, i, 0)
      self.layout.addWidget(value_label, i, 1)
