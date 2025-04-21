import os
import pickle
import threading
from typing import List, Union

from tqdm import tqdm

from curses_playlist.tools import StopWatch
from curses_playlist.video_file import VideoFile


class VideoStore:
    """
    Cache list of videofiles (extracting duration takes time)
    """

    def __init__(self, cache_file_name="video_store_2.pkl"):
        """
        The constructor initializes the VideoStore by loading the old state from the .pkl
        and retrieving a list of video files from the cwd.

        The internal representation is a List[VideoFile]

        Args:
            cache_file_name: where the VideoStore state gets stored
        """

        # load cache
        self.cache_file_name = cache_file_name
        self.local_db = dict()
        try:
            with open(cache_file_name, "rb") as f:
                full_db = pickle.load(f)
        except IOError:
            print("no videostore found, indexing ... pls restart afterwards.`")
            full_db = dict()

        self.full_db = full_db
        # Create and start a thread
        self.update_thread = threading.Thread(target=self.update_videostore(), args=())
        self.update_thread.start()
        print("found %i files" % len(self.local_db))

    def update_videostore(self):
        # load files from filesystem
        with StopWatch("filewalk"):
            candidate_paths = self.grab_files_from_disk()

        modified = False
        with StopWatch("populate Videostore"):
            for idx, path in tqdm(
                enumerate(candidate_paths), total=len(candidate_paths)
            ):

                el = VideoFile(path)
                canonical_path = el.canonical_path
                if canonical_path not in self.full_db:
                    modified = True
                    try:
                        el.get_stats()
                        self.full_db[canonical_path] = el
                        self.local_db[canonical_path] = el
                    except OSError:
                        print(f"\nWARNING: Cannot parse {el}, not adding.")
                else:
                    self.local_db[canonical_path] = self.full_db[canonical_path]

                if idx % 10 == 0 and modified:
                    with open(self.cache_file_name, "wb") as f:
                        pickle.dump(self.full_db, f)
                        modified = False

        with open(self.cache_file_name, "wb") as f:
            pickle.dump(self.full_db, f)

    def get_file_list(self):
        with StopWatch("sort by modification time"):
            flist = [self.local_db[key] for key in self.local_db]
            flist.sort(
                key=lambda el: el.stat.st_ctime, reverse=True
            )  # sort by modification time, newest fist
        return flist

    def retrieve_video_file(self, name: str) -> Union[VideoFile, None]:
        tmp = VideoFile(name)
        return self.local_db.get(tmp.canonical_path, None)

    @staticmethod
    def grab_files_from_disk() -> List[str]:
        """
        Recursively traverse directory tree and return list of files that have a valid extension.
        Returns: List of valid file paths relative to cwd.
        """
        valid_extensions = [
            ".avi",
            ".asf",
            ".mp4",
            ".m4v",
            ".mov",
            ".flv",
            ".wmv",
            ".mkv",
        ]

        all_files = []
        for dir_name, subdir_list, file_list in os.walk(".", followlinks=True):
            for fname in file_list:
                all_files.append(os.path.join(dir_name, fname))

        all_files = list(set(all_files))
        all_files = [
            el for el in all_files if os.path.splitext(el)[1] in valid_extensions
        ]

        return all_files
