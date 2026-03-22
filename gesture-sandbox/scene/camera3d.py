"""Orbital camera for the 3D workspace."""

import math
from OpenGL.GL import *
from OpenGL.GLU import *


class Camera3D:
    def __init__(self):
        self.distance = 8.0       # distance from target
        self.yaw = 45.0           # horizontal angle (degrees)
        self.pitch = 30.0         # vertical angle (degrees)
        self.target = [0.0, 0.0, 0.0]  # look-at point
        self.min_pitch = -85.0
        self.max_pitch = 85.0
        self.min_dist = 2.0
        self.max_dist = 50.0

    def orbit(self, dx, dy):
        """Rotate camera around target."""
        self.yaw += dx * 0.3
        self.pitch += dy * 0.3
        self.pitch = max(self.min_pitch, min(self.max_pitch, self.pitch))

    def pan(self, dx, dy):
        """Pan the target point."""
        # Move perpendicular to view direction
        rad_yaw = math.radians(self.yaw)
        speed = self.distance * 0.002
        self.target[0] += (-dx * math.cos(rad_yaw) + dy * math.sin(rad_yaw) * math.sin(math.radians(self.pitch))) * speed
        self.target[1] += dy * math.cos(math.radians(self.pitch)) * speed
        self.target[2] += (dx * math.sin(rad_yaw) + dy * math.cos(rad_yaw) * math.sin(math.radians(self.pitch))) * speed

    def zoom(self, amount):
        """Zoom in/out."""
        self.distance *= (1.0 - amount * 0.1)
        self.distance = max(self.min_dist, min(self.max_dist, self.distance))

    def get_position(self):
        """Calculate camera position from spherical coords."""
        rad_yaw = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)
        x = self.target[0] + self.distance * math.cos(rad_pitch) * math.sin(rad_yaw)
        y = self.target[1] + self.distance * math.sin(rad_pitch)
        z = self.target[2] + self.distance * math.cos(rad_pitch) * math.cos(rad_yaw)
        return x, y, z

    def apply(self):
        """Set the OpenGL modelview matrix."""
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        pos = self.get_position()
        gluLookAt(pos[0], pos[1], pos[2],
                  self.target[0], self.target[1], self.target[2],
                  0, 1, 0)
