import threading
import time
import tkinter as tk


class StopWatch:
    """
    Context manager for stopping duration of tasks.
    """

    def __init__(self, info):
        self.info = info

    def __enter__(self):
        self.tic = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        dt = time.time() - self.tic
        print(f"{self.info}: {dt:0.3f}s")


# Create a full-screen black window
def blank_screen(top: bool = False):
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    if top:
        root.attributes('-topmost', True)  # Keep the window on top
    root.config(bg='black')
    root.mainloop()


# Function to start the Tkinter window in a separate thread
def start_blank_screen(top: bool = False):
    screen_thread = threading.Thread(target=blank_screen, args=(top,))
    screen_thread.daemon = True  # Ensure the thread exits when the main program exits
    screen_thread.start()