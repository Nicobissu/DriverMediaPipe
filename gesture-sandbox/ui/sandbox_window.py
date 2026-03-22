import ctypes
import pygame
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, BG_COLOR,
    VIDEO_PANEL_WIDTH, LOG_PANEL_WIDTH,
    CAM_X_MIN, CAM_X_MAX, CAM_Y_MIN, CAM_Y_MAX,
    ACCEL_CURVE, ACCEL_GAIN,
)
from ui.video_panel import VideoPanel
from ui.gesture_log import GestureLog
from ui.status_panel import StatusPanel
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
        self.status_panel = StatusPanel(
            VIDEO_PANEL_WIDTH + LOG_PANEL_WIDTH, 0, desktop_w, WINDOW_HEIGHT
        )

        # Input driver
        self.input = InputDriver()

        # Right hand state
        self._fist_clicked = False
        self._pinch_clicked = False
        self._scroll_prev_y = None
        self._prev_cursor_x = SCREEN_W / 2
        self._prev_cursor_y = SCREEN_H / 2

        # Left hand state
        self._l_minimize_done = False
        self._l_close_done = False
        self._l_select_done = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True

    def _map_to_screen(self, gesture):
        """Map normalized hand coords to screen pixels with zone remap + acceleration.
        Webcam is mirrored, so moving hand right = x decreases in camera.
        We invert so cursor moves same direction as the hand."""
        d = gesture.data
        nx = d.get("smooth_x", d.get("x", 0.5))
        ny = d.get("smooth_y", d.get("y", 0.5))

        # Remap camera zone to 0-1 (no X invert — webcam already mirrors)
        rx = (nx - CAM_X_MIN) / (CAM_X_MAX - CAM_X_MIN)
        ry = (ny - CAM_Y_MIN) / (CAM_Y_MAX - CAM_Y_MIN)
        rx = max(0.0, min(1.0, rx))
        ry = max(0.0, min(1.0, ry))

        # Target position
        target_x = rx * SCREEN_W
        target_y = ry * SCREEN_H

        # Non-linear acceleration
        dx = target_x - self._prev_cursor_x
        dy = target_y - self._prev_cursor_y

        def accel(delta):
            sign = 1 if delta >= 0 else -1
            mag = abs(delta) / SCREEN_W
            return sign * (mag ** ACCEL_CURVE) * ACCEL_GAIN * SCREEN_W

        final_x = self._prev_cursor_x + accel(dx)
        final_y = self._prev_cursor_y + accel(dy)
        final_x = max(0, min(SCREEN_W - 1, final_x))
        final_y = max(0, min(SCREEN_H - 1, final_y))

        self._prev_cursor_x = final_x
        self._prev_cursor_y = final_y
        return int(final_x), int(final_y)

    def _apply_right(self, gesture):
        """Right hand: cursor, click, scroll, double click."""
        name = gesture.name

        if name == "R_CURSOR":
            sx, sy = self._map_to_screen(gesture)
            self.input.move_mouse(sx, sy)
            self._fist_clicked = False
            self._pinch_clicked = False

        elif name == "R_SCROLL":
            d = gesture.data
            ny = d.get("smooth_y", d.get("y", 0.5))
            if self._scroll_prev_y is None:
                self._scroll_prev_y = ny
            dy = ny - self._scroll_prev_y
            self._scroll_prev_y = ny
            if abs(dy) > 0.003:
                self.input.scroll(int(-dy * 3000))
            self._fist_clicked = False
            self._pinch_clicked = False

        elif name == "R_STANDBY":
            self._fist_clicked = False
            self._pinch_clicked = False
            self._scroll_prev_y = None

        elif name == "R_CLICK":
            if not self._fist_clicked:
                self.input.click()
                self._fist_clicked = True
            self._pinch_clicked = False
            self._scroll_prev_y = None

        elif name == "R_DOUBLE_CLICK":
            if not self._pinch_clicked:
                self.input.double_click()
                self._pinch_clicked = True
            self._fist_clicked = False
            self._scroll_prev_y = None

        else:
            self._fist_clicked = False
            self._pinch_clicked = False
            self._scroll_prev_y = None

    def _apply_left(self, gesture):
        """Left hand: window management."""
        name = gesture.name

        if name == "L_MINIMIZE":
            if not self._l_minimize_done:
                self.input.minimize_window()
                self._l_minimize_done = True
            self._l_close_done = False
            self._l_select_done = False

        elif name == "L_CLOSE":
            if not self._l_close_done:
                self.input.close_window()
                self._l_close_done = True
            self._l_minimize_done = False
            self._l_select_done = False

        elif name == "L_SELECT":
            if not self._l_select_done:
                self.input.focus_window_at_cursor()
                self._l_select_done = True
            self._l_minimize_done = False
            self._l_close_done = False

        else:
            self._l_minimize_done = False
            self._l_close_done = False
            self._l_select_done = False

    def _get_cursor_pos(self):
        pt = _POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def draw(self, bgr_frame, right_gesture, left_gesture, fps):
        self.screen.fill(BG_COLOR)

        # Apply right hand input
        self._apply_right(right_gesture)

        # Apply left hand commands
        self._apply_left(left_gesture)

        # Draw panels
        self.video_panel.draw(self.screen, bgr_frame, fps)

        # Log both hands
        self.gesture_log.log(right_gesture)
        if left_gesture.active:
            self.gesture_log.log(left_gesture)
        self.gesture_log.draw(self.screen, right_gesture)

        self.status_panel.draw(self.screen, right_gesture, left_gesture)

        pygame.display.flip()
        self.clock.tick(60)
