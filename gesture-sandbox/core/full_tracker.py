"""Full body tracker: pose (33 landmarks), hands (21 each), face (478 landmarks)."""

import os
import cv2
import mediapipe as mp

BaseOptions = mp.tasks.BaseOptions
RunningMode = mp.tasks.vision.RunningMode

PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions

HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions

FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions

MODEL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TrackingResult:
    """Container for all tracking data from a single frame."""
    def __init__(self):
        self.pose_landmarks = None          # list of 33 NormalizedLandmark
        self.pose_world_landmarks = None    # 3D world coordinates
        self.left_hand = None               # list of 21 NormalizedLandmark
        self.right_hand = None              # list of 21 NormalizedLandmark
        self.face_landmarks = None          # list of 478 NormalizedLandmark
        self.face_blendshapes = None        # facial expressions


class FullTracker:
    """Runs pose, hand, and face landmarkers on each frame."""

    # ── Pose landmark indices ──
    NOSE = 0
    LEFT_EYE_INNER, LEFT_EYE, LEFT_EYE_OUTER = 1, 2, 3
    RIGHT_EYE_INNER, RIGHT_EYE, RIGHT_EYE_OUTER = 4, 5, 6
    LEFT_EAR, RIGHT_EAR = 7, 8
    MOUTH_LEFT, MOUTH_RIGHT = 9, 10
    LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
    LEFT_ELBOW, RIGHT_ELBOW = 13, 14
    LEFT_WRIST, RIGHT_WRIST = 15, 16
    LEFT_PINKY, RIGHT_PINKY = 17, 18
    LEFT_INDEX, RIGHT_INDEX = 19, 20
    LEFT_THUMB, RIGHT_THUMB = 21, 22
    LEFT_HIP, RIGHT_HIP = 23, 24
    LEFT_KNEE, RIGHT_KNEE = 25, 26
    LEFT_ANKLE, RIGHT_ANKLE = 27, 28
    LEFT_HEEL, RIGHT_HEEL = 29, 30
    LEFT_FOOT_INDEX, RIGHT_FOOT_INDEX = 31, 32

    # Pose connections for drawing
    POSE_CONNECTIONS = [
        # Torso
        (11, 12), (11, 23), (12, 24), (23, 24),
        # Left arm
        (11, 13), (13, 15),
        # Right arm
        (12, 14), (14, 16),
        # Left hand (from pose)
        (15, 17), (15, 19), (15, 21),
        # Right hand (from pose)
        (16, 18), (16, 20), (16, 22),
        # Left leg
        (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
        # Right leg
        (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),
        # Face
        (0, 1), (1, 2), (2, 3), (3, 7),
        (0, 4), (4, 5), (5, 6), (6, 8),
        (9, 10),
    ]

    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (0, 9), (9, 10), (10, 11), (11, 12),
        (0, 13), (13, 14), (14, 15), (15, 16),
        (0, 17), (17, 18), (18, 19), (19, 20),
        (5, 9), (9, 13), (13, 17),
    ]

    def __init__(self):
        self._timestamp_ms = 0

        # Pose
        pose_path = os.path.join(MODEL_DIR, "pose_landmarker.task")
        self._pose = PoseLandmarker.create_from_options(PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=pose_path),
            running_mode=RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ))

        # Hands
        hand_path = os.path.join(MODEL_DIR, "hand_landmarker.task")
        self._hands = HandLandmarker.create_from_options(HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=hand_path),
            running_mode=RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ))

        # Face
        face_path = os.path.join(MODEL_DIR, "face_landmarker.task")
        self._face = FaceLandmarker.create_from_options(FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=face_path),
            running_mode=RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=True,
        ))

    def process(self, bgr_frame):
        """Process frame through all three landmarkers. Returns TrackingResult."""
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._timestamp_ms += 33

        result = TrackingResult()

        # Pose
        pose_result = self._pose.detect_for_video(mp_image, self._timestamp_ms)
        if pose_result.pose_landmarks:
            result.pose_landmarks = pose_result.pose_landmarks[0]
        if pose_result.pose_world_landmarks:
            result.pose_world_landmarks = pose_result.pose_world_landmarks[0]

        # Hands
        hand_result = self._hands.detect_for_video(mp_image, self._timestamp_ms)
        for i, hand_lm in enumerate(hand_result.hand_landmarks):
            if i < len(hand_result.handedness):
                label = hand_result.handedness[i][0].category_name
                # Mirrored: "Left" label = user's right hand
                if label == "Left":
                    result.right_hand = hand_lm
                else:
                    result.left_hand = hand_lm

        # Face
        face_result = self._face.detect_for_video(mp_image, self._timestamp_ms)
        if face_result.face_landmarks:
            result.face_landmarks = face_result.face_landmarks[0]
        if face_result.face_blendshapes:
            result.face_blendshapes = face_result.face_blendshapes[0]

        return result

    def draw(self, frame, result):
        """Draw all landmarks on the frame."""
        h, w = frame.shape[:2]

        # ── Pose skeleton ──
        if result.pose_landmarks:
            lm = result.pose_landmarks
            for start, end in self.POSE_CONNECTIONS:
                p1, p2 = lm[start], lm[end]
                x1, y1 = int(p1.x * w), int(p1.y * h)
                x2, y2 = int(p2.x * w), int(p2.y * h)
                cv2.line(frame, (x1, y1), (x2, y2), (0, 200, 180), 2)
            for p in lm:
                cx, cy = int(p.x * w), int(p.y * h)
                cv2.circle(frame, (cx, cy), 4, (0, 255, 200), -1)

        # ── Hands ──
        for hand_lm, color_line, color_dot in [
            (result.right_hand, (0, 180, 100), (0, 255, 128)),
            (result.left_hand, (180, 100, 0), (255, 150, 50)),
        ]:
            if hand_lm is None:
                continue
            for start, end in self.HAND_CONNECTIONS:
                p1, p2 = hand_lm[start], hand_lm[end]
                x1, y1 = int(p1.x * w), int(p1.y * h)
                x2, y2 = int(p2.x * w), int(p2.y * h)
                cv2.line(frame, (x1, y1), (x2, y2), color_line, 2)
            for p in hand_lm:
                cx, cy = int(p.x * w), int(p.y * h)
                cv2.circle(frame, (cx, cy), 3, color_dot, -1)

        # ── Face mesh ──
        if result.face_landmarks:
            for p in result.face_landmarks:
                cx, cy = int(p.x * w), int(p.y * h)
                cv2.circle(frame, (cx, cy), 1, (200, 180, 255), -1)

        # ── Face blendshapes (expressions) ──
        if result.face_blendshapes:
            y_pos = 30
            # Show top expressions with highest score
            shapes = sorted(result.face_blendshapes,
                          key=lambda s: s.score, reverse=True)
            for bs in shapes[:8]:
                if bs.score > 0.1 and bs.category_name != "_neutral":
                    bar_w = int(bs.score * 150)
                    cv2.rectangle(frame, (w - 220, y_pos - 12),
                                (w - 220 + bar_w, y_pos), (100, 200, 255), -1)
                    cv2.putText(frame, f"{bs.category_name}: {bs.score:.2f}",
                              (w - 220, y_pos - 2),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
                    y_pos += 18

    def release(self):
        self._pose.close()
        self._hands.close()
        self._face.close()
