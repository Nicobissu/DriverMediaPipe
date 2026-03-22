import os
import cv2
import numpy as np
import mediapipe as mp
from config import MP_MAX_HANDS, MP_DETECTION_CONFIDENCE, MP_TRACKING_CONFIDENCE

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode
HandConnections = mp.tasks.vision.HandLandmarksConnections

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "hand_landmarker.task")


class HandTracker:
    """Wraps MediaPipe HandLandmarker (Tasks API). Processes BGR frames, returns hand data."""

    # MediaPipe landmark indices
    WRIST = 0
    THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
    INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
    RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
    PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

    FINGER_TIPS = [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
    FINGER_PIPS = [THUMB_IP, INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP]
    FINGER_MCPS = [THUMB_MCP, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP]

    # Connection pairs for drawing (start_idx, end_idx)
    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),       # thumb
        (0, 5), (5, 6), (6, 7), (7, 8),       # index
        (0, 9), (9, 10), (10, 11), (11, 12),  # middle
        (0, 13), (13, 14), (14, 15), (15, 16),# ring
        (0, 17), (17, 18), (18, 19), (19, 20),# pinky
        (5, 9), (9, 13), (13, 17),             # palm
    ]

    def __init__(self):
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=RunningMode.VIDEO,
            num_hands=MP_MAX_HANDS,
            min_hand_detection_confidence=MP_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=MP_DETECTION_CONFIDENCE,
            min_tracking_confidence=MP_TRACKING_CONFIDENCE,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        self._timestamp_ms = 0

    def process(self, bgr_frame):
        """Process a BGR frame. Returns list of hand landmark lists (normalized coords)."""
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._timestamp_ms += 33  # ~30fps increment
        result = self._landmarker.detect_for_video(mp_image, self._timestamp_ms)
        return result.hand_landmarks  # list of list of NormalizedLandmark

    def draw_landmarks(self, bgr_frame, hands_landmarks):
        """Draw landmarks + connections on the frame (in-place)."""
        h, w = bgr_frame.shape[:2]
        for landmarks in hands_landmarks:
            # Draw connections
            for start_idx, end_idx in self.HAND_CONNECTIONS:
                p1 = landmarks[start_idx]
                p2 = landmarks[end_idx]
                x1, y1 = int(p1.x * w), int(p1.y * h)
                x2, y2 = int(p2.x * w), int(p2.y * h)
                cv2.line(bgr_frame, (x1, y1), (x2, y2), (0, 180, 100), 2)
            # Draw landmarks
            for lm in landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(bgr_frame, (cx, cy), 4, (0, 255, 128), -1)

    def release(self):
        self._landmarker.close()
