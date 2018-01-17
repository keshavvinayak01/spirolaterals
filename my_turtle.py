# my_turtle.py
"""
    Copyright (C) 2010  Peter Hewitt

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

"""
import logging
import pygame

import g
import utils


class TurtleClass:  # used only for keeping track of the right hand turtle

    def setup(self, color):
        steps = 0
        for n in self.current:
            steps = steps + 4 * n
        self.steps = steps
        self.x1 = g.x1 + 4.0 * g.dd
        self.y1 = g.y1 + 6.0 * g.dd
        self.dx = 0
        self.dy = -g.dd
        self.step_count = 0
        self.ms = pygame.time.get_ticks()
        self.running = False
        self.crashed = False
        self.changed = False
        self.win = False
        self.color = color
        self.between_levels = False

    def move(self):
        if self.step_count < self.steps:
            d = pygame.time.get_ticks() - self.ms
            if d < 0 or d > g.delay:  # time to move
                g.redraw = True
                x2 = self.x1 + self.dx
                y2 = self.y1 + self.dy
                self.x1 = x2
                self.y1 = y2
                self.step_count += 1
                self.ms = pygame.time.get_ticks()
        else:
            self.running = False

    def help1(self):
        x1 = g.x1 + 4 * g.dd
        y1 = g.y1 + 6 * g.dd
        dx = 0
        dy = -g.dd
        steps = 0
        angle = 0
        n = 0
        for j in self.current:
            for k in range(j):
                steps += 1
                x2 = x1 + dx
                y2 = y1 + dy
                pygame.draw.line(g.screen, self.color, (x1, y1), (x2, y2), 4)
                x1 = x2
                y1 = y2
            if dy == -g.dd:
                dx = g.dd
                dy = 0
                angle = 90
            elif dx == g.dd:
                dx = 0
                dy = g.dd
                angle = 180
            elif dy == g.dd:
                dx = -g.dd
                dy = 0
                angle = 270
            else:
                dx = 0
                dy = -g.dd
                angle = 0
            n += 1
            if n == g.help1:
                break
        utils.centre_blit(g.screen, g.turtle, (x2, y2), angle)
        self.step_count = steps

    def draw(self):
        if self.between_levels:
            return

        x1 = g.x1 + 4 * g.dd
        y1 = g.y1 + 6 * g.dd
        dx = 0
        dy = -g.dd
        steps = 0
        angle = 0
        x2 = x1
        y2 = y1  # in case we haven't moved yet - for turtle image
        done = True
        n = 0
        for i in range(4):
            for j in self.current:
                for k in range(j):
                    steps += 1
                    if not g.show_help:
                        if steps > self.step_count:
                            done = False
                            break
                    x2 = x1 + dx
                    y2 = y1 + dy
                    pygame.draw.line(g.screen, self.color,
                                     (x1, y1), (x2, y2), 4)
                    x1 = x2
                    y1 = y2
                if not g.show_help:
                    if steps > self.step_count:
                        break
                if dy == -g.dd:
                    dx = g.dd
                    dy = 0
                    angle = 90
                elif dx == g.dd:
                    dx = 0
                    dy = g.dd
                    angle = 180
                elif dy == g.dd:
                    dx = -g.dd
                    dy = 0
                    angle = 270
                else:
                    dx = 0
                    dy = -g.dd
                    angle = 0
                if g.show_help:
                    n += 1
                    if n == g.help1:
                        self.step_count = steps
                        break
            if g.show_help:
                if n == g.help1:
                    break
            elif steps > self.step_count:
                break
        img = g.turtle
        if self.crashed:
            img = g.crash
        utils.centre_blit(g.screen, img, (x2, y2), angle)
        d8 = 8 * g.dd
        if not g.show_help:
            if abs(x2 - g.x1) < .1 or abs(x2 - (g.x1 + d8)) < .1 or \
                    abs(y2 - g.y1) < .1 or abs(y2 - (g.y1 + d8)) < .1:
                if not self.crashed:
                    g.crash_drawn = False
                self.running = False
                self.crashed = True
            elif done:
                self.win = correct(self.current)
                if self.win:
                    if not g.finale:
                        if g.help2 > 5:
                            g.help2 = 5
                        g.score = g.score + 6 - g.help2
                    g.finale = True

    def clear(self):
        '''
        x1 = g.x1 + 4 * g.dd
        y1 = g.y1 + 6 * g.dd
        angle = 0
        x2 = x1
        y2 = y1
        img = g.crash
        utils.centre_blit(g.screen, img, (x2, y2), angle)
        '''
        self.between_levels = True


def correct(current):
    for goal in g.goals:
        if trace(goal) == trace(current):
            return True
    return False


def trace(l):  # returns a list based on the line segments drawn
    hl = [0, 0, 0, 0, 0, 0, 0]
    vl = [0, 0, 0, 0, 0, 0, 0]
    x1 = 3
    y1 = 1
    dx = 0
    dy = 1
    for i in range(4):
        for j in l:
            for k in range(j):
                x2 = x1 + dx
                y2 = y1 + dy
                mark(hl, vl, x1, y1, x2, y2)
                x1 = x2
                y1 = y2
            if dy == -1:
                dx = -1
                dy = 0
            elif dx == 1:
                dx = 0
                dy = -1
            elif dy == 1:
                dx = 1
                dy = 0
            else:
                dx = 0
                dy = 1
    return hl + vl


def mark(hl, vl, x1, y1, x2, y2):
    twos = [1, 2, 4, 8, 16, 32]
    if x1 == x2:  # vertical
        y = min(y1, y2)
        vl[x1] = vl[x1] | twos[y]
    else:
        x = min(x1, x2)
        hl[y1] = hl[y1] | twos[x]
