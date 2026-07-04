# platform specific setting here
import platform
import os

if platform.system() == "Linux":
    KEY_BACKSPACE = 263
    CMD = "mplayer -fs -really-quiet -playlist"
else:
    KEY_BACKSPACE = 8

    exec_list = [
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    ]

    vlc_exec = None
    for fpath in exec_list:
        if os.path.exists(fpath):
            vlc_exec = fpath
            break

    if vlc_exec is None:
        raise FileNotFoundError("Cannot find vlc executable")

    # CMD = f'"{vlc_exec}" --fullscreen --intf rc --rc-host 127.0.0.1:44500'
    CMD = f'"{vlc_exec}" --file-caching=10000 --network-caching=10000 --intf ' \
          'rc --rc-host 127.0.0.1:44500 --no-video-deco --no-embedded-video --video-x=0 --video-y=0'

    print(f"CMD: {CMD}")
