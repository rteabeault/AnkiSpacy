import os
import shutil
import zipfile

from invoke import task


@task(help={"Dude"})
def clean(c):
  """
  Cleans the project.
  """
  for path in ['src/__pycache__', 'src/ui/__pycache__', 'dist']:
    if os.path.exists(path):
      print(f"Removing {path}")
      shutil.rmtree(path)


@task(clean)
def dist(c):
  """
  Creates a distribution of the addon that can be uploaded to ankiweb
  """
  if not os.path.exists('dist'):
    os.makedirs('dist')
  print("Creating dist file...")
  zipdir('src', 'dist/AnkiSpacy.addon', _is_dist_dir)
  print("dist/AnkiSpacy.addon created")


@task
def test(c):
  """
  Runs tests
  """
  print("Running tests!")


def zipdir(src_path, dest_path, filter):
  zipf = zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED)

  for folderName, subfolders, filenames in os.walk(src_path):
    for filename in filenames:
      filePath = os.path.join(folderName, filename)
      arcname = os.path.relpath(filePath, src_path)

      if filter(arcname):
        zipf.write(filePath, arcname=arcname)


def _is_dist_dir(path):
  return not path.startswith('user_files')
