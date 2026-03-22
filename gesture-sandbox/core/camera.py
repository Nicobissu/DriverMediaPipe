import cv2
from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS


class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")

    def read(self):
        """Return (success, bgr_frame). Frame is flipped horizontally (mirror)."""
        ok, frame = self.cap.read()
        if ok:
            frame = cv2.flip(frame, 1)
        return ok, frame

    def release(self):
        self.cap.release()
