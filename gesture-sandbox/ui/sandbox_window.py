import ctypes
import pygame
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, BG_COLOR,
    VIDEO_PANEL_WIDTH, LOG_PANEL_WIDTH,
)
from ui.video_panel import VideoPanel
from ui.gesture_log import GestureLog
from ui.desktop_panel import DesktopPanel
from core.input_driver import InputDriver, SCREEN_W, SCREEN_H


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class SandboxWindow:
    """Main window with three panels: video | log | desktop mirror."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Gesture Driver")
        self.clock = pygame.time.Clock()

        # Layout
        desktop_w = WINDOW_WIDTH - VIDEO_PANEL_WIDTH - LOG_PANEL_WIDTH
        self.video_panel = VideoPanel(0, 0, VIDEO_PANEL_WIDTH, WINDOW_HEIGHT)
        self.gesture_log = GestureLog(VIDEO_PANEL_WIDTH, 0, LOG_PANEL_WIDTH, WINDOW_HEIGHT)
        self.desktop_panel = DesktopPanel(
            VIDEO_PANEL_WIDTH + LOG_PANEL_WIDTH, 0, desktop_w, WINDOW_HEIGHT
        )

        # Input driver
        self.input = InputDriver()

        # Debounce state
        self._fist_clicked = False
        self._pinch_clicked = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True

    def _map_to_screen(self, gesture):
        """Map normalized hand coords (0-1) to screen pixels."""
        d = gesture.data
        nx = d.get("smooth_x", d.get("x", 0.5))
        ny = d.get("smooth_y", d.get("y", 0.5))
        return int(nx * SCREEN_W), int(ny * SCREEN_H)

    def _apply_input(self, gesture):
        """Map gestures to real input actions."""
        name = gesture.name

        if name == "CURSOR":
            # Index + middle → move cursor
            sx, sy = self._map_to_screen(gesture)
            self.input.move_mouse(sx, sy)
            self._fist_clicked = False
            self._pinch_clicked = False

        elif name == "THREE":
            # Index + middle + ring → scroll
            d = gesture.data
            ny = d.get("smooth_y", d.get("y", 0.5))
            if not hasattr(self, "_scroll_prev_y"):
                self._scroll_prev_y = ny
            dy = ny - self._scroll_prev_y
            self._scroll_prev_y = ny
            if abs(dy) > 0.003:
                self.input.scroll(int(-dy * 3000))
            self._fist_clicked = False
            self._pinch_clicked = False

        elif name == "STANDBY":
            # Only index → do nothing, cursor stays in place
            self._fist_clicked = False
            self._pinch_clicked = False
            self._scroll_prev_y = None

        elif name == "FIST":
            # All closed → single click (once)
            if not self._fist_clicked:
                self.input.click()
                self._fist_clicked = True
            self._pinch_clicked = False
            self._scroll_prev_y = None

        elif name == "PINCH":
            # Thumb + index touching → double click (once)
            if not self._pinch_clicked:
                self.input.double_click()
                self._pinch_clicked = True
            self._fist_clicked = False
            self._scroll_prev_y = None

        else:
            # PALM, IDLE, other → reset
            self._fist_clicked = False
            self._pinch_clicked = False
            self._scroll_prev_y = None

    def _get_cursor_pos(self):
        pt = _POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def draw(self, bgr_frame, gesture_result, fps):
        self.screen.fill(BG_COLOR)

        # Apply real input
        self._apply_input(gesture_result)

        # Cursor position for desktop overlay
        if gesture_result.active and "x" in gesture_result.data:
            sx, sy = self._map_to_screen(gesture_result)
        else:
            sx, sy = self._get_cursor_pos()

        # Draw panels
        self.video_panel.draw(self.screen, bgr_frame, fps)
        self.gesture_log.log(gesture_result)
        self.gesture_log.draw(self.screen, gesture_result)
        self.desktop_panel.update(gesture_result, sx, sy)
        self.desktop_panel.draw(self.screen)

        pygame.display.flip()
        self.clock.tick(60)
