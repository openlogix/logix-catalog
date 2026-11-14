"""MkDocs hooks (mkdocs.yml, hooks): adds the generated board and FPGA lists.

boards.md and fpgas.md are written from the catalog's files by tools/lists.py
on every docs build, so they always match the catalog and aren't committed.
"""

import sys
from pathlib import Path

from mkdocs.structure.files import File

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lists  # noqa: E402


def on_files(files, config):
    files.append(File.generated(config, "boards.md", content=lists.boards_page()))
    files.append(File.generated(config, "fpgas.md", content=lists.fpgas_page()))
    return files
