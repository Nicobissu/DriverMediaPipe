"""Infinite-looking grid floor for the 3D workspace."""

from OpenGL.GL import *


def draw_grid(size=20, step=1.0):
    """Draw a flat grid on the XZ plane at y=0."""
    glBegin(GL_LINES)
    half = size * step
    i = -size
    while i <= size:
        x = i * step
        # Lines along Z
        if i == 0:
            glColor4f(0.5, 0.5, 0.5, 0.8)
        else:
            glColor4f(0.25, 0.25, 0.3, 0.4)
        glVertex3f(x, 0, -half)
        glVertex3f(x, 0, half)
        # Lines along X
        glVertex3f(-half, 0, x)
        glVertex3f(half, 0, x)
        i += 1
    glEnd()

    # Draw axis indicators
    glLineWidth(2.0)
    glBegin(GL_LINES)
    # X axis — red
    glColor4f(0.8, 0.2, 0.2, 1.0)
    glVertex3f(0, 0.01, 0)
    glVertex3f(3, 0.01, 0)
    # Y axis — green
    glColor4f(0.2, 0.8, 0.2, 1.0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 3, 0)
    # Z axis — blue
    glColor4f(0.2, 0.2, 0.8, 1.0)
    glVertex3f(0, 0.01, 0)
    glVertex3f(0, 0.01, 3)
    glEnd()
    glLineWidth(1.0)
