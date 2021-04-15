import unittest

from io import BytesIO
from obsscenetransporter.pathformatter import ZipPathFormatter
from zipfile import ZipFile

class TestPathFormatter(unittest.TestCase):

    def setUp(self) -> None:
        b = BytesIO()
        self.zipfile = ZipFile(b, "w")
        self.zipfile.writestr("assets/image0.jpg", "foo")
        self.zipfile.writestr("assets/dir/image1.jpg", "foo")
        self.zipfile.writestr("assets/dir/image2.jpg", "foo")
        self.zipfile.writestr("assets/image0.jpg1", "foo")

    def test_zip_formatter(self):
        zpf = ZipPathFormatter(self.zipfile)
        self.assertEqual(["assets/image0.jpg"], zpf.format_expanding_dirs("assets/image0.jpg"))
        self.assertEqual(["assets/dir/image1.jpg"], zpf.format_expanding_dirs("assets/dir/image1.jpg"))
        self.assertEqual(["assets/dir/image1.jpg", "assets/dir/image2.jpg"], zpf.format_expanding_dirs("assets/dir"))
