import curses
import os
from contextlib import contextmanager

from curses_playlist.curses_gui import MyCursesGUI
from curses_playlist.flask_controller import flask_vlc_context
from curses_playlist.gui_state import GUIState
from curses_playlist.platform_defs import CMD, KEY_BACKSPACE
from curses_playlist.tools import start_blank_screen
from curses_playlist.video_file import VideoFile
from curses_playlist.video_store import VideoStore


@contextmanager
def volume(vol: float):
    """
    Contextmanager for setting Master Windows Volume to a certain value and then returning
    it to the previous volume using pycaw.

    Args:
        vol: in [-64, 0] which gets mapped to [0, 100] on my windows desktop.
    """

    if vol < -64 or vol > 0:
        raise ValueError("gain must be in range [-64, 0]")

    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    current_vol = volume.GetMasterVolumeLevel()
    res = volume.SetMasterVolumeLevel(vol, None)
    print(f"setting MasterVolume to {vol} with res({res})")

    yield

    res = volume.SetMasterVolumeLevel(current_vol, None)
    print(f"re-setting MasterVolume to {current_vol} with res({res})")


class PlistController:
    """gets commands, e.g. from curses and knows how to react to them.
    Controls GUI.
    """

    def __init__(self, playlist_path: str, gain: float, clear_playlist: bool):

        self.playlist_path = playlist_path
        self.gain = gain
        video_store = VideoStore()

        self.state = GUIState(video_store.get_file_list())

        if not clear_playlist:
            self.state.restore_from_playlist(playlist_path, video_store)

        self.gui = MyCursesGUI(self)
        self.gui.start()  # blocking.

        # react to result
        # write out playlist and play
        print(f"State: {self.state.mode}")
        print(f"playlist: {self.state.play_list}")

        if self.state.mode == GUIState.PLAY:

            self.write_playlist()
            start_blank_screen()  # windowed playback on black screen.
            cmd = f"{CMD} {playlist_path}"
            print(cmd)
            with volume(self.gain), flask_vlc_context():
                os.system(cmd)

        # only write out playlist
        if self.state.mode == GUIState.WRITE:
            self.write_playlist()

        print("waiting for update videostore.")
        video_store.update_thread.join()

    def write_playlist(self):
        """
        Write out playlist to disk that is understood my mplayer or vlc.
        """

        def write_single_entry(output_file, fname: VideoFile):
            entry = os.path.join(os.getcwd(), os.path.sep.join(fname.canonical_path))
            if os.path.isfile(entry):
                output_file.write("{}\n".format(entry))

        with open(self.playlist_path, "w") as output_file:
            for obj in self.state.play_list:
                if type(obj) is not list:
                    write_single_entry(output_file, obj)
                else:
                    output_file.write("# group_start\n")
                    for fname in obj:
                        write_single_entry(output_file, fname)
                    output_file.write("# group_end\n")

    def key_pressed(self, c):
        """This is the only method that is supposed to handle keypresses.
        It updates the internal state according to the current state and the pressed key.

        Args:
            c: the pressed key
        """

        #
        # INPUT
        #
        if self.state.mode == GUIState.INPUT:
            # ESC
            if c == 27:
                self.state.set_mode(GUIState.CMD)

            # all alphanum + special // backspace
            if c in range(32, 123) or c == KEY_BACKSPACE:
                self.state.update_search_str(c)

            # Enter
            if c == 10:  # enter: add topmost candlist item to playlist
                self.state.add_candidate(0)

            if c == curses.KEY_UP:
                self.state.history_up()

            if c == curses.KEY_DOWN:
                self.state.history_down()

            if c == curses.KEY_LEFT:
                self.state.gui_request("candlist_left")

            if c == curses.KEY_RIGHT:
                self.state.gui_request("candlist_right")
        #
        # CMD
        #
        elif self.state.mode == GUIState.CMD:

            if c == 27:  # ESC
                self.state.set_mode(GUIState.INPUT)

            if chr(c) == "m":
                self.state.selected_line = 0
                self.state.set_mode(GUIState.NAVIGATE_PLAYLIST)

            if chr(c) == "w":  # write out results
                self.state.mode = GUIState.WRITE
                self.state.exit_GUI = True

            if chr(c) == "p":  # play using some player
                self.state.mode = GUIState.PLAY
                self.state.exit_GUI = True

            if chr(c) == "q":  # quit without action
                self.state.exit_GUI = True

            if chr(c) == "r":  # reset playlist
                self.state.reset_state()

            # 0-9: select this from candidates
            if c in range(48, 58):
                idx = int(chr(c))
                self.state.add_candidate(idx - 1 if idx != 0 else 9)
                self.state.set_mode(GUIState.INPUT)

            # select all as list into one slot
            if chr(c) == "*":
                self.state.add_all_candidates()
                self.state.set_mode(GUIState.INPUT)

        #
        # PLAYLIST NAV & MOVE
        #
        elif (
            self.state.mode == GUIState.NAVIGATE_PLAYLIST
            or self.state.mode == GUIState.MOVE_PLAYLIST_ENTRIES
        ):

            # ESC: terminate without doing anything
            if c == 27:
                self.state.set_mode(GUIState.INPUT)
                self.state.selected_line = -1

            if chr(c) == "k":  # 259:  cursor UP
                self.state.playlist_cursor_up()

            if chr(c) == "j":  # cursor DOWN
                self.state.playlist_cursor_down()

            if chr(c) == "m":
                self.state.toggle_playlist_mode()

            if chr(c) == "d":
                self.state.remove_selected_line_from_playlist()
