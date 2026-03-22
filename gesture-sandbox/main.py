"""Gesture Sandbox — webcam hand gesture detection with MediaPipe + PyGame."""

import sys
import os

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.camera import Camera
from core.hand_tracker import HandTracker
from core.gesture_engine import GestureEngine
from ui.sandbox_window import SandboxWindow
from utils.fps_counter import FPSCounter


def main():
    camera = Camera()
    tracker = HandTracker()
    engine = GestureEngine()
    window = SandboxWindow()
    fps_counter = FPSCounter()

    print("Gesture Sandbox running — press ESC or close window to quit")

    try:
        running = True
        while running:
            running = window.handle_events()

            ok, frame = camera.read()
            if not ok:
                continue

            # Detect hands (returns dict with 'right'/'left' + all landmarks list)
            hands, all_landmarks = tracker.process(frame)

            # Draw landmarks on frame (color-coded per hand)
            tracker.draw_landmarks(frame, all_landmarks, hands)

            # Run gesture engine (processes both hands)
            frame_shape = (frame.shape[0], frame.shape[1])  # (h, w)
            right_gesture, left_gesture = engine.update(hands, frame_shape)

            # Update FPS
            fps_counter.tick()

            # Render
            window.draw(frame, right_gesture, left_gesture, fps_counter.fps)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nERROR: {e}")
        input("Press Enter to exit...")
    finally:
        camera.release()
        tracker.release()
        import pygame
        pygame.quit()


if __name__ == "__main__":
    main()
