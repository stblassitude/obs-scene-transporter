import os
import platform

class PathHelper:
    """
    Help construct correct paths to OBS Studio settings and the Documents folder.
    """
    @staticmethod
    def _get_windows_path(kind: int) -> str:
        """
        Return the path to a special folder on Windows systems.
        :param kind:
        :return:
        """
        import ctypes.wintypes
        SHGFP_TYPE_CURRENT = 0
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, kind, None, SHGFP_TYPE_CURRENT, buf)
        return buf.value

    @staticmethod
    def get_scenes_path() -> str:
        """
        Get the path to the OBS Studio directory that stores scene collections.
        :return:
        """
        if platform.system() == "Windows":
            p = PathHelper._get_windows_path(26)  # CSIDL_APPDATA
        elif platform.system() == "Darwin":
            p = os.path.expanduser("~/Library/Application Support")
        else:
            p = os.path.expanduser("~/.config")
        return os.path.join(p, "obs-studio", "basic", "scenes")

    @staticmethod
    def get_documents_path() -> str:
        """
        Get the path to the users Documents folder.
        :return:
        """
        if platform.system() == "Windows":
            p = PathHelper._get_windows_path(5)  # CSIDL_PERSONAL
        else:
            p = os.path.expanduser("~/Documents")
        return p
