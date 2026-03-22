"""3D objects that can be placed and manipulated in the workspace."""

import math
from OpenGL.GL import *
from OpenGL.GLU import *


class SceneObject:
    """Base class for all objects in the 3D scene."""

    _id_counter = 0

    def __init__(self, pos=(0, 0, 0)):
        SceneObject._id_counter += 1
        self.id = SceneObject._id_counter
        self.pos = list(pos)        # [x, y, z]
        self.rot = [0.0, 0.0, 0.0]  # [rx, ry, rz] degrees
        self.scale = [1.0, 1.0, 1.0]
        self.color = [0.3, 0.6, 0.9, 0.9]  # RGBA
        self.selected = False
        self.hovered = False

    def draw(self):
        glPushMatrix()
        glTranslatef(*self.pos)
        glRotatef(self.rot[1], 0, 1, 0)
        glRotatef(self.rot[0], 1, 0, 0)
        glRotatef(self.rot[2], 0, 0, 1)
        glScalef(*self.scale)

        if self.selected:
            c = [min(1.0, self.color[0] + 0.3),
                 min(1.0, self.color[1] + 0.3),
                 min(1.0, self.color[2] + 0.3), 1.0]
        elif self.hovered:
            c = [min(1.0, self.color[0] + 0.15),
                 min(1.0, self.color[1] + 0.15),
                 min(1.0, self.color[2] + 0.15), 1.0]
        else:
            c = self.color

        glColor4f(*c)
        self._draw_shape()

        # Selection outline
        if self.selected:
            glColor4f(1.0, 1.0, 0.3, 1.0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glLineWidth(2.0)
            self._draw_shape()
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glLineWidth(1.0)

        glPopMatrix()

    def _draw_shape(self):
        raise NotImplementedError


class Cube(SceneObject):
    def __init__(self, pos=(0, 0.5, 0), size=1.0):
        super().__init__(pos)
        self.size = size

    def _draw_shape(self):
        h = self.size / 2
        # 6 faces
        glBegin(GL_QUADS)
        # Top
        glNormal3f(0, 1, 0)
        glVertex3f(-h, h, -h); glVertex3f(-h, h, h)
        glVertex3f(h, h, h); glVertex3f(h, h, -h)
        # Bottom
        glNormal3f(0, -1, 0)
        glVertex3f(-h, -h, -h); glVertex3f(h, -h, -h)
        glVertex3f(h, -h, h); glVertex3f(-h, -h, h)
        # Front
        glNormal3f(0, 0, 1)
        glVertex3f(-h, -h, h); glVertex3f(h, -h, h)
        glVertex3f(h, h, h); glVertex3f(-h, h, h)
        # Back
        glNormal3f(0, 0, -1)
        glVertex3f(-h, -h, -h); glVertex3f(-h, h, -h)
        glVertex3f(h, h, -h); glVertex3f(h, -h, -h)
        # Left
        glNormal3f(-1, 0, 0)
        glVertex3f(-h, -h, -h); glVertex3f(-h, -h, h)
        glVertex3f(-h, h, h); glVertex3f(-h, h, -h)
        # Right
        glNormal3f(1, 0, 0)
        glVertex3f(h, -h, -h); glVertex3f(h, h, -h)
        glVertex3f(h, h, h); glVertex3f(h, -h, h)
        glEnd()


class Sphere(SceneObject):
    def __init__(self, pos=(0, 0.5, 0), radius=0.5):
        super().__init__(pos)
        self.radius = radius
        self._quadric = gluNewQuadric()
        gluQuadricNormals(self._quadric, GLU_SMOOTH)

    def _draw_shape(self):
        gluSphere(self._quadric, self.radius, 24, 16)


class Plane(SceneObject):
    """A flat rectangular plane (like a note/card)."""

    def __init__(self, pos=(0, 1, 0), width=2.0, height=1.5):
        super().__init__(pos)
        self.width = width
        self.height = height
        self.color = [0.95, 0.92, 0.8, 0.95]  # paper-like

    def _draw_shape(self):
        w, h = self.width / 2, self.height / 2
        glBegin(GL_QUADS)
        glNormal3f(0, 0, 1)
        glVertex3f(-w, -h, 0)
        glVertex3f(w, -h, 0)
        glVertex3f(w, h, 0)
        glVertex3f(-w, h, 0)
        glEnd()
        # Back face
        glBegin(GL_QUADS)
        glNormal3f(0, 0, -1)
        glVertex3f(-w, -h, -0.01)
        glVertex3f(-w, h, -0.01)
        glVertex3f(w, h, -0.01)
        glVertex3f(w, -h, -0.01)
        glEnd()
