#!/usr/bin/python
# Spirolaterals.py
"""
    Copyright (C) 2010  Peter Hewitt

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

"""
import os
import sys
import logging
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
import pygame

import g
import utils
import buttons
import my_turtle
import load_save
import slider


class Spirolaterals:

    def __init__(self, colors, sugar=True):
        self.colors = colors
        self.sugar = sugar
        self.journal = True  # set to False if we come in via main()
        self.canvas = None
        self.label = None
        self.cyan_button = None
        self.pattern = 1
        self.num_patterns = utils.count_lines(
            os.path.join('data', 'patterns.dat'))

    def display(self):  # called each loop
        if g.big:
            g.screen.fill(self.colors[1])
            utils.centre_blit(g.screen, g.big_surface, (g.sx(16), g.sy(11.5)))
        else:
            if self.sugar:
                g.screen.fill(self.colors[1])
            else:
                g.screen.blit(g.bgd, (g.sx(0), 0))
            g.screen.blit(g.box, (g.x0, g.y0))
            g.screen.blit(g.box, (g.x1, g.y1))
            if not self.sugar:
                utils.centre_blit(g.screen, g.magician, g.magician_c)
            self.draw_goal()
            utils.centre_blit(g.screen, g.turtle,
                              (g.x0 + 4 * g.dd, g.y0 + 6 * g.dd))
            self.tu.draw()
            if self.tu.win:
                utils.centre_blit(g.screen, g.smiley, (g.sx(16.6), g.sy(2.2)))
                if self.sugar:
                    self.cyan_button.set_sensitive(True)
                else:
                    buttons.on('cyan')
                if not self.journal:
                    utils.save()
            self.draw_nos()
            if not self.sugar:
                buttons.draw()
                self.slider.draw()
            if g.score > 0:
                if self.sugar:
                    self.label.set_markup(
                        '<span><big><b> %s</b></big></span>' % (str(g.score)))
                else:
                    utils.display_score()
            utils.display_number1(g.pattern, (g.sx(2.4), g.sy(2)),
                                  g.font1, utils.BLUE)

    def set_cyan_button(self, cyan):
        self.cyan_button = cyan

    def set_label(self, label):
        self.label = label

    def do_slider(self, value):
        g.delay = int(value)

    def do_button(self, bu):
        if bu == 'cyan':
            g.pattern += 1
            if g.pattern == self.num_patterns + 1:
                g.pattern = 1
            g.help1 = 0
            g.help2 = 0
            self.get_goal()
            self.tu.win = False
            g.finale = False
            g.show_help = False
            self.tu.changed = True
            self.tu.clear()
            if self.sugar:
                self.cyan_button.set_sensitive(False)
            else:
                buttons.off('cyan')
            self.mouse_1st_no()  # to 1st number
        elif bu == 'black':
            self.tu.current = utils.copy_list(g.numbers)
            self.tu.setup(self.colors[0])
            g.show_help = False
        elif bu == 'green':
            self.tu.between_levels = False
            g.show_help = False
            if self.tu.changed:
                self.tu.current = utils.copy_list(g.numbers)
                self.tu.setup(self.colors[0])
                self.tu.changed = False
                self.tu.running = True
            elif self.tu.win or self.tu.crashed:
                self.tu.setup(self.colors[0])
                self.tu.running = True
            else:
                if self.tu.step_count == 0:
                    self.tu.ms = pygame.time.get_ticks()
                self.tu.running = True
        elif bu == 'red':
            self.tu.running = False

    def do_key(self, key):
        if key in g.CROSS and not self.sugar:
            if utils.mouse_on_img1(g.magician, g.magician_c):
                self.help2()
                return
            bu = buttons.check()
            if bu != '':
                self.do_button(bu)
                return
            g.show_help = False
            self.check_nos(1)
            return
        if key in g.CIRCLE:
            self.check_nos(3)
            return
        if key in g.RIGHT:
            self.mouse_right()
            return
        if key in g.LEFT:
            self.mouse_left()
            return
        if key in g.SQUARE:
            if self.sugar and self.cyan_button.get_sensitive():
                self.do_button('cyan')
            if not self.sugar and buttons.active('cyan'):
                self.do_button('cyan')
            return
        if key in g.TICK:
            self.change_level()
            return
        if key == pygame.K_v:
            g.version_display = not g.version_display
            return

    def mouse_1st_no(self):
        c = g.n_cx0 + g.sy(.2), g.n_cy0 + g.sy(1.2)
        pygame.mouse.set_pos(c)
        g.pos = c

    def mouse_magician(self):
        x, y = g.magician_c
        x -= g.sy(.15)
        y -= g.sy(.52)
        c = x, y
        pygame.mouse.set_pos(c)
        g.pos = c

    def mouse_left(self):
        bu = ''
        cx = g.n_cx0
        cy = g.n_cy0
        c = None
        if not self.sugar:
            if utils.mouse_on_img1(g.magician, g.magician_c):
                c = (cx + 4 * g.n_dx, cy)
            elif buttons.mouse_on('cyan'):
                self.mouse_magician()
                return
            elif buttons.mouse_on('green'):
                if buttons.active('cyan'):
                    bu = 'cyan'
                else:
                    self.mouse_magician()
                    return
            elif buttons.mouse_on('red'):
                bu = 'green'
            elif buttons.mouse_on('black'):
                bu = 'red'
            if bu != '':
                buttons.set_mouse(bu)
                return
        if c is None:
            c = (cx, cy)  # default to 1st no.
            for i in range(5):
                n = g.numbers[i]
                if utils.mouse_on_img_rect(g.n[n - 1], (cx, cy)):
                    c = (cx - g.n_dx, cy)
                    break
                cx += g.n_dx
        cx, cy = c
        cx += g.sy(.2)
        cy += g.sy(1.2)
        c = cx, cy
        pygame.mouse.set_pos(c)
        g.pos = c
        return

    def mouse_right(self):
        bu = ''
        if not self.sugar:
            if utils.mouse_on_img1(g.magician, g.magician_c):
                bu = 'green'
                if buttons.active('cyan'):
                    bu = 'cyan'
            elif buttons.mouse_on('cyan'):
                bu = 'green'
            elif buttons.mouse_on('green'):
                bu = 'red'
            elif buttons.mouse_on('red'):
                bu = 'black'
            if bu != '':
                buttons.set_mouse(bu)
                return
        cx = g.n_cx0
        cy = g.n_cy0
        c = (cx, cy)  # default to 1st no.
        if not buttons.mouse_on('black'):
            for i in range(5):
                n = g.numbers[i]
                if utils.mouse_on_img_rect(g.n[n - 1], (cx, cy)):
                    if i == 4:
                        self.mouse_magician()
                        return
                    c = (cx + g.n_dx, cy)
                    break
                cx += g.n_dx
        cx, cy = c
        cx += g.sy(.2)
        cy += g.sy(1.2)
        c = cx, cy
        pygame.mouse.set_pos(c)
        g.pos = c
        return

    def change_level(self):
        g.level += 1
        if g.level > self.slider.steps:
            g.level = 1
        g.delay = (3 - g.level) * 400

    def draw_goal(self):  # draws the left hand pattern
        x1 = g.x0 + 4 * g.dd
        y1 = g.y0 + 6 * g.dd
        dx = 0
        dy = -g.dd
        for i in range(4):
            for j in g.goals[0]:
                for k in range(j):
                    x2 = x1 + dx
                    y2 = y1 + dy
                    pygame.draw.line(
                        g.screen, self.colors[0], (x1, y1), (x2, y2), 4)
                    x1 = x2
                    y1 = y2
                if dy == -g.dd:
                    dx = g.dd
                    dy = 0
                elif dx == g.dd:
                    dx = 0
                    dy = g.dd
                elif dy == g.dd:
                    dx = -g.dd
                    dy = 0
                else:
                    dx = 0
                    dy = -g.dd

    def calc_steps(self, l):  # calculates total # of steps for a given
                              # pattern eg [1,2,3,4,5] = (1+2+3+4+5)*4=60
        return [sum(x) * 4 for x in l]

    def get_goal(self):
        fname = os.path.join('data', 'patterns.dat')
        try:
            with open(fname, 'r') as f:
                for n in range(0, g.pattern):
                    s = f.readline().strip()
        except:
            s = '11132'
            g.pattern = 1
        s = s.split(' ')
        l = [[int(x) for x in y] for y in s]
        g.goals = l
        g.steps = self.calc_steps(l)

    def draw_nos(self):  # draw the numbers with glow in correct position
        pos = self.calc_pos(self.tu.step_count)
        x = g.n_cx0
        for i in range(5):
            if i == pos:
                x_glow = x
            n = g.numbers[i]
            utils.centre_blit(g.screen, g.n[n - 1], (x, g.n_cy0))
            x += g.n_dx
        if not self.tu.changed or g.show_help:
            if self.tu.step_count < self.tu.steps:  # no glow if finished
                n = self.tu.current[pos]
                utils.centre_blit(g.screen, g.n_glow[n - 1], (x_glow, g.n_cy0))

    def check_nos(self, mouse_button):
        w = g.n[3].get_width()
        h = g.n[3].get_height()  # "4" is widest
        x1 = g.n_cx0 - w / 2
        y1 = g.n_cy0 - h / 2
        x2 = g.n_cx0 + w / 2
        y2 = g.n_cy0 + h / 2
        for pos in range(5):
            if utils.mouse_in(x1, y1, x2, y2):
                self.tu.changed = True
                self.tu.running = False
                if mouse_button == 1:
                    self.inc_numbers(pos)
                elif mouse_button == 3:
                    self.dec_numbers(pos)
                return True
            x1 += g.n_dx
            x2 += g.n_dx
        return False

    def calc_pos(self, step_count):  # calculate which number we are
                                     # currently on
        steps = 1
        if self.tu.crashed:
            step_count -= 1
        for i in range(4):
            pos = 0
            for j in self.tu.current:
                for k in range(j):
                    if steps >= step_count:
                        return pos
                    steps += 1
                pos += 1

    def inc_numbers(self, pos):  # pos 0 to 4 - called with numberclicked
        v = g.numbers[pos] + 1
        if v == 6:
            v = 1
        g.numbers[pos] = v

    def dec_numbers(self, pos):  # pos 0 to 4 - called with numberclicked
        v = g.numbers[pos] - 1
        if v == 0:
            v = 5
        g.numbers[pos] = v

    def solution(self):
        s = ''
        for i in range(5):
            s += str(g.goals[0][i]) + ' '
        s = s[:9]
        return s

    def big_pic(self):
        if not self.tu.running:
            d = g.sy(1)
            s = g.bw - 2 * d
            self.tu.draw()
            g.player_surface.blit(
                g.screen, (0, 0), (g.x1 + d, g.y0 + d, s, s))
            g.big = True
            g.big_surface = pygame.transform.scale2x(g.player_surface)

    def help2(self):
        self.tu.current = utils.copy_list(g.numbers)
        self.tu.crashed = False
        g.help1 = 0
        looking = True
        best_match = self.help_answer()
        while looking:
            g.help1 += 1
            ind = g.help1 - 1
            if g.numbers[ind] != g.goals[best_match][ind]:
                g.numbers[ind] = g.goals[best_match][ind]
                self.tu.current[ind] = g.goals[best_match][ind]
                g.show_help = True
                self.tu.changed = True
                g.help2 += 1
                looking = False
            if g.help1 > 4:
                g.show_help = True
                looking = False

    def help_answer(self):
        scores = []
        for goal in g.goals:
            ind = 0
            while(g.numbers[ind] == goal[ind]):
                ind += 1
            scores.append(ind)
        return scores.index(max(scores))    

    def flush_queue(self):
        flushing = True
        while flushing:
            flushing = False
            if self.journal:
                while Gtk.events_pending():
                    Gtk.main_iteration()
            for event in pygame.event.get():
                flushing = True

    def save_pattern(self):
        logging.debug('save pattern %d' % (g.pattern))
        self.pattern = g.pattern

    def restore_pattern(self):
        g.pattern = self.pattern
        logging.debug('restore pattern %d' % (g.pattern))

    def g_init(self):
        g.init()

    def run(self, restore=False):
        self.g_init()
        if not self.journal:
            utils.load()
        load_save.retrieve()
        if restore:
            self.restore_pattern()
        else:
            g.delay = (3 - g.level) * 400
        self.tu = my_turtle.TurtleClass()
        self.tu.current = [1, 1, 1, 3, 2]
        self.get_goal()
        if g.pattern == 1:
            self.tu.current = utils.copy_list(g.goals[0])
        self.tu.setup(self.colors[0])
        g.numbers = utils.copy_list(self.tu.current)
        # buttons
        x = g.sx(7.3)
        y = g.sy(16.5)
        dx = g.sy(2.6)

        if not self.sugar:
            buttons.Button("cyan", (x, y), True)
            x += dx
            buttons.off('cyan')
            buttons.Button("green", (x, y), True)
            x += dx
            buttons.Button("red", (x, y), True)
            x += dx
            buttons.Button("black", (x, y), True)
            x += dx
            self.slider = slider.Slider(g.sx(23.5), g.sy(21), 3, utils.YELLOW)

        self.mouse_1st_no()  # to 1st number
        if self.canvas is not None:
            self.canvas.grab_focus()
        ctrl = False
        pygame.key.set_repeat(600, 120)
        key_ms = pygame.time.get_ticks()
        going = True
        while going:
            if self.journal:
                # Pump Gtk messages.
                while Gtk.events_pending():
                    Gtk.main_iteration()

            # Pump PyGame messages.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if not self.journal:
                        utils.save()
                    going = False
                elif event.type == pygame.MOUSEMOTION:
                    g.pos = event.pos
                    g.redraw = True
                    if self.canvas is not None:
                        self.canvas.grab_focus()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    g.redraw = True
                    if g.big:
                        g.big = False
                    else:
                        bu = buttons.check()
                        if bu != '':
                            self.do_button(bu)
                            self.flush_queue()
                        elif not self.sugar:
                            if utils.mouse_on_img1(g.magician, g.magician_c):
                                self.help2()
                            elif utils.mouse_in(g.x1, g.y0, g.x1 + g.bw,
                                                g.y0 + g.bw):
                                self.big_pic()
                            elif self.slider.mouse():
                                g.delay = (3 - g.level) * 400
                            else:
                                g.show_help = False
                                self.check_nos(event.button)
                        else:
                            g.show_help = False
                            self.check_nos(event.button)
                elif event.type == pygame.KEYDOWN:
                    # throttle keyboard repeat
                    if pygame.time.get_ticks() - key_ms > 110:
                        key_ms = pygame.time.get_ticks()
                        if ctrl:
                            if event.key == pygame.K_q:
                                if not self.journal:
                                    utils.save()
                                going = False
                                break
                            else:
                                ctrl = False
                        if event.key in (pygame.K_LCTRL, pygame.K_RCTRL):
                            ctrl = True
                            break
                        self.do_key(event.key)
                        g.redraw = True
                        self.flush_queue()
                elif event.type == pygame.KEYUP:
                    ctrl = False
            if not going:
                break
            if self.tu.running:
                self.tu.move()
            if not g.crash_drawn:
                g.crash_drawn = True
                g.redraw = True
            if g.redraw:
                self.display()
                if g.version_display:
                    utils.version_display()
                g.screen.blit(g.pointer, g.pos)
                pygame.display.flip()
                g.redraw = False
            g.clock.tick(40)

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((1024, 768), pygame.FULLSCREEN)
    game = Spirolaterals(([0, 255, 255], [0, 0, 0]), sugar=False)
    game.journal = False
    game.run()
    pygame.display.quit()
    pygame.quit()
    sys.exit(0)
