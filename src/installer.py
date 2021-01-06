import logging
import os
import runpy
import sys
from contextlib import redirect_stdout, redirect_stderr, contextmanager
from io import TextIOBase

from PyQt5.QtCore import QObject, pyqtSignal
from pip._internal.cli import progress_bars
from pip._internal.cli.progress_bars import DownloadProgressMixin
from pip._vendor.progress.bar import Bar
from pkg_resources import Requirement

from .const import ADDON_NAME
from .spacy_packages import distribution

logger = logging.getLogger(f'{ADDON_NAME}.{__name__}')

class PipInstallerSignals(QObject):
  install_complete = pyqtSignal(object)
  install_progress = pyqtSignal(str)
  install_failed = pyqtSignal(object, object)


class PipInstaller:
  def __init__(self, package, version):
    super(PipInstaller, self).__init__()
    self.package = package
    self.requirement = package.requirement(version)
    self.target_path = package.install_dir
    self.exclude_deps = package.exclude_deps
    self.signals = PipInstallerSignals()
    self.output = PipInstallProgress(self)

  def run(self):
    try:
      args = [
        'pip',
        'install',
        '--upgrade',
        '--no-cache-dir',
        '--progress-bar', 'qt_friendly',
        '--disable-pip-version-check',
        '--no-cache-dir',
        '-t', self.target_path,
        self.target()
      ]

      if self.exclude_deps:
        args.append('--no-deps')

      self._run_pip_install(args)

      if self.exclude_deps:
        dist = distribution(self.package.install_dir, self.package.name.replace('_', '-'))
        for req in dist.requires():
          if req.name in self.exclude_deps:
            continue

          args = [
            'pip',
            'install',
            '--upgrade',
            '--no-cache-dir',
            '--progress-bar', 'qt_friendly',
            '--disable-pip-version-check',
            '--no-cache-dir',
            '-t', self.target_path,
            str(req)
          ]

          self._run_pip_install(args)

      self.signals.install_complete.emit(self)

    except SystemExit as e:
      logger.debug(f"Install failed with exception {e}")
      self.signals.install_failed.emit(e, self)
    except Exception as e:
      logger.debug(f"Install failed with exception {e}")
      self.signals.install_failed.emit(e, self)

  def _run_pip_install(self, args):
    with temp_sys_argv(), temp_environ():
      os.environ['LC_ALL'] = "en_US.UTF-8"
      sys.argv = args
      try:
        logger.info(f"Running pip install with args {sys.argv}")
        with redirect_stdout(self.output), redirect_stderr(self.output):
          runpy.run_module("pip", run_name="__main__")
      except SystemExit as se:
        logger.debug(f"Pip SystemExit: {se.code}")
        if se.code != 0:
          raise se

  def target(self):
    if type(self.requirement) == str:
      return self.requirement
    elif type(self.requirement) == Requirement:
      return self.requirement.url if self.requirement.url else str(self.requirement)


class PipInstallProgress(TextIOBase):
  """
  Intercepts calls to write and emits them as a signal 'install_progress'.
  """
  def __init__(self, installer):
    super(PipInstallProgress, self).__init__()
    self.installer = installer

  def write(self, str):
    self.installer.signals.install_progress.emit(str)

  def isatty(self):
    return True


class QtFriendlyBar(DownloadProgressMixin, Bar):
  """
  A progress download bar that sets file to sys.stdout when it
  is instantiated. That way when the PipInstaller redirects
  stdout we can properly capture what pip is writing.
  """

  def __init__(self, *args, **kwargs):
    super(QtFriendlyBar, self).__init__(*args,
      **dict({
        'check_tty': False,
        'file': sys.stdout,
        'hide_cursor': False,
        'suffix': "%(downloaded)s %(download_speed)s %(pretty_eta)s"
      }, **kwargs))


# Add our progress bar to pip
progress_bars.BAR_TYPES.update(qt_friendly=(QtFriendlyBar, QtFriendlyBar))

@contextmanager
def temp_sys_argv():
  original_argv = sys.argv.copy()
  try:
    yield
  finally:
    sys.argv = original_argv

@contextmanager
def temp_environ():
  _environ = dict(os.environ)
  try:
    yield
  finally:
    os.environ.clear()
    os.environ.update(_environ)
