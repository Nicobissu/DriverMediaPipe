import time
from config import FPS_UPDATE_INTERVAL


class FPSCounter:
    def __init__(self):
        self._frame_count = 0
        self._start_time = time.perf_counter()
        self.fps = 0.0

    def tick(self):
        self._frame_count += 1
        elapsed = time.perf_counter() - self._start_time
        if elapsed >= FPS_UPDATE_INTERVAL:
            self.fps = self._frame_count / elapsed
            self._frame_count = 0
            self._start_time = time.perf_counter()
