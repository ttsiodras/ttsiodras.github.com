#!/usr/bin/env python
"""
A naive simulator of gravity, in only 200 commented lines of Python code.
Coded by Thanassis Tsiodras, during a 2010 summer night...
Blog post: https://www.thanassis.space/gravity.html

Well, I've always been fascinated by space - ever since I read 'The Family of
the Sun', when I was young. And I always wanted to simulate what I've read
about Newton's gravity law, and see what happens in... a universe of my own
making...

So here's what I did: The following code 'sprays' some 'particles' randomly,
inside a 900x600 window (the values are below, change them at will).
Afterwards, it applies a very simple set of laws:

- Gravity, inversely proportional to the square of the distance,
  and linearly proportional to the product of the two masses
- Elastic collissions of two objects if they are close enough to
  touch: a merged object is then created, that maintains the
  momentum (mass*velocity) and the mass of the two merged ones.

The results... I let you decide :-)

Use the numeric keypad's +/- to zoom in/out.

Released under the GPL.
"""

import math
import pygame as pg
import random

# The window size
WIDTH, HEIGHT = 900, 600
WIDTHD2, HEIGHTD2 = WIDTH/2., HEIGHT/2.
# The number of simulated particles
PARTICLES = 200
# The density of the particles - used to calculate their mass
# from their volume (i.e. via their radius)
DENSITY = 0.001
# The gravity coefficient.
# It's my universe, I can pick whatever I want.
GRAVITYSTRENGTH = 1.e4


class Particle:
    def __init__(self):
        # Position
        self._x = float(random.randint(0, WIDTH))
        self._y = float(random.randint(0, HEIGHT))
        # Speed
        self._vx = 0.
        self._vy = 0.
        # Radius
        self._radius = 1.5
        # Use density to calculate mass from radius
        self.setMassFromRadius()
        # When two particles are close enough to touch: - _merged will be set
        # to True for the lighter one - it will no longer be simulated, since
        # its mass will be added to the larger one, and its momentum
        # (mass*velocity) will be merged to the larger one's (see code for
        # merging particles below, in main loop)
        self._merged = False

    def resetAccel(self):
        # Acceleration, set to 0 in each "calculate total force" loop
        self._ax = 0.0
        self._ay = 0.0

    def addAccel(self, particle):
        # Calculate the acceleration contribution from another particle
        dx = particle._x - self._x
        dy = particle._y - self._y
        dsq = dx*dx + dy*dy  # distance squared
        dr = math.sqrt(dsq)  # distance
        force = GRAVITYSTRENGTH*self._mass*particle._mass/dsq if dsq>1e-10 else 0.
        # Accumulate acceleration...
        self._ax += force*dx/dr
        self._ay += force*dy/dr

    def updatePos(self):
        # Afrer "addAccel" has been called to account for all other particles,
        # update my position and my speed...
        self._x += self._vx
        self._y += self._vy
        self._vx += self._ax
        self._vy += self._ay
        self.resetAccel()  # prepare for next round

    def setMassFromRadius(self):
        # The volume is (4/3)*Pi*(r^3), so...
        self._mass = DENSITY * 4. * math.pi * (self._radius**3.)/3.

    def setRadiusFromMass(self):
        # Reversing the previous formula, to calculate radius from mass (used
        # after merging of two particles - mass is added, and new radius is
        # calculated from this formula)
        self._radius = (3.*self._mass/(DENSITY * 4.*math.pi))**(0.3333)


def main():
    pg.init()
    win=pg.display.set_mode((WIDTH, HEIGHT))

    # And God said: Let there be lights in the firmament of the heavens...
    particles = []
    keysPressed = {pg.K_KP_MINUS: False, pg.K_KP_PLUS: False, pg.K_ESCAPE: False}
    for i in xrange(0, PARTICLES):
        particles.append(Particle())

    def particlesTouch(p1, p2):
        dx = p1._x - p2._x
        dy = p1._y - p2._y
        dsq = dx*dx + dy*dy
        dr = math.sqrt(dsq)
        return dr<=(p1._radius + p2._radius)

    sun = None
    #sun = Particle()    # Uncomment this section to play with a sun :-)
    #sun._x, sun._y = WIDTHD2, HEIGHTD2
    #sun._mass *= 1000
    #sun.setRadiusFromMass()
    #particles.append(sun)
    #for p in particles[:-1]:
    #    if particlesTouch(p, sun):
    #        p._merged = True

    # Zoom factor, changed at runtime via the '+' and '-' numeric keypad keys
    zoom = 1.0

    while True:
        pg.display.flip()
        win.fill((0, 0, 0))
        win.lock()
        for p in particles:
            if not p._merged:  # for those that have not been merged, draw a
                # circle based on their radius, but take zoom factor into account
                pg.draw.circle(win, (255, 255, 255),
                    (int(WIDTHD2+zoom*WIDTHD2*(p._x-WIDTHD2)/WIDTHD2),
                     int(HEIGHTD2+zoom*HEIGHTD2*(p._y-HEIGHTD2)/HEIGHTD2)),
                     int(p._radius*zoom), 0)
        win.unlock()
        while True:
            # Update the keysPressed state:
            evt = pg.event.poll()
            if evt.type == pg.NOEVENT:
                break
            elif evt.type in [pg.KEYDOWN, pg.KEYUP]:
                keysPressed[evt.key] = evt.type == pg.KEYDOWN

        # Update all particles' positions and speeds:
        for p1 in particles:
            if p1._merged or p1 is sun:
                continue
            # Calculate the contributions of all the others to its acceleration
            # (via the gravity force)
            p1.resetAccel()
            for p2 in particles:
                if p1 is p2 or p2._merged:
                    continue  # ignore ourselves and merged particles
                p1.addAccel(p2)
            p1.updatePos()

        # See if we should merge the ones that are close enough to touch,
        # using elastic collisions (conservation of total momentum)
        for p1 in particles:
            if p1._merged:
                continue
            for p2 in particles:
                if p1 is p2 or p2._merged:
                    continue
                if particlesTouch(p1, p2):
                    if p1._mass < p2._mass:
                        p1, p2 = p2, p1  # p1 is the biggest one (mass-wise)
                    p2._merged = True
                    if p1 is sun:
                        continue
                    newvx = (p1._vx*p1._mass+p2._vx*p2._mass)/(p1._mass+p2._mass)
                    newvy = (p1._vy*p1._mass+p2._vy*p2._mass)/(p1._mass+p2._mass)
                    p1._mass += p2._mass  # maintain the mass (just add them)
                    p1.setRadiusFromMass()  # new mass --> new radius
                    p1._vx, p1._vy = newvx, newvy

        # update zoom factor (numeric keypad +/- keys)
        if keysPressed[pg.K_KP_PLUS]:
            zoom /= 0.99
        if keysPressed[pg.K_KP_MINUS]:
            zoom /= 1.01
        if keysPressed[pg.K_ESCAPE]:
            break
        if evt.type == pg.NOEVENT:
            pg.time.wait(20)  # don't get beyond 50 frames per second...

if __name__ == "__main__":
    try:
        import psyco
        psyco.profile()
    except:
        print 'Psyco not found, ignoring it'
    main()
