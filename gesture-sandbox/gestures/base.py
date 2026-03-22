from dataclasses import dataclass, field
from typing import Any


@dataclass
class GestureResult:
    name: str
    confidence: float  # 0.0 – 1.0
    active: bool
    data: dict = field(default_factory=dict)  # gesture-specific payload


class Gesture:
    """Base class for all gesture detectors."""

    NAME = "unknown"

    def detect(self, hands, frame_shape) -> GestureResult:
        """
        Analyse hand landmarks and return a GestureResult.

        Args:
            hands: list of landmark lists (each has 21 normalized landmarks)
            frame_shape: (height, width) of the camera frame
        """
        raise NotImplementedError
