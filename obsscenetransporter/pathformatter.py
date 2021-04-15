from __future__ import annotations

import os

from pathlib import Path
from typing import Union
from zipfile import ZipFile


class PathFormatter:
    """
    Massage file names in the filesystem into a format that allows replacing absolute paths with relative ones.

    The path includes "/./" as a special separator to indicate the split between the base path and the
    file/subdirectory.
    """
    def format_file_name(self, path: str) -> Union[str, None]:
        """
        Format path to indicate the split between the base path and the file/subdirectory.

        :param path:
        :return:
        """
        if os.path.isfile(path) or os.path.isdir(path):
            return os.path.dirname(path) + "/./" + os.path.basename(path)
        return None

    def format_expanding_dirs(self, path: str) -> list[str]:
        """
        Create a list of all asset files. If a directory is specified, return a list of all files.

        :param path:
        :return:
        """
        if os.path.isfile(path):
            return [os.path.dirname(path) + "/./" + os.path.basename(path)]
        r = list()
        if os.path.isdir(path):
            pp = Path(path)
            for e in pp.glob("*"):
                if not os.path.basename(e).startswith(".") and os.path.isfile(e):
                    p = os.path.dirname(path)
                    r.append(p + "/./" + str(e.relative_to(Path(p))))
        return r


class ZipPathFormatter(PathFormatter):
    """
    Massage ZIP archive file names into a format that allows replacing absolute paths with relative ones.
    """

    def __init__(self, zip: ZipFile, prefix: str = "assets") -> None:
        self.prefix = prefix
        self.zip = zip
        self.names = zip.namelist()

    def format_file_name(self, path: str):
        if path.startswith(self.prefix):
            return self.prefix + "/./" + path[(len(self.prefix) + 1):]
        return path

    def format_expanding_dirs(self, path: str) -> list[str]:
        if path in self.names:
            return [path]
        path += "/"
        return list(filter(lambda n: n.startswith(path), self.names))
