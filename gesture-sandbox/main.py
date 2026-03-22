"""Gesture Sandbox — webcam hand gesture detection with OpenCV UI."""

import sys
import os
import cv2
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.camera import Camera
from core.hand_tracker import HandTracker
from core.gesture_engine import GestureEngine
from core.input_driver import InputDriver, SCREEN_W, SCREEN_H
from gestures.base import GestureResult
from config import (
    CAM_X_MIN, CAM_X_MAX, CAM_Y_MIN, CAM_Y_MAX,
    PINCH_ACTIVATE_DIST,
)


class GestureDriver:
    def __init__(self):
        self.camera = Camera()
        self.tracker = HandTracker()
        self.engine = GestureEngine()
        self.input = InputDriver()

        # Cursor state
        self.prev_cx = SCREEN_W / 2
        self.prev_cy = SCREEN_H / 2
        self.smooth = 0.35  # lower = smoother but laggier

        # Debounce
        self.fist_clicked = False
        self.pinch_clicked = False
        self.scroll_prev_y = None
        self.l_minimize_done = False
        self.l_close_done = False
        self.l_select_done = False

        # FPS
        self.fps = 0
        self._fps_time = time.time()
        self._fps_count = 0

    def _map_to_screen(self, gesture):
        d = gesture.data
        nx = d.get("smooth_x", d.get("x", 0.5))
        ny = d.get("smooth_y", d.get("y", 0.5))

        # Remap camera zone to 0..1
        rx = (nx - CAM_X_MIN) / (CAM_X_MAX - CAM_X_MIN)
        ry = (ny - CAM_Y_MIN) / (CAM_Y_MAX - CAM_Y_MIN)
        rx = max(0.0, min(1.0, rx))
        ry = max(0.0, min(1.0, ry))

        target_x = rx * SCREEN_W
        target_y = ry * SCREEN_H

        # Smooth cursor
        self.prev_cx += (target_x - self.prev_cx) * self.smooth
        self.prev_cy += (target_y - self.prev_cy) * self.smooth
        self.prev_cx = max(0, min(SCREEN_W - 1, self.prev_cx))
        self.prev_cy = max(0, min(SCREEN_H - 1, self.prev_cy))

        return int(self.prev_cx), int(self.prev_cy)

    def _apply_right(self, g):
        name = g.name
        if name == "R_CURSOR":
            sx, sy = self._map_to_screen(g)
            self.input.move_mouse(sx, sy)
            self.fist_clicked = False
            self.pinch_clicked = False
        elif name == "R_SCROLL":
            ny = g.data.get("smooth_y", g.data.get("y", 0.5))
            if self.scroll_prev_y is None:
                self.scroll_prev_y = ny
            dy = ny - self.scroll_prev_y
            self.scroll_prev_y = ny
            if abs(dy) > 0.003:
                self.input.scroll(int(-dy * 3000))
            self.fist_clicked = False
            self.pinch_clicked = False
        elif name == "R_STANDBY":
            self.fist_clicked = False
            self.pinch_clicked = False
            self.scroll_prev_y = None
        elif name == "R_CLICK":
            if not self.fist_clicked:
                self.input.click()
                self.fist_clicked = True
            self.pinch_clicked = False
            self.scroll_prev_y = None
        elif name == "R_DOUBLE_CLICK":
            if not self.pinch_clicked:
                self.input.double_click()
                self.pinch_clicked = True
            self.fist_clicked = False
            self.scroll_prev_y = None
        else:
            self.fist_clicked = False
            self.pinch_clicked = False
            self.scroll_prev_y = None

    def _apply_left(self, g):
        name = g.name
        if name == "L_MINIMIZE":
            if not self.l_minimize_done:
                self.input.minimize_window()
                self.l_minimize_done = True
            self.l_close_done = False
            self.l_select_done = False
        elif name == "L_CLOSE":
            if not self.l_close_done:
                self.input.close_window()
                self.l_close_done = True
            self.l_minimize_done = False
            self.l_select_done = False
        elif name == "L_SELECT":
            if not self.l_select_done:
                self.input.focus_window_at_cursor()
                self.l_select_done = True
            self.l_minimize_done = False
            self.l_close_done = False
        else:
            self.l_minimize_done = False
            self.l_close_done = False
            self.l_select_done = False

    def _draw_hud(self, frame, right, left):
        """Draw gesture info overlay on the camera frame."""
        h, w = frame.shape[:2]

        # FPS
        self._fps_count += 1
        now = time.time()
        if now - self._fps_time >= 0.5:
            self.fps = self._fps_count / (now - self._fps_time)
            self._fps_count = 0
            self._fps_time = now
        cv2.putText(frame, f"FPS: {self.fps:.0f}", (10, 28),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 128), 2)

        # Right hand gesture
        rn = right.name if right.active else "---"
        color_r = (0, 255, 128)
        cv2.putText(frame, f"R: {rn}", (10, 60),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_r, 2)

        # Right fingers
        if right.active and "fingers" in right.data:
            y = 90
            for fname in ["thumb", "index", "middle", "ring", "pinky"]:
                state = right.data["fingers"].get(fname, False)
                icon = "UP" if state else "--"
                c = (0, 200, 100) if state else (80, 80, 80)
                cv2.putText(frame, f"  {fname}: {icon}", (10, y),
                             cv2.FONT_HERSHEY_SIMPLEX, 0.45, c, 1)
                y += 18

        # Left hand gesture
        ln = left.name if left.active else "---"
        color_l = (255, 150, 50)
        cv2.putText(frame, f"L: {ln}", (w - 200, 60),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_l, 2)

        # Controls legend at bottom
        legend = [
            "Idx+Mid=Cursor  Fist=Click  Thumb~Idx=DblClick",
            "Idx+Mid+Ring=Scroll  Index=Standby",
        ]
        for i, line in enumerate(legend):
            cv2.putText(frame, line, (10, h - 30 + i * 20),
                         cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)

    def run(self):
        print("Gesture Driver running — press ESC to quit")
        cv2.namedWindow("Gesture Driver", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Gesture Driver", 800, 500)

        while True:
            ok, frame = self.camera.read()
            if not ok:
                continue

            # Detect hands
            hands, all_landmarks = self.tracker.process(frame)
            self.tracker.draw_landmarks(frame, all_landmarks, hands)

            # Gestures
            frame_shape = (frame.shape[0], frame.shape[1])
            right, left = self.engine.update(hands, frame_shape)

            # Apply input
            self._apply_right(right)
            self._apply_left(left)

            # Draw HUD
            self._draw_hud(frame, right, left)

            # Show
            cv2.imshow("Gesture Driver", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break

        self.camera.release()
        self.tracker.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        GestureDriver().run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nERROR: {e}")
        input("Press Enter to exit...")
