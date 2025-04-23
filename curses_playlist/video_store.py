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
        try:
            with open(cache_file_name, "rb") as f:
                self.full_db = pickle.load(f)
                print(f"loaded {len(self.full_db)} files")
        except IOError:
            print("no videostore found, indexing ... pls restart afterwards.`")
            self.full_db = dict()

        # Create and start a thread for updating DB
        self.update_thread = threading.Thread(target=self.update_videostore)
        self.update_thread.start()

    def update_videostore(self):
        """
        Update videostore and check for consistency wrt. deletion / renaming
        """
        # load files from filesystem
        with StopWatch("filewalk"):
            candidate_paths = self.grab_files_from_disk()

        # check: paths that are not yet in db
        modified = False
        with StopWatch("check: paths in videostore"):
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
                    except OSError:
                        print(f"\nWARNING: Cannot parse {el}, not adding.")

                if idx % 10 == 0 and modified:
                    with open(self.cache_file_name, "wb") as f:
                        pickle.dump(self.full_db, f)
                        modified = False

        # check: deletion / renaming
        db_keys = set(self.full_db.keys())
        canonical_paths = {VideoFile(el).canonical_path for el in candidate_paths}
        diff = db_keys - canonical_paths

        print(f"DB elements with no file counterpart: {diff}")

        for el in diff:
            del self.full_db[el]

        with open(self.cache_file_name, "wb") as f:
            pickle.dump(self.full_db, f)

    def get_file_list(self):
        with StopWatch("sort by modification time"):
            flist = [self.full_db[key] for key in self.full_db]
            flist.sort(
                key=lambda el: el.stat.st_ctime, reverse=True
            )  # sort by modification time, newest fist
        return flist

    def retrieve_video_file(self, name: str) -> Union[VideoFile, None]:
        tmp = VideoFile(name)
        return self.full_db.get(tmp.canonical_path, None)

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

if __name__ == '__main__':
    os.chdir(r"Z:\diverse\porn\scenes")
    vs = VideoStore()