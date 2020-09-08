import os
import shutil

def remove_path(path):
  if os.path.isfile(path):
    os.remove(path)
  if os.path.islink(path):
    os.unlink(path)
  if os.path.exists(path):
    shutil.rmtree(path)

def ensureDirExists(path):
  path = str(path)
  if not os.path.exists(path):
    os.makedirs(path)
