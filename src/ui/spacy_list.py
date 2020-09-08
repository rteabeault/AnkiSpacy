import math
import os
from dataclasses import dataclass

from PyQt5.QtCore import pyqtSignal, Qt, QSize, QPoint, QRect
from PyQt5.QtGui import QFont, QFontMetrics, QPainter, QPen, QIcon, QTextLayout
from PyQt5.QtWidgets import QAbstractItemView, QStyledItemDelegate, QStyle, QListView, QToolTip

from .spacy_colors import spacy_medium, spacy_light, spacy_dark_blue, spacy_light2, spacy_dark
from .spacy_model import SpacyItemListModel
from ..spacy_packages import ModelPackage
from ..spacy_paths import resources_dir


@dataclass
class IconLayout:
  rect: QRect
  icon_rect: QRect
  text_rect: QRect
  installed_rect: QRect
  updates_rect: QRect


@dataclass
class InfoLayout:
  rect: QRect
  title_rect: QRect
  description_rect: QRect


@dataclass
class VersionLayout:
  rect: QRect
  top_version_rect: QRect
  bottom_version_rect: QRect


@dataclass
class ItemLayout:
  icon_layout: IconLayout
  info_layout: InfoLayout
  version_layout: VersionLayout


class SpacyListView(QListView):
  model_selected = pyqtSignal(object)
  spacy_selected = pyqtSignal(object)
  package_selected = pyqtSignal(object)

  def __init__(self, parent=None):
    super(SpacyListView, self).__init__(parent=parent)
    self.setMinimumWidth(400)
    self.setSelectionMode(QAbstractItemView.SingleSelection)
    self.setSelectionBehavior(QAbstractItemView.SelectRows)

    self.setStyleSheet(f"""
      QListView {{
        background-color: {spacy_dark.name()};
      }}
    """)

    self.setItemDelegate(SpacyListDelegate())


ITEM_HEIGHT = 70
VERSION_SECTION_WIDTH = 50
ICON_SECTION_WIDTH = 55
PACKAGE_TITLE_FONT_SIZE = 14
MODEL_ICON_CODE_BOX_CORNER_RADIUS = 10
MODEL_ICON_FONT_SIZE = 28
MODEL_ICON_CODE_PEN_WIDTH = 4
MODEL_ICON_CODE_BOX_PEN_WIDTH = 4
REFRESH_PATH = os.path.join(resources_dir, "refresh.png")
INSTALLED_PATH = os.path.join(resources_dir, "checkmark.png")
INCOMPATIBLE_PATH = os.path.join(resources_dir, "incompatible.png")
VERSION_FONT_SIZE = 10
DESCRIPTION_FONT_SIZE = 10


class SpacyListDelegate(QStyledItemDelegate):
  """
  Custom delegate to draw list items for spacy packages.
  """

  def __init__(self, parent=None):
    super(SpacyListDelegate, self).__init__(parent)
    self.debug_layout = False

  def paint(self, painter, option, index):
    if not index.isValid():
      return

    package = index.data(SpacyItemListModel.PackageRole)
    painter.save()

    if option.state & QStyle.State_Selected:
      background = spacy_medium
      painter.setPen(option.palette.highlightedText().color())
    else:
      painter.setPen(option.palette.text().color())
      background = spacy_dark

    painter.fillRect(option.rect, background)

    layout = self._get_layout(option)

    self._debug_layout(painter, layout)
    self._draw_icon_section(painter, layout, option, index)
    self._draw_package_info_section(painter, layout, package)
    self._draw_version_section(painter, layout, package)

    painter.restore()

  def helpEvent(self, event, view, option, index) -> bool:
    layout = self._get_layout(option)
    package = index.data(SpacyItemListModel.PackageRole)
    spacy_info = index.data(SpacyItemListModel.SpacyInfoRole)

    if layout.icon_layout.installed_rect.contains(event.pos()) and package.installed:
      if self.is_model_incompatible(package, spacy_info):
        QToolTip.showText(
          event.globalPos(),
          f"Version {package.installed} installed but may be incompatible with installed spacy "
          f"version")
        return True
      else:
        QToolTip.showText(event.globalPos(), f"Version {package.installed} installed")
        return True
    elif layout.icon_layout.updates_rect.contains(event.pos()) and package.updates_available():
      QToolTip.showText(event.globalPos(), f"Newer version available")
      return True
    elif layout.version_layout.top_version_rect.contains(event.pos()) and not package.installed:
      QToolTip.showText(event.globalPos(), f"v{package.versions[0]} latest version")
      return True
    elif layout.version_layout.top_version_rect.contains(event.pos()) and package.installed:
      QToolTip.showText(event.globalPos(), f"v{package.installed} installed")
      return True
    elif layout.version_layout.bottom_version_rect.contains(event.pos()) and package.updates():
      QToolTip.showText(event.globalPos(), f"Newer version v{package.updates()[0]} available")
      return True
    else:
      return super().helpEvent(event, view, option, index)

  def is_model_incompatible(self, package, spacy_info):
    return (type(package) == ModelPackage) and not spacy_info.is_model_compatible(
      package.name,
      package.installed)

  def sizeHint(self, option, index):
    return QSize(200, ITEM_HEIGHT)

  def _draw_icon_section(self, painter, layout, option, index):
    package = index.data(SpacyItemListModel.PackageRole)
    icon = index.data(Qt.DecorationRole)

    if icon:
      icon.paint(painter, layout.icon_layout.icon_rect)
    elif type(package) == ModelPackage:
      self._draw_model_icon(painter, option, layout, package)

    self._draw_icon_overlays(painter, layout, package, index)

  def _draw_model_icon(self, painter, option, layout, package):
    self._draw_model_icon_box(painter, layout, option)
    self._draw_model_icon_lang_code(painter, layout, package)

  @staticmethod
  def _draw_model_icon_box(painter, layout, option):
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    if option.state & QStyle.State_Selected:
      painter.setPen(QPen(spacy_light2, MODEL_ICON_CODE_BOX_PEN_WIDTH))
    else:
      painter.setPen(QPen(spacy_medium, MODEL_ICON_CODE_BOX_PEN_WIDTH))

    painter.drawRoundedRect(
      layout.icon_layout.icon_rect,
      MODEL_ICON_CODE_BOX_CORNER_RADIUS,
      MODEL_ICON_CODE_BOX_CORNER_RADIUS)
    painter.restore()

  @staticmethod
  def _draw_model_icon_lang_code(painter, layout, package):
    painter.save()
    font = painter.font()
    font.setPointSize(MODEL_ICON_FONT_SIZE)
    painter.setFont(font)
    painter.setPen(QPen(spacy_dark_blue, MODEL_ICON_CODE_PEN_WIDTH))
    painter.drawText(layout.icon_layout.text_rect, Qt.AlignLeft & Qt.AlignTop, package.lang_code)
    painter.restore()

  def _draw_icon_overlays(self, painter, layout, package, index):
    spacy_info = index.data(SpacyItemListModel.SpacyInfoRole)

    if package.installed:
      if self.is_model_incompatible(package, spacy_info):
        icon_installed = QIcon(INCOMPATIBLE_PATH)
        icon_installed.paint(painter, layout.icon_layout.installed_rect, Qt.AlignCenter)
      else:
        icon_installed = QIcon(INSTALLED_PATH)
        icon_installed.paint(painter, layout.icon_layout.installed_rect, Qt.AlignCenter)

    if package.updates_available():
      icon_refresh = QIcon(REFRESH_PATH)
      icon_refresh.paint(painter, layout.icon_layout.updates_rect, Qt.AlignCenter)

  def _draw_package_info_section(self, painter, layout, package):
    painter.save()
    title_rect = layout.info_layout.title_rect
    description_rect = layout.info_layout.description_rect

    font = painter.font()
    font.setStyle(QFont.StyleNormal)
    font.setPointSize(PACKAGE_TITLE_FONT_SIZE)
    painter.setFont(font)
    painter.setPen(QPen(spacy_light, 1))

    painter.drawText(
      title_rect,
      Qt.AlignLeft & Qt.AlignTop,
      package.display_name())

    font.setPointSize(DESCRIPTION_FONT_SIZE)
    painter.setFont(font)

    self._draw_elided_text(painter, description_rect, package.detail_dict()['Description'])

    painter.restore()

  def _draw_version_section(self, painter, layout, package):
    painter.save()

    font = painter.font()
    font.setPointSize(VERSION_FONT_SIZE)
    painter.setPen(QPen(spacy_light, 1))
    painter.setFont(font)

    if package.installed:
      self._draw_top_version(painter, layout, package.installed)
      if updates := package.updates():
        self._draw_bottom_version(painter, layout, updates[0])
    elif versions := package.versions:
      self._draw_top_version(painter, layout, versions[0])

    painter.restore()

  @staticmethod
  def _draw_top_version(painter, layout, text):
    painter.drawText(
      layout.version_layout.top_version_rect,
      Qt.AlignLeft & Qt.AlignCenter,
      f"v{text}")

  @staticmethod
  def _draw_bottom_version(painter, layout, text):
    painter.drawText(
      layout.version_layout.bottom_version_rect,
      Qt.AlignLeft & Qt.AlignCenter,
      f"v{text}")

  @staticmethod
  def _draw_version(painter, rect, text):
    painter.drawText(
      rect,
      Qt.AlignLeft & Qt.AlignCenter,
      f"v{text}")

  def _get_layout(self, option):
    rect = option.rect
    font = option.font
    icon_rect = QRect(
      QPoint(rect.x(), rect.y()),
      QSize(ICON_SECTION_WIDTH, rect.height()))

    info_rect = QRect(
      QPoint(rect.x() + ICON_SECTION_WIDTH, rect.y()),
      QSize(rect.width() - VERSION_SECTION_WIDTH - ICON_SECTION_WIDTH,
        rect.height()))

    version_rect = QRect(
      QPoint(rect.x() + rect.width() - VERSION_SECTION_WIDTH, rect.y()),
      QSize(VERSION_SECTION_WIDTH, rect.height()))

    return ItemLayout(
      icon_layout=self._get_icon_layout(icon_rect, font),
      info_layout=self._get_info_layout(info_rect, font),
      version_layout=self._get_version_layout(version_rect, font)
    )

  @staticmethod
  def _get_icon_layout(rect, font):
    icon_rect_width = min(rect.width(), rect.height())
    overlay_rect_width = icon_rect_width * 0.30

    icon_rect = QRect(
      rect.x() + 6,
      rect.y() + (overlay_rect_width / 2.0) + 6,
      icon_rect_width - (overlay_rect_width / 2.0) - 6,
      icon_rect_width - (overlay_rect_width / 2.0) - 6)

    font.setPointSize(MODEL_ICON_FONT_SIZE)
    metrics = QFontMetrics(font)
    text_height = metrics.height()
    text_rect = QRect(
      icon_rect.x() + 6,
      icon_rect.y(),
      icon_rect.width() - 6,
      text_height)

    installed_rect = QRect(
      icon_rect.x() + icon_rect.width() - (overlay_rect_width / 2),
      icon_rect.y() - (overlay_rect_width / 2),
      overlay_rect_width,
      overlay_rect_width
    )

    updates_rect = QRect(
      icon_rect.x() + icon_rect.width() - (overlay_rect_width / 2),
      icon_rect.y() + icon_rect.height() - (overlay_rect_width / 2),
      overlay_rect_width,
      overlay_rect_width
    )

    return IconLayout(
      rect=rect,
      icon_rect=icon_rect,
      text_rect=text_rect,
      installed_rect=installed_rect,
      updates_rect=updates_rect
    )

  @staticmethod
  def _get_info_layout(rect, font):
    top_margin = 12
    margin = 3
    font.setPointSize(PACKAGE_TITLE_FONT_SIZE)
    metrics = QFontMetrics(font)
    title_rect_height = metrics.height()
    title_rect_width = rect.width() - margin - margin
    title_rect = QRect(
      rect.x() + margin,
      rect.y() + top_margin,
      title_rect_width,
      title_rect_height)

    description_rect_width = title_rect_width
    description_rect_height = rect.height() - top_margin - title_rect_height - margin - margin
    description_rect = QRect(
      rect.x() + margin,
      title_rect.y() + title_rect.height() + margin,
      description_rect_width,
      description_rect_height)

    return InfoLayout(
      rect=rect,
      title_rect=title_rect,
      description_rect=description_rect
    )

  @staticmethod
  def _get_version_layout(rect, font):
    top_margin = 15
    margin = 3
    spacing = 10

    font.setPointSize(VERSION_FONT_SIZE)
    font.setStyle(QFont.StyleNormal)
    metrics = QFontMetrics(font)
    version_height = metrics.height()

    top_version_rect = QRect(
      rect.x() + margin,
      rect.y() + top_margin,
      VERSION_SECTION_WIDTH - margin - margin,
      version_height)

    bottom_version_rect = QRect(
      rect.x() + margin,
      top_version_rect.y() + version_height + spacing,
      VERSION_SECTION_WIDTH - margin - margin,
      version_height)

    return VersionLayout(
      rect=rect,
      top_version_rect=top_version_rect,
      bottom_version_rect=bottom_version_rect
    )

  @staticmethod
  def _draw_elided_text(painter, rect, text):
    """
    Uses the painter to draw text inside of rect.Computes the max number of lines that can fit
    inside the rect based on the current font inside the painter. If the text does not fit it
    will elide the last line.
    """
    painter.save()
    font = painter.font()
    metrics = QFontMetrics(font)
    line_height = metrics.lineSpacing()
    rect_width = rect.width()
    rect_height = rect.height()

    max_lines = math.floor(rect_height / line_height)

    layout = QTextLayout(text)
    layout.setFont(font)
    layout.beginLayout()
    line_count = 0
    width_used = 0
    while line_count < max_lines:
      line = layout.createLine()
      if not line.isValid():
        break

      line.setLineWidth(rect_width)
      width_used += line.naturalTextWidth()
      line_count += 1
    else:
      layout.endLayout()

    elided_text = painter.fontMetrics().elidedText(text, Qt.ElideRight, width_used)
    painter.drawText(rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, elided_text)
    painter.restore()

  def _debug_layout(self, painter, layout):
    if self.debug_layout:
      painter.save()
      painter.setPen(Qt.green)
      painter.drawRect(layout.icon_layout.rect)
      painter.drawRect(layout.info_layout.rect)
      painter.drawRect(layout.version_layout.rect)

      painter.setPen(Qt.blue)
      painter.drawRect(layout.icon_layout.text_rect)
      painter.setPen(Qt.red)
      painter.drawRect(layout.icon_layout.icon_rect)
      painter.drawRect(layout.icon_layout.installed_rect)
      painter.drawRect(layout.icon_layout.updates_rect)

      painter.setPen(Qt.blue)
      painter.drawRect(layout.info_layout.title_rect)
      painter.drawRect(layout.info_layout.description_rect)
      painter.drawRect(layout.version_layout.top_version_rect)
      painter.drawRect(layout.version_layout.bottom_version_rect)
      painter.restore()
