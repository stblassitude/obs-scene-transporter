"""
A collection of OBS Studio Scenes
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import textwrap

from pathlib import Path
from typing import Callable
from zipfile import ZipInfo, ZipFile

# Maps the source ids as used in Linux to macOS or Windows
source_id_mappings = {
    "Darwin": {
        "v4l2_input": "av_capture_input",
        "xshm_input": "display_capture",
    },
    "Windows": {
        "v4l2_input": "dshow_input",
        "xshm_input": "monitor_capture",
    },
}


def _get_windows_path(kind: int) -> str:
    import ctypes.wintypes
    SHGFP_TYPE_CURRENT = 0
    buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(None, kind, None, SHGFP_TYPE_CURRENT, buf)
    return buf.value


def _get_scenes_path() -> str:
    if platform.system() == "Windows":
        p = _get_windows_path(26) # CSIDL_APPDATA
    elif platform.system() == "Darwin":
        p = os.path.expanduser("~/Library/Application Support")
    else:
        p = os.path.expanduser("~/.config")
    return os.path.join(p, "obs-studio/basic/scenes")


def _get_assets_path() -> str:
    if platform.system() == "Windows":
        p = _get_windows_path(5) # CSIDL_PERSONAL
    else:
        p = os.path.expanduser("~/Documents")
    return p


class ObsStudioSceneCollection:
    asset_path_in_archive = "assets"
    path_props = ["file", "local_file", "path"]

    def __init__(self, name: str = None, path: str = None):
        if not name and not path:
            raise Exception("Need either name or path")
        if path:
            self.path = path
        else:
            self.path = os.path.join(_get_scenes_path(), name + ".json")
        if name:
            self.name = name
        else:
            self.name = os.path.splitext(os.path.basename(self.path))[0]
        self.assets = None
        self.counts = {}
        self.loaded = False
        self.nsources = 0
        self.nscenes = 0
        self.scenes = None
        self.title = None

    def _find_asset_in(self, o, update: Callable[[dict, str, str], None]):
        """
        Recursively walk the scene collection and run a callback on each path definition.
        :param o:
        :param update:
        :return:
        """
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str) and k in self.path_props:
                    update(o, k, v)
                else:
                    self._find_asset_in(v, update)
        elif isinstance(o, list):
            for i in o:
                self._find_asset_in(i, update)
        # ignore all other types

    def _find_assets(self, scene: dict) -> list:
        """
        Return a list of pathnames of the assets referenced in the scene collection.
        :param scene:
        :return:
        """
        r = []

        def append(o: dict, k: str, v: str) -> None:
            r.append(v)

        self._find_asset_in(scene, append)
        return sorted(set(r))

    def _update_assets(self, scene: dict, base: str):
        """
        Update the asset paths by replacing the path with base.
        :param scene:
        :param base:
        :return:
        """

        def update_path(o: dict, k: str, path: str) -> None:
            o[k] = os.path.join(base, os.path.basename(path))

        self._find_asset_in(scene, update_path)

    def _map_source_id(self, source: dict, prop, system) -> None:
        """
        Update the key prop in each source definition by mapping either the Linux definition to the specified system
        definition, or vice versa.
        :param source: The source dict to operate on
        :param prop: the name of the property to update
        :param system: the OS to update the definition to
        :return:
        """
        if system == "Linux":
            for (os, map) in source_id_mappings.items():
                for (k, v) in map.items():
                    if source[prop] == v:
                        source[prop] = k
                        return
        else:
            for (k, v) in source_id_mappings[system].items():
                if source[prop] == k:
                    source[prop] = v
                    return

    def _fix_source_ids(self, system="Linux") -> None:
        """
        Adjust the id property of each source to use the camera or display grabber ID appropriate for the target OS.
        :param system: "Linux", "Darwin", or "Windows"
        :return:
        """
        for s in self.scenes["sources"]:
            self._map_source_id(s, "id", system)
            self._map_source_id(s, "versioned_id", system)

    def _parse(self) -> None:
        self.loaded = True
        self.counts = {
            "scene": 0
        }
        for i in self.scenes["sources"]:
            if i["id"] in self.counts:
                self.counts[i["id"]] += 1
            else:
                self.counts[i["id"]] = 1
        self.nsources = len(self.scenes["sources"]) - self.counts["scene"]
        self.nscenes = self.counts["scene"]
        self.title = self.scenes["name"]
        self.assets = self._find_assets(self.scenes)
        self._fix_source_ids()

    def _adjust_asset_path(self, base: str, path: str) -> str:
        return os.path.join(base, os.path.basename(path))

    def _update_asset_paths(self, base: str) -> None:
        self._update_assets(self.scenes, base)

    def _load(self) -> ObsStudioSceneCollection:
        if self.loaded:
            return self
        with open(self.path, 'r', encoding='utf-8') as fp:
            self.scenes = json.load(fp)
        self._parse()
        return self

    def export_scenes(self, zipfile=None) -> None:
        """
        Export the scene into the zipfile. If no filename is specified, derive the filename from the scene collection name.
        :param zipfile:
        :return:
        """
        if not zipfile:
            zipfile = self.name + ".zip"
        if not self.loaded:
            self._load()
        self._update_asset_paths(self.asset_path_in_archive)
        with ZipFile(zipfile, "w") as zip:
            zip.writestr("scene-collection.json", json.dumps(self.scenes))
            for a in self.assets:
                if os.path.isfile(a):
                    zip.write(a, arcname=self._adjust_asset_path(self.asset_path_in_archive, a))
                else:
                    print(f"Warning: no such file \"{a}\", skipping", file=sys.stderr)

    def import_scenes(self, zipfile: str, name: str = None, asset_dir: str = None) -> None:
        """
        Import the zipfile
        :return:
        """
        with ZipFile(zipfile, "r") as zip:
            with zip.open("scene-collection.json", "r") as j:
                self.scenes = json.load(j)
            self._parse()
            if name:
                self.name = name
            self.scenes["name"] = name
            if not asset_dir:
                asset_dir = _get_assets_path()
                asset_dir = os.path.join(asset_dir, f"OBS/Scene-Assets/{self.name}")
            self._fix_source_ids(platform.system())
            self._update_asset_paths(asset_dir)
            scenes = os.path.join(_get_scenes_path(), f"{self.name}.json")
            with open(scenes, "w") as fp:
                json.dump(self.scenes, fp)
            os.makedirs(asset_dir, exist_ok=True)
            for a in self.assets:
                try:
                    # zip.extract(a, os.path.join(asset_dir, os.path.basename(a)))
                    with zip.open(a, "r") as src, open(os.path.join(asset_dir, os.path.basename(a)), "wb") as dst:
                        dst.write(src.read())
                except KeyError as e:
                    print(f"Warning: No such file in archive: \"{a}\", skipping", file=sys.stderr)


def list_scenes(path=None) -> list:
    r = []
    if not path:
        path = _get_scenes_path()
    p = Path(path)
    for f in sorted(p.glob("*.json")):
        r.append(ObsStudioSceneCollection("", path=str(f)))
    return r


def main(argv: list = None) -> int:
    if not argv:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     prog="obs-scene-transporter",
                                     description=textwrap.dedent("""\
        Import or export a scene collection into/out of OBS Studio, using a ZIP file.
        The first parameter must be a sub-command.
        
        list:
            List the scene collections available for export in OBS. With -v, list more
            details about the scenes.
        
        export <scene> <zipfile>:
            During export, package up all references assets (images, videos, etc.) into
            the ZIP, and fix their path names in the scene collection.
        
        import <zipfile>:
            During import, extract the assets to a directory, and fix the scene
            collection to refer to those absolute paths. For desktop sharing and camera
            sources, fix the types of sources for the operating system in use.
    """))
    parser.add_argument("-a", "--assets", help="directory to store assets in on import",
                        type=str)
    parser.add_argument("-i", "--ignore", help="ignore missing files",
                        action="store_true")
    parser.add_argument("-l", "--long", help="include more details in list output",
                        action="store_true")
    parser.add_argument("-n", "--name", help="import collection under this name",
                        type=str)
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")
    parser.add_argument("cmd", help="command to run")
    parser.add_argument("params", help="additional parameters, depending on command",
                        nargs="*")
    args = parser.parse_args(argv)

    if args.cmd == "list" or args.cmd == "ls":
        for f in list_scenes():
            if args.long:
                f._load()
                print(f"{f.name}:\t{f.path}")
                print(f"    name:     {f.title}")
                print(f"    scenes:   {f.nscenes}")
                print(f"    sources:  {f.nsources}")
                print(f"    assets:")
                for i in f.assets:
                    e = "" if os.path.isfile(i) else " *"
                    print(f"        {i}{e}")
            else:
                print(f.name)
    elif args.cmd == "export":
        if not (1 <= len(args.params) <= 2):
            parser.error("Need exactly name and ZIP file name")
            return os.EX_USAGE
        oss = ObsStudioSceneCollection(name=args.params[0])
        if len(args.params) > 2:
            oss.export_scenes(args.params[1])
        else:
            oss.export_scenes()
    elif args.cmd == "import":
        if len(args.params) != 1:
            parser.error("Need to specify a zip file")
            return os.EX_USAGE
        oss = ObsStudioSceneCollection(name="Importing")
        oss.import_scenes(args.params[0], args.name)
    else:
        parser.error(f"Unknown command {args.cmd}")
        return os.EX_USAGE
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
