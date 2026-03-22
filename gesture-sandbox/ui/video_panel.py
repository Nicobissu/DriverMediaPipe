import cv2
import numpy as np
import pygame
from config import VIDEO_PANEL_WIDTH, WINDOW_HEIGHT, PANEL_BG


class VideoPanel:
    """Left panel: camera feed with landmark overlay."""

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, surface, bgr_frame, fps):
        # Convert BGR → RGB, resize to fit panel
        if bgr_frame is not None:
            rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            # Fit to panel keeping aspect ratio
            fh, fw = rgb.shape[:2]
            scale = min(self.rect.width / fw, self.rect.height / fh)
            new_w, new_h = int(fw * scale), int(fh * scale)
            rgb = cv2.resize(rgb, (new_w, new_h))
            # Transpose for pygame (height, width, channels) → Surface
            frame_surface = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))
            # Center in panel
            ox = self.rect.x + (self.rect.width - new_w) // 2
            oy = self.rect.y + (self.rect.height - new_h) // 2
            surface.blit(frame_surface, (ox, oy))
        else:
            pygame.draw.rect(surface, PANEL_BG, self.rect)

        # FPS overlay
        font = pygame.font.SysFont("consolas", 16)
        fps_text = font.render(f"FPS: {fps:.1f}", True, (0, 255, 128))
        surface.blit(fps_text, (self.rect.x + 8, self.rect.y + 8))
