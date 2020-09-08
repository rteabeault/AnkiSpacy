from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QFontDatabase, QTextCursor
from PyQt5.QtWidgets import QTextEdit

from .spacy_colors import spacy_dark, spacy_light


class StdoutProgressText(QTextEdit):
  """
  Provides a QTextEdit widget for outputting terminal based text.
  """

  def __init__(self, parent=None):
    super(StdoutProgressText, self).__init__(parent=parent)
    self.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
    self.setPlaceholderText("Progress")
    self.setStyleSheet(f"""  
      QTextEdit {{
        background-color: {spacy_dark.name()};
        color: {spacy_light.name()} }}""")

  @pyqtSlot(str)
  def append_text(self, text: str):
    if text == '\x1b[?25h':
      pass
    elif text == '\x1b[?25l':
      pass
    elif text == '\r\x1b[K':
      cursor = self.textCursor()
      cursor.select(QTextCursor.LineUnderCursor)
      cursor.removeSelectedText()
      self.moveCursor(QTextCursor.StartOfLine)
    else:
      self.moveCursor(QTextCursor.End)
      self.insertPlainText(text)

  @pyqtSlot(str)
  def println(self, text: str):
    self.insertPlainText(text + "\n")

  @pyqtSlot()
  def clear_text(self):
    self.clear()
