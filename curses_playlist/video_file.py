import os
from datetime import timedelta

from moviepy.video.io.VideoFileClip import VideoFileClip


class VideoFile:
    """
    Represents a VideoFile on disk, exposing a canonical path relative to a given entry-point (folder)
    The canonical representation is a list of strings, e.g.:

    'some\\folder\\deine_mudda.mp4' --> ['some', 'folder', 'deine_mudda.mp4']
    """

    def __init__(self, path, get_duration=False):
        self.locale_path = path
        self.locale_separator = os.path.sep
        self.stat = None
        self.duration = None

        if get_duration:
            self.get_stats()

    @property
    def path(self):
        return os.path.sep.join(self.canonical_path)

    @property
    def canonical_path(self):
        tmp = self.locale_path.split(self.locale_separator)
        if tmp[0] == ".":
            del tmp[0]
        return tuple(tmp)  # for dict

    def get_stats(self):
        """
        This method extracts the video's duration and stores it in the object. It is quite expensive to perform.
        """
        self.stat = os.stat(self.locale_path)
        try:
            tmp_video = VideoFileClip(self.locale_path)
            self.duration = timedelta(seconds=tmp_video.duration)
            tmp_video.close()
        except UnicodeDecodeError:
            self.duration = None

    def __str__(self):

        if self.duration:
            minutes = self.duration.total_seconds() // 60
            seconds = int(self.duration.total_seconds() - minutes * 60)
        else:
            minutes = 0
            seconds = 0

        # shorten to a max of len==# 110
        max_path_len = 100
        sub_len = 7
        if len(self.path) >= max_path_len:
            tmp = os.path.normpath(self.path).split(os.sep)

            for idx in range(len(tmp) - 1):
                tmp[idx] = f"{tmp[idx][:sub_len]}...{tmp[idx][-sub_len:]}"
                short_path = os.path.sep.join(tmp)
                if len(short_path) <= max_path_len:
                    break
        else:
            short_path = self.path

        return f"{short_path} ({minutes:0.0f}:{seconds:02d})"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.canonical_path == other.canonical_path
        else:
            return False

    def __repr__(self):
        return f"VideoFile({self.path})"


# debug
if __name__ == "__main__":
    os.chdir(r"Z:\tmp\torrents")
    vf = VideoFile(
        r"The Witcher (2019) Season 1 S01 1080p 10bit NF WEB-RIP x265  [Eng DD 5.1"
        r" - Hindi DD 768Kbps Org 5.1] ~ EmKayy\The Witcher S01E04 - Of Banquets, Bastards and Burials.mkv",
        get_duration=True,
    )
    print(vf)
