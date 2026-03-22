import cv2
import numpy as np
import pygame
from config import PANEL_BG


class VideoPanel:
    """Left panel: camera feed with landmark overlay."""

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self._font = None

    def draw(self, surface, bgr_frame, fps):
        if self._font is None:
            self._font = pygame.font.SysFont("consolas", 16)

        if bgr_frame is not None:
            rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            fh, fw = rgb.shape[:2]
            scale = min(self.rect.width / fw, self.rect.height / fh)
            new_w, new_h = int(fw * scale), int(fh * scale)
            rgb = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
            frame_surface = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))
            ox = self.rect.x + (self.rect.width - new_w) // 2
            oy = self.rect.y + (self.rect.height - new_h) // 2
            surface.blit(frame_surface, (ox, oy))
        else:
            pygame.draw.rect(surface, PANEL_BG, self.rect)

        fps_text = self._font.render(f"FPS: {fps:.1f}", True, (0, 255, 128))
        surface.blit(fps_text, (self.rect.x + 8, self.rect.y + 8))
