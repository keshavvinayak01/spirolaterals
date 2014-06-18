#!/usr/bin/python
# Spirolaterals.py
"""
    Copyright (C) 2014  Walter Bender
    Copyright (C) 2010  Peter Hewitt

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This is a refactoring of Peter's Spirolaterals game. It uses cairo
    and Gtk instead of pygame.

"""
import os
import sys
import cairo
import logging

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import Pango
from gi.repository import PangoCairo

from sugar3.graphics import style

from sprites import Sprites, Sprite

# artwork positions/scale in [landscape, portrait]
BS = [400, 400]  # box scale
X1 = [25, 25]  # left/top box position
Y1 = [25, 25]
X2 = [475, 25]  # right/bottom box position
Y2 = [25, 475]
NX = [475, 475]
NY = [475, 475]
NS = [75, 75]
NO = [7, 7]
TX = [200, 225]
TY = [350, 350]
TS = [50, 50]
UX = [650, 475]
UY = [350, 850]
US = [50, 50]
GY = [500, 1000]
LS = [24, 24]


class Spirolaterals:

    def __init__(self, canvas, colors, parent=None, sugar=True):
        self.canvas = canvas
        self.colors = colors
        self.parent = parent
        self.good_job = None
        self.delay = 500
        self.score = 0
        self.sugar = sugar
        self.journal = True  # set to False if we come in via main()
        self.cyan_button = None
        self.pattern = 1
        self.last_pattern = None
        self.turtle_canvas = None
        self.user_numbers = [1, 1, 1, 3, 2]
        self.active_index = 0

        self.sprites = Sprites(self.canvas)
        self.sprites.set_delay(True)

        size = max(Gdk.Screen.width(), Gdk.Screen.height())

        cr = self.canvas.get_property('window').cairo_create()
        logging.error(cr)
        self.turtle_canvas = cr.get_target().create_similar(
            cairo.CONTENT_COLOR, size, size)
        logging.error(self.turtle_canvas)
        self.canvas.connect('draw', self.__draw_cb)

        self.cr = cairo.Context(self.turtle_canvas)
        self.cr.set_line_cap(1)  # Set the line cap to be round
        self.sprites.set_cairo_context(self.cr)

        self.canvas.set_can_focus(True)
        self.canvas.grab_focus()
        self.canvas.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.canvas.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.canvas.add_events(Gdk.EventMask.POINTER_MOTION_MASK)

        self.canvas.connect('button-press-event', self._button_press_cb)
        self.canvas.connect('button-release-event', self._button_release_cb)
        self.canvas.connect('motion-notify-event', self._mouse_move_cb)
        self.canvas.connect('key_press_event', self._keypress_cb)

        self.width = Gdk.Screen.width()
        self.height = Gdk.Screen.height() - style.GRID_CELL_SIZE

        if self.width < self.height:
            self.i = 1
        else:
            self.i = 0

        # TODO: SET SCALE
        self.scale = 1.0

        self.offset = 0
        self.offset = (self.width - 
                       (self.sx(X1[self.i] + X2[self.i]) +
                        self.ss(BS[self.i]))) / 2.

        self.numbers = []
        self.glownumbers = []
        self._create_number_sprites()
        self._create_turtle_sprites()
        self._create_results_sprites()

        self._set_color(colors[0])
        self._set_pen_size(4)

        self._show_user_numbers()
        self._show_background_graphics()
        # TODO: Add turtle graphics
        self.get_goal()
        self.draw_goal()
        self.inval_all()

    def _keypress_cb(self, area, event):
        ''' Keypress: moving the slides with the arrow keys '''

        k = Gdk.keyval_name(event.keyval)
        if k in ['1', '2', '3', '4', '5']:
            self.do_stop()
            i = self.active_index
            j = int(k) - 1
            self.numbers[i][self.user_numbers[i] - 1].set_layer(0)
            self.numbers[i][j].set_layer(1)
            self.user_numbers[i] = j + 1
            self.inval_all()
        elif k in ['KP_Up', 'j', 'Up']:
            self.do_stop()
            i = self.active_index
            j = self.user_numbers[i]
            if j < 5:
                j += 1
            self.numbers[i][self.user_numbers[i] - 1].set_layer(0)
            self.numbers[i][j - 1].set_layer(1)
            self.user_numbers[i] = j
            self.inval_all()
        elif k in ['KP_Down', 'k', 'Down']:
            self.do_stop()
            i = self.active_index
            j = self.user_numbers[i]
            if j > 0:
                j -= 1
            self.numbers[i][self.user_numbers[i] - 1].set_layer(0)
            self.numbers[i][j - 1].set_layer(1)
            self.user_numbers[i] = j
            self.inval_all()
        elif k in ['KP_Left', 'h', 'Left']:
            self.do_stop()
            self.active_index -= 1
            self.active_index %= 5
        elif k in ['KP_Right', 'l', 'Right']:
            self.do_stop()
            self.active_index += 1
            self.active_index %= 5
        elif k in ['Return']:
            self.do_run()
        elif k in ['space', 'Esc']:
            self.do_stop()
        else:
            logging.debug(k)

    def _mouse_move_cb(self, win, event):
        ''' Callback to handle the mouse moves '''
        pass

    def _button_release_cb(self, win, event):
        ''' Callback to handle the button releases '''
        pass

    def _button_press_cb(self, win, event):
        ''' Callback to handle the button presses '''
        win.grab_focus()
        x, y = map(int, event.get_coords())
        self.press = self.sprites.find_sprite((x, y))
        if self.press is not None and self.press.type == 'number':
            self.do_stop()
            i = int(self.press.name.split(',')[0])
            self.active_index = i
            j = int(self.press.name.split(',')[1])
            j1 = (j + 1) % 5
            self.numbers[i][j1].set_layer(1)
            self.numbers[i][j].set_layer(0)
            self.user_numbers[i] = j1 + 1
            self.inval_all()

    def _create_results_sprites(self):
        x = 0
        y = self.sy(GY[self.i])
        self._success = Sprite(self.sprites, x, y,
                               self.parent.good_job_pixbuf())
        self._success.hide()
        self._failure = Sprite(self.sprites, x, y, self.parent.splot_pixbuf())
        self._failure.hide()

    def _create_turtle_sprites(self):
        x = self.sx(TX[self.i] - TS[self.i] / 2)
        y = self.sy(TY[self.i])
        pixbuf = self.parent.turtle_pixbuf()
        self.target_turtle = Sprite(self.sprites, x, y, pixbuf)
        self.user_turtles = []
        x = self.sx(UX[self.i] - US[self.i] / 2)
        y = self.sy(UY[self.i])
        self.user_turtles.append(Sprite(self.sprites, x, y, pixbuf))
        pixbuf = pixbuf.rotate_simple(270)
        self.user_turtles.append(Sprite(self.sprites, x, y, pixbuf))
        pixbuf = pixbuf.rotate_simple(270)
        self.user_turtles.append(Sprite(self.sprites, x, y, pixbuf))
        pixbuf = pixbuf.rotate_simple(270)
        self.user_turtles.append(Sprite(self.sprites, x, y, pixbuf))
        self._show_turtle(0)
        self._splot = Sprite(self.sprites, 0, 0, self.parent.splot_pixbuf())
        self._splot.hide()

    def _show_splot(self, x, y, dd, h):
        for i in range(4):
            self.user_turtles[i].hide()
        if h == 0:
            self._splot.move((x - int(dd / 2), y))
        elif h == 1:
            self._splot.move((x - dd, y - int(dd / 2)))
        elif h == 2:
            self._splot.move((x - int(dd / 2), y - dd))
        elif h == 3:
            self._splot.move((x, y - int(dd / 2)))
        self._splot.set_layer(3)

    def _show_turtle(self, t):
        for i in range(4):
            if i == t:
                self.user_turtles[i].set_layer(2)
            else:
                self.user_turtles[i].hide()

    def _reset_user_turtle(self):
        x = self.sx(UX[self.i] - US[self.i] / 2)
        y = self.sy(UY[self.i])
        self.user_turtles[0].move((x, y))
        self._show_turtle(0)

    def _create_number_sprites(self):
        for i in range(5):
            self.numbers.append([])
            self.glownumbers.append([])
            for j in range(5):
                if self.i == 0:
                    x = self.sx(NX[self.i]) + i * (self.ss(NS[self.i]
                                                           + NO[self.i]))
                    y = self.sy(NY[self.i])
                else:
                    x = self.sy(NX[self.i])
                    y = self.sx(NY[self.i]) + i * (self.ss(NS[self.i]
                                                           + NO[self.i]))
                number = Sprite(
                    self.sprites, x, y,
                    self.parent.number_pixbuf(self.ss(NS[self.i]), j + 1,
                                              self.parent.sugarcolors[1]))
                number.type = 'number'
                number.name = '%d,%d' % (i, j)
                self.numbers[i].append(number)

                number = Sprite(
                    self.sprites, x, y,
                    self.parent.number_pixbuf(self.ss(NS[self.i]), j + 1,
                                              '#FFFFFF'))
                number.type = 'number'
                number.name = '%d,%d' % (i, j)
                self.glownumbers[i].append(number)

    def _show_user_numbers(self):
        # Hide the numbers
        for i in range(5):
            for j in range(5):
                self.numbers[i][j].set_layer(0)
                self.glownumbers[i][j].set_layer(0)
        # Show user numbers
        self.numbers[0][self.user_numbers[0] - 1].set_layer(1)
        self.numbers[1][self.user_numbers[1] - 1].set_layer(1)
        self.numbers[2][self.user_numbers[2] - 1].set_layer(1)
        self.numbers[3][self.user_numbers[3] - 1].set_layer(1)
        self.numbers[4][self.user_numbers[4] - 1].set_layer(1)

    def _show_background_graphics(self):
        if self.width < self.height:
            self.i = 1
        else:
            self.i = 0
        size = max(self.width, self.height)

        self._draw_pixbuf(
            self.cr, self.parent.background_pixbuf(), 0, 0, size, size)
        self._draw_pixbuf(
            self.cr, self.parent.box_pixbuf(self.ss(BS[self.i])),
            self.sx(X1[self.i]), self.sy(Y1[self.i]), self.ss(BS[self.i]),
            self.ss(BS[self.i]))
        self._draw_pixbuf(
            self.cr, self.parent.box_pixbuf(self.sx(BS[self.i])),
            self.sx(X2[self.i]), self.sy(Y2[self.i]), self.ss(BS[self.i]),
            self.ss(BS[self.i]))
        self._draw_text(self.cr, self.pattern, self.sx(X1[self.i]),
                        self.sy(Y1[self.i]), self.ss(LS[self.i]))

    def _set_pen_size(self, ps):
        self.cr.set_line_width(ps)

    def _set_color(self, color):
        r = color[0] / 255.
        g = color[1] / 255.
        b = color[2] / 255.
        self.cr.set_source_rgb(r, g, b)

    def _draw_line(self, x1, y1, x2, y2):
        self.cr.move_to(x1, y1)
        self.cr.line_to(x2, y2)
        self.cr.stroke()

    def ss(self, f):  # scale size function
        return int(f * self.scale)

    def sx(self, f):  # scale x function
        return int(f * self.scale + self.offset)

    def sy(self, f):  # scale y function
        return int(f * self.scale)

    def _draw_pixbuf(self, cc, pixbuf, x, y, w, h):
        cc.save()
        cc.translate(x + w / 2., y + h / 2.)
        cc.translate(-x - w / 2., -y - h / 2.)
        Gdk.cairo_set_source_pixbuf(cc, pixbuf, x, y)
        cc.rectangle(x, y, w, h)
        cc.fill()
        cc.restore()

    def _draw_text(self, cr, label, x, y, size):
        pl = PangoCairo.create_layout(cr)
        fd = Pango.FontDescription('Sans')
        fd.set_size(int(size) * Pango.SCALE)
        pl.set_font_description(fd)
        if type(label) == str or type(label) == unicode:
            pl.set_text(label.replace('\0', ' '), -1)
        elif type(label) == float or type(label) == int:
            pl.set_text(str(label), -1)
        else:
            pl.set_text(str(label), -1)
        cr.save()
        cr.translate(x, y)
        cr.set_source_rgb(1, 1, 1)
        PangoCairo.update_layout(cr, pl)
        PangoCairo.show_layout(cr, pl)
        cr.restore()

    def inval_all(self):
        ''' Force a refresh '''
        # TODO: Window inval
        self.canvas.queue_draw_area(0, 0, self.width, self.height)

    def __draw_cb(self, canvas, cr):
        cr.set_source_surface(self.turtle_canvas)
        cr.paint()

        self.sprites.redraw_sprites(cr=cr)

    def do_stop(self):
        self.running = False

    def do_run(self):
        self._show_background_graphics()
        # TODO: Add turtle graphics
        self._success.hide()
        self._failure.hide()
        self._splot.hide()
        self.get_goal()
        self.draw_goal()
        self.inval_all()
        self.running = True
        self.loop = 0
        self.active_index = 0
        self.step = 0
        self._set_pen_size(4)
        self._set_color(self.colors[0])
        x1 = self.sx(UX[self.i])
        y1 = self.sy(UY[self.i])
        dd = self.ss(US[self.i])
        self.numbers[0][self.user_numbers[0] - 1].set_layer(0)
        self.glownumbers[0][self.user_numbers[0] - 1].set_layer(1)
        self.user_turtles[0].move((int(x1 - dd / 2), y1))
        self._show_turtle(0)

        GObject.timeout_add(self.delay, self._do_step, x1, y1, dd, 0)

    def _do_step(self, x1, y1, dd, h):
        if not self.running:
            return
        if self.loop > 3:
            return
        if h == 0:  # up
            x2 = x1
            y2 = y1 - dd
            self.user_turtles[h].move((int(x2 - dd / 2), int(y2 - dd)))
        elif h == 1:  # right
            x2 = x1 + dd
            y2 = y1
            self.user_turtles[h].move((int(x2), int(y2 - dd / 2)))
        elif h == 2:  # down
            x2 = x1
            y2 = y1 + dd
            self.user_turtles[h].move((int(x2 - dd / 2), int(y2)))
        elif h == 3:  # left
            x2 = x1 - dd
            y2 = y1
            self.user_turtles[h].move((int(x2 - dd), int(y2 - dd / 2)))
        self._show_turtle(h)

        if x2 < self.sx(X2[self.i]) or \
           x2 > self.sx(X2[self.i] + BS[self.i]) or \
           y2 < self.sy(Y2[self.i]) or \
           y2 > self.sy(Y2[self.i] + BS[self.i]):
            self.do_stop()
            self._show_splot(x2, y2, dd, h)

        self._draw_line(x1, y1, x2, y2)
        self.inval_all()
        self.step += 1
        i = self.active_index
        if self.step == self.user_numbers[i]:
            self.numbers[i][self.user_numbers[i] - 1].set_layer(1)
            self.glownumbers[i][self.user_numbers[i] - 1].set_layer(0)
            h += 1
            h %= 4
            self.step = 0
            self.active_index += 1
            if self.active_index == 5:
                self.loop += 1
                self.active_index = 0
            else:
                i = self.active_index
                self.numbers[i][self.user_numbers[i] - 1].set_layer(0)
                self.glownumbers[i][self.user_numbers[i] - 1].set_layer(1)

        if self.loop < 4 and self.running:
            GObject.timeout_add(self.delay, self._do_step, x2, y2, dd, h)
        elif self.loop == 4:  # Test to see if we win
            self._reset_user_turtle()
            self.test_level()

    def test_level(self):
        success = True
        for i in range(5):
            if self.user_numbers[i] != self.goal[i]:
                success = False
                break
        if success:
            self._do_success()
        else:
            self._do_fail()

    def _do_success(self):
        logging.debug('success... you can advance to the next level')
        self._success.set_layer(3)
        self.parent.cyan.set_sensitive(True)
        if self.last_pattern != self.pattern:
            self.score += 6
            self.last_pattern = self.pattern
        self.parent.update_score(int(self.score))

    def _do_fail(self):
        self._failure.set_layer(3)
        logging.debug('fail... try again')
        self.parent.cyan.set_sensitive(False)

    def do_slider(self, value):
        self.delay = int(value)

    def do_button(self, bu):
        if bu == 'cyan':  # Next level
            self._success.hide()
            self._failure.hide()
            self._splot.hide()
            self.pattern += 1
            if self.pattern == 123:
                self.pattern = 1
            self.help1 = 0
            self.help2 = 0
            self.get_goal()
            self._show_background_graphics()
            self.draw_goal()
            self._reset_user_turtle()
            self.inval_all()
            self.parent.cyan.set_sensitive(False)
        elif bu == 'green':  # Run level
            self.do_run()
        elif bu == 'red':  # Stop level
            self.do_stop()

    def draw_goal(self):  # draws the left hand pattern
        x1 = self.sx(TX[self.i])
        y1 = self.sy(TY[self.i])
        dd = self.ss(TS[self.i])
        dx = 0
        dy = -dd
        for i in range(4):
            for j in self.goal:
                for k in range(j):
                    x2 = x1 + dx
                    y2 = y1 + dy
                    self._set_pen_size(4)
                    self._set_color(self.colors[0])
                    self._draw_line(x1, y1, x2, y2)
                    x1 = x2
                    y1 = y2
                if dy == -dd:
                    dx = dd
                    dy = 0
                elif dx == dd:
                    dx = 0
                    dy = dd
                elif dy == dd:
                    dx = -dd
                    dy = 0
                else:
                    dx = 0
                    dy = -dd

    def calc_steps(self, l):  # calculates total # of steps for a given
                              # pattern eg [1,2,3,4,5] = (1+2+3+4+5)*4=60
        return sum(l) * 4

    def get_goal(self):
        fname = os.path.join('data', 'patterns.dat')
        try:
            f = open(fname, 'r')
            for n in range(0, self.pattern):
                s = f.readline()
            s = s[0:5]
        except:
            s = 11132
            self.pattern = 1
        f.close
        l = [int(c) for c in str(s)]
        self.goal = l
        self.steps = self.calc_steps(l)
