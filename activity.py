# activity.py
# my standard link between sugar and my activity
"""
    Copyright (C) 2010  Peter Hewitt
    Copyright (C) 2013  Ignacio Rodriguez

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

"""

from gettext import gettext as _
import logging

from gi.repository import Gtk
from gi.repository import Gdk

from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton, StopButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.style import GRID_CELL_SIZE
from sugar3 import profile

import pygame
import sugargame.canvas

import load_save
import Spirolaterals


class PeterActivity(activity.Activity):
    LOWER = 0
    UPPER = 400

    def __init__(self, handle):
        super(PeterActivity, self).__init__(handle)

        # Get user's Sugar colors
        sugarcolors = profile.get_color().to_string().split(',')
        colors = [[int(sugarcolors[0][1:3], 16),
                   int(sugarcolors[0][3:5], 16),
                   int(sugarcolors[0][5:7], 16)],
                  [int(sugarcolors[1][1:3], 16),
                   int(sugarcolors[1][3:5], 16),
                   int(sugarcolors[1][5:7], 16)]]

        # No sharing
        self.max_participants = 1

        # Build the activity toolbar.
        toolbox = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbox.toolbar.insert(activity_button, 0)
        activity_button.show()

        self._add_speed_slider(toolbox.toolbar)

        cyan = ToolButton('cyan')
        toolbox.toolbar.insert(cyan, -1)
        cyan.set_tooltip(_('Next pattern'))
        cyan.connect('clicked', self._button_cb, 'cyan')
        cyan.set_sensitive(False)
        cyan.show()

        green = ToolButton('green')
        toolbox.toolbar.insert(green, -1)
        green.set_tooltip(_('Draw'))
        green.connect('clicked', self._button_cb, 'green')
        green.show()

        red = ToolButton('red')
        toolbox.toolbar.insert(red, -1)
        red.set_tooltip(_('Stop'))
        red.connect('clicked', self._button_cb, 'red')
        red.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = True
        toolbox.toolbar.insert(separator, -1)
        separator.show()

        label = Gtk.Label('')
        label.set_use_markup(True)
        label.show()
        labelitem = Gtk.ToolItem()
        labelitem.add(label)
        toolbox.toolbar.insert(labelitem, -1)
        labelitem.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbox.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        stop_button.props.accelerator = _('<Ctrl>Q')
        toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

        toolbox.show()
        self.set_toolbar_box(toolbox)

        # Create the game instance.
        self.game = Spirolaterals.Spirolaterals(colors)

        # Build the Pygame canvas.
        self._pygamecanvas = \
            sugargame.canvas.PygameCanvas(self)
        # Note that set_canvas implicitly calls
        # read_file when resuming from the Journal.
        self.set_canvas(self._pygamecanvas)
        self.game.canvas = self._pygamecanvas

        Gdk.Screen.get_default().connect('size-changed',
                                         self.__configure_cb)

        # Start the game running.
        self.game.set_cyan_button(cyan)
        self.game.set_label(label)
        self._speed_range.set_value(200)
        self._pygamecanvas.run_pygame(self.game.run)

    def __configure_cb(self, event):
        ''' Screen size has changed '''
        logging.debug(self._pygamecanvas.get_allocation())
        pygame.display.set_mode((Gdk.Screen.width(),
                                 Gdk.Screen.height() - GRID_CELL_SIZE),
                                pygame.RESIZABLE)
        self.game.save_pattern()
        self.game.g_init()
        self._speed_range.set_value(200)
        self.game.run(restore=True)

    def read_file(self, file_path):
        try:
            f = open(file_path, 'r')
        except Exception as e:
            logging.debug('Error opening %s: %s' % (file_path, e))
            return
        load_save.load(f)
        f.close()

    def write_file(self, file_path):
        f = open(file_path, 'w')
        load_save.save(f)
        f.close()

    def _button_cb(self, button=None, color=None):
        self.game.do_button(color)

    def _add_speed_slider(self, toolbar):
        self._speed_stepper_down = ToolButton('speed-down')
        self._speed_stepper_down.set_tooltip(_('Slow down'))
        self._speed_stepper_down.connect('clicked',
                                         self._speed_stepper_down_cb)
        self._speed_stepper_down.show()

        self._adjustment = Gtk.Adjustment.new(
            200, self.LOWER, self.UPPER, 25, 100, 0)
        self._adjustment.connect('value_changed', self._speed_change_cb)
        self._speed_range = Gtk.HScale.new(self._adjustment)
        self._speed_range.set_inverted(True)
        self._speed_range.set_draw_value(False)
        self._speed_range.set_size_request(120, 15)
        self._speed_range.show()

        self._speed_stepper_up = ToolButton('speed-up')
        self._speed_stepper_up.set_tooltip(_('Speed up'))
        self._speed_stepper_up.connect('clicked', self._speed_stepper_up_cb)
        self._speed_stepper_up.show()

        self._speed_range_tool = Gtk.ToolItem()
        self._speed_range_tool.add(self._speed_range)
        self._speed_range_tool.show()

        toolbar.insert(self._speed_stepper_down, -1)
        toolbar.insert(self._speed_range_tool, -1)
        toolbar.insert(self._speed_stepper_up, -1)
        return

    def _speed_stepper_down_cb(self, button=None):
        new_value = self._speed_range.get_value() + 25
        if new_value <= self.UPPER:
            self._speed_range.set_value(new_value)
        else:
            self._speed_range.set_value(self.UPPER)

    def _speed_stepper_up_cb(self, button=None):
        new_value = self._speed_range.get_value() - 25
        if new_value >= self.LOWER:
            self._speed_range.set_value(new_value)
        else:
            self._speed_range.set_value(self.LOWER)

    def _speed_change_cb(self, button=None):
        logging.debug(self._adjustment.get_value())
        self.game.do_slider(self._adjustment.get_value())
        return True
