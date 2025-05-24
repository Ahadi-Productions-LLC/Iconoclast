import time

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer, pyqtSignal

from app import constants
from app import counters
from app.counters import GenericAnimCounter
from app.utilities.utils import frames2ms

from app.editor.settings import MainSettingsController

class Timer(QWidget):
    tick_elapsed = pyqtSignal()

    def __init__(self, fps=60):
        super().__init__()
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.tick)
        timer_speed = int(1000/float(fps))
        self.main_timer.setInterval(timer_speed)
        self.main_timer.start()

        self.autosave_timer = QTimer()
        autosave_time = MainSettingsController().get_autosave_time(5)
        self.autosave_timer.setInterval(int(autosave_time * 60 * 1000))
        self.autosave_timer.start()

        self.passive_counter = GenericAnimCounter.from_frames_back_and_forth([16, 2, 16], frame_duration=constants.FRAMERATE * 2, get_time=lambda: time.time() * 1000)
        self.active_counter = GenericAnimCounter.from_frames_back_and_forth([10, 2, 10], frame_duration=constants.FRAMERATE * 2, get_time=lambda: time.time() * 1000)
        self.move_sprite_counter = GenericAnimCounter.from_frames([6, 3, 6, 3], frame_duration=constants.FRAMERATE * 2, get_time=lambda: time.time() * 1000)

    def tick(self):
        self.tick_elapsed.emit()

    def start(self):
        self.main_timer.start()
        self.autosave_timer.start()

    def start_for_editor(self):
        self.main_timer.start()

    def stop(self):
        self.main_timer.stop()
        self.autosave_timer.stop()

    def stop_for_editor(self):
        self.main_timer.stop()

TIMER = None
def get_timer():
    global TIMER
    if not TIMER:
        TIMER = Timer(constants.FPS//2)
    return TIMER
