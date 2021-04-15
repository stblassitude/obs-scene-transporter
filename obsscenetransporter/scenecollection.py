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
from shutil import copyfileobj
from typing import Callable, IO, Union
from zipfile import ZipFile

from obsscenetransporter.pathhelper import PathHelper
from obsscenetransporter.pathformatter import PathFormatter, ZipPathFormatter


class ObsStudioSceneCollection:
    asset_path_in_archive = "assets"
    path_props = ["file", "local_file", "path", "value"]
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

    def __init__(self, file: IO, path: str = None):
        """
        Create object from a file object.

        :param file: a file-like object to read the JSON definition from
        """
        self.assets = list()
        self.counts = {}
        self.name = "Untitled"
        self.nsources = 0
        self.nscenes = 0
        self.scenes = json.load(file)
        self.path = path

    @staticmethod
    def from_path(path: str) -> ObsStudioSceneCollection:
        """
        Create an ObsSceneCollection object from the specified JSON file.

        :param path: A fully qualified path to the file to be loaded, or a file name (without extension) that will be
            searched for in the OBS Studio scene collection directory.
        :return:
        """
        if not os.path.isfile(path):
            path = os.path.join(PathHelper.get_scenes_path(), path + ".json")
        with open(path, "r") as f:
            ossc = ObsStudioSceneCollection(f, path)
        ossc._parse(PathFormatter().format_expanding_dirs)
        return ossc

    def export_scenes(self, zipfile=None) -> None:
        """
        Export the scene into the zipfile. If no filename is specified, derive the filename from the scene collection name.
        :param zipfile:
        :return:
        """
        if not zipfile:
            zipfile = self.name + ".zip"
        self._update_assets(self.scenes, self.asset_path_in_archive, PathFormatter().format_file_name)
        with ZipFile(zipfile, "w") as zip:
            zip.writestr("scene-collection.json", json.dumps(self.scenes))
            for a in self.assets:
                an = f"{self.asset_path_in_archive}/{a.partition('/./')[2]}"
                zip.write(a, arcname=an)

    @staticmethod
    def import_scenes(zipfile: str, name: str = None, asset_dir: str = None) -> ObsStudioSceneCollection:
        """
        Import the zipfile
        :return:
        """
        with ZipFile(zipfile, "r") as zip:
            with zip.open("scene-collection.json", "r") as j:
                ossc = ObsStudioSceneCollection(j)
            zpf = ZipPathFormatter(zip, ossc.asset_path_in_archive)
            ossc._parse(zpf.format_expanding_dirs)
            if name:
                ossc.name = name
            ossc.scenes["name"] = ossc.name
            if not asset_dir:
                asset_dir = PathHelper.get_documents_path()
                asset_dir = os.path.join(asset_dir, "OBS", "Scene-Assets", ossc.name)
            asset_path_prefix_len = len(ossc.asset_path_in_archive) + 1
            ossc._fix_source_ids(platform.system())
            ossc._update_assets(ossc.scenes, asset_dir, zpf.format_file_name)
            scenes = os.path.join(PathHelper.get_scenes_path(), f"{ossc.name}.json")
            with open(scenes, "w") as fp:
                json.dump(ossc.scenes, fp)
            os.makedirs(asset_dir, exist_ok=True)
            for a in filter(lambda p: p.startswith(ossc.asset_path_in_archive), zip.namelist()):
                p = os.path.join(asset_dir, a[asset_path_prefix_len:])
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with zip.open(a, "r") as src, open(p, "wb") as dst:
                    copyfileobj(src, dst)
        return ossc

    @staticmethod
    def list_scenes(path=None) -> list[ObsStudioSceneCollection]:
        """
        Returns a list of scene collections loaded from the OBS Studio scene collection directory.

        :param path: Optional path to find scene JSON files in. Default is the platform-specific directory where
            OBS Studio stores scene collections.
        :return: a list of ObsSceneCollection objects
        """
        r = []
        if not path:
            path = PathHelper.get_scenes_path()
        p = Path(path)
        for f in sorted(p.glob("*.json")):
            r.append(ObsStudioSceneCollection.from_path(str(f)))
        return r

    @staticmethod
    def _dict_path(o: Union[dict,list], path: Union[str,list[str]], callback: Callable[[dict, str], None]) -> None:
        """
        Recursively iterate through dict o, calling callback on every element matching path.

        For each element in dict, match the first element of path.

        If o is a list, recursively handle each element.

        If path is a string, split it at ".", so you can either say ["foo", "bar"] or "foo.bar".

        :param o: dict or object to iterate over
        :param path: specifies elements to pass to callback
        :param callback: method to invoke for each matching element
        :return:
        """
        if isinstance(path, str):
            path = path.split(".")
        if isinstance(o, list):
            for i in o:
                ObsStudioSceneCollection._dict_path(i, path, callback)
        elif len(path) == 1 and path[0] in o:
            callback(o, path[0])
        elif len(path) > 0 and path[0] in o:
            ObsStudioSceneCollection._dict_path(o[path[0]], path[1:], callback)

    @staticmethod
    def _process_assets_in_sources(scenes: dict, update: Callable[[dict, str], None]) -> None:
        """
        Iterate over all sources and run the callback on each file reference contained.

        :param scene: Scene collection dict as read from the JSON
        :param update: callback to call for each element that contains a filename
        :return:
        """
        for scene in scenes["sources"]:
            if scene["versioned_id"] in ("ffmpeg_source",):
                ObsStudioSceneCollection._dict_path(scene, "settings.local_file", update)
            if scene["versioned_id"] in ("image_source",):
                ObsStudioSceneCollection._dict_path(scene, "settings.file", update)
            if scene["versioned_id"] in ("slideshow",):
                ObsStudioSceneCollection._dict_path(scene, "settings.files.value", update)
            if scene["versioned_id"] in ("vlc_source",):
                ObsStudioSceneCollection._dict_path(scene, "settings.playlist.value", update)

    @staticmethod
    def _process_assets_in_transitions(scenes: dict, update: Callable[[dict, str], None]) -> None:
        """
        Iterate over all transitions and run the callback on each file reference contained.

        :param scenes: Scene collection dict as read from the JSON
        :param update: callback to call for each element that contains a filename
        :return:
        """
        for t in scenes["transitions"]:
            if t["id"] == "obs_stinger_transition":
                ObsStudioSceneCollection._dict_path(t, "settings.path", update)

    def _find_assets(self, scene: dict, check: Callable[[str], list[str]]) -> list:
        """
        Return a list of pathnames of the assets referenced in the scene collection.
        :param scene:
        :return:
        """
        r = []

        def add(o: dict, k: str) -> None:
            r.extend(check(o[k]))

        self._process_assets_in_sources(scene, add)
        self._process_assets_in_transitions(scene, add)

        return sorted(set(r))

    def _update_assets(self, scene: dict, base: str, check: Callable[[str], str]) -> None:
        """
        Update the asset paths by replacing the path with base.
        :param scene:
        :param base:
        :return:
        """

        def update_path(o: dict, k: str) -> None:
            c = check(o[k])
            if c:
                o[k] = base + "/" + c.partition("/./")[2]

        self._process_assets_in_sources(scene, update_path)
        self._process_assets_in_transitions(scene, update_path)

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
            for (os, map) in self.source_id_mappings.items():
                for (k, v) in map.items():
                    if source[prop] == v:
                        source[prop] = k
                        return
        else:
            for (k, v) in self.source_id_mappings[system].items():
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

    def _parse(self, check: Callable[[str], list[str]]) -> None:
        self.assets = self._find_assets(self.scenes, check)
        self.counts = {
            "scene": 0
        }
        for i in self.scenes["sources"]:
            if i["id"] in self.counts:
                self.counts[i["id"]] += 1
            else:
                self.counts[i["id"]] = 1
        self.name = self.scenes["name"]
        self.nsources = len(self.scenes["sources"]) - self.counts["scene"]
        self.nscenes = self.counts["scene"]
        self._fix_source_ids()

    def _update_asset_paths(self, base: str) -> None:
        self._update_assets(self.scenes, base)


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
    parser.add_argument("-n", "--name", help="use this name instead of what's in the scene collection",
                        type=str)
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")
    parser.add_argument("cmd", help="command to run")
    parser.add_argument("params", help="additional parameters, depending on command",
                        nargs="*")
    args = parser.parse_args(argv)

    if args.cmd == "list" or args.cmd == "ls":
        for f in ObsStudioSceneCollection.list_scenes():
            if args.long:
                print(f"{f.name}:\t{f.path}")
                print(f"    scenes:   {f.nscenes}")
                print(f"    sources:  {f.nsources}")
                for s in sorted(f.counts.keys()):
                    if s in ("scene"):
                        continue
                    print(f"        {s}: {f.counts[s]}")
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
        oss = ObsStudioSceneCollection.from_path(args.params[0])
        if args.name:
            oss.name = args.name
        if len(args.params) > 1:
            oss.export_scenes(args.params[1])
        else:
            oss.export_scenes()
    elif args.cmd == "import":
        if len(args.params) != 1:
            parser.error("Need to specify a zip file")
            return os.EX_USAGE
        ObsStudioSceneCollection.import_scenes(args.params[0], args.name)
    else:
        parser.error(f"Unknown command {args.cmd}")
        return os.EX_USAGE
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
