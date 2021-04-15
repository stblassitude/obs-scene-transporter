import unittest

from pathlib import Path
from unittest.mock import patch

from obsscenetransporter import ObsStudioSceneCollection
from obsscenetransporter.pathformatter import PathFormatter


class TestAssets(unittest.TestCase):

    def setUp(self) -> None:
        self.dut = ObsStudioSceneCollection.from_path("obsscenetransporter/tests/fixtures/TransportTest-mac.json")

    def test_name(self):
        self.assertEqual("TransportTest", self.dut.name)

    def test_process_assets_in_transitions(self):
        def p(o: dict, k: str) -> None:
            r.append(o[k])

        r = []
        self.dut._process_assets_in_transitions(self.dut.scenes, p)

        self.assertEqual(1, len(r))
        self.assertEqual("/Users/dev/Downloads/OBS-TransportTest/Rotating_earth.mp4", r[0])

    def test_process_assets_in_sources(self):
        def p(o: dict, k: str) -> None:
            r.append(o[k])

        r = []
        self.dut._process_assets_in_sources(self.dut.scenes, p)
        r = sorted(set(r))

        self.assertEqual(4, len(r))
        self.assertEqual("/Users/dev/Documents/DevDay/Screens/broadcast_test_pattern_1920X1080.jpg", r[0])
        self.assertEqual("/Users/dev/Downloads/OBS-TransportTest", r[1])
        self.assertEqual("/Users/dev/Downloads/OBS-TransportTest/Rotating_earth.mp4", r[2])

    def test_dict_path(self):
        def u(d: dict, k: str) -> None:
            r.append((k, d[k]))

        r = []
        d = {}
        p = []
        ObsStudioSceneCollection._dict_path(d, p, u)

        r = []
        d = {"a": "foo"}
        p = ["a"]
        ObsStudioSceneCollection._dict_path(d, p, u)
        self.assertEqual(1, len(r))
        self.assertEqual(("a", "foo"), r[0])

        r = []
        d = {"a": [{"b": "foo"}]}
        p = ["a", "b"]
        ObsStudioSceneCollection._dict_path(d, p, u)
        self.assertEqual(1, len(r))
        self.assertEqual(("b", "foo"), r[0])

        r = []
        d = {"a": [{"b": "foo", "c": "bar"}]}
        p = ["a", "c"]
        ObsStudioSceneCollection._dict_path(d, p, u)
        self.assertEqual(1, len(r))
        self.assertEqual(("c", "bar"), r[0])

        r = []
        d = {
            "a": [
                {
                    "b": "foo",
                    "c": "bar"
                },
                {
                    "b": "fuu",
                    "c": "baz"
                }
            ]
        }
        p = ["a", "c"]
        ObsStudioSceneCollection._dict_path(d, p, u)
        self.assertEqual(2, len(r))
        self.assertEqual(("c", "bar"), r[0])

        r = []
        p = "a.c"
        ObsStudioSceneCollection._dict_path(d, p, u)
        self.assertEqual(2, len(r))
        self.assertEqual(("c", "bar"), r[0])

    @patch("os.path.isfile")
    def test_format_file_name_expanding_dirs_file(self, mock_os_path_isfile):
        mock_os_path_isfile.return_value = True
        r = PathFormatter().format_expanding_dirs("/home/foo/image.jpg")
        self.assertEqual(["/home/foo/./image.jpg"], r)

    def test_format_file_name_expanding_dirs_dir_with_file(self):
        with patch("os.path.isdir") as mock_os_path_isdir, \
                patch("os.path.isfile") as mock_os_path_isfile, \
                patch.object(Path, "glob") as mock_path_glob:
            def isdir(path):
                return str(path) == "/home/foo/subdir"
            def isfile(path):
                return str(path) == "/home/foo/subdir/image.jpg"
            mock_os_path_isdir.side_effect = isdir
            mock_os_path_isfile.side_effect = isfile
            mock_path_glob.return_value = [Path("/home/foo/subdir/image.jpg")]
            r = PathFormatter().format_expanding_dirs("/home/foo/subdir")
            mock_path_glob.assert_called_with("*")
            self.assertEqual(["/home/foo/./subdir/image.jpg"], r)


if __name__ == '__main__':
    unittest.main()
