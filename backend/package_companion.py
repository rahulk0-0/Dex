"""Build the optional offline PC bundle during the container build."""
from pathlib import Path
import shutil,zipfile
ROOT=Path(__file__).resolve().parents[1]
web=ROOT/'web';companion=ROOT/'companion'
shutil.copytree(web,companion/'web',dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.zip'))
with zipfile.ZipFile(web/'dex-editor-companion.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for file in companion.rglob('*'):
  if file.is_file() and '__pycache__' not in str(file):archive.write(file,str(file.relative_to(companion)))
