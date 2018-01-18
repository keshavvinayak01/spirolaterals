# activity.py
# my standard link between sugar and my activity
"""
    Copyright (C) 2010  Peter Hewitt

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

"""

from gettext import gettext as _
import logging
import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
import pygame


from sugar3.activity import activity
from sugar3.datastore import datastore
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import ToolButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.style import GRID_CELL_SIZE
from sugar3.graphics.alert import Alert
from sugar3 import profile

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
        self.datapath = os.path.join(activity.get_activity_root(), 'instance')

        # Build the activity toolbar.
        toolbar_box = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        self._add_speed_slider(toolbar_box.toolbar)

        cyan = ToolButton('cyan')
        toolbar_box.toolbar.insert(cyan, -1)
        cyan.set_tooltip(_('Next pattern'))
        cyan.connect('clicked', self._button_cb, 'cyan')
        cyan.set_sensitive(False)
        cyan.show()

        green = ToolButton('green')
        toolbar_box.toolbar.insert(green, -1)
        green.set_tooltip(_('Draw'))
        green.connect('clicked', self._button_cb, 'green')
        green.show()

        red = ToolButton('red')
        toolbar_box.toolbar.insert(red, -1)
        red.set_tooltip(_('Stop'))
        red.connect('clicked', self._button_cb, 'red')
        red.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = True
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        label = Gtk.Label('')
        label.set_use_markup(True)
        label.show()
        labelitem = Gtk.ToolItem()
        labelitem.add(label)
        toolbar_box.toolbar.insert(labelitem, -1)
        labelitem.show()

        export = ToolButton('export-turtleblocks')
        toolbar_box.toolbar.insert(export, -1)
        export.set_tooltip(_('Export to TurtleBlocks'))
        export.connect('clicked', self._export_turtleblocks_cb)
        export.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        toolbar_box.show()
        self.set_toolbar_box(toolbar_box)
        # Create the game instance.
        self.game = Spirolaterals.Spirolaterals(colors)

        # Build the Pygame canvas.
        self.game.canvas = self._pygamecanvas = \
            sugargame.canvas.PygameCanvas(self,
                main=self.game.run,
                modules=[pygame.display, pygame.font])


        # Note that set_canvas implicitly calls
        # read_file when resuming from the Journal.
        self.set_canvas(self._pygamecanvas)

        Gdk.Screen.get_default().connect('size-changed',
                                             self.__configure_cb)

        # Start the game running.
        self.game.set_cyan_button(cyan)
        self.game.set_label(label)
        self._speed_range.set_value(200)

    def get_preview(self):
        return self._pygamecanvas.get_preview()

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

    def _export_turtleblocks_cb(self, button=None):
        alert = Alert()
        alert.props.title = _('Save as TurtleBlocks project')
        self.add_alert(alert)
        alert.show()

        GObject.idle_add(self._export_turtleblocks, alert)

    def _export_turtleblocks(self, alert):
        data = self.game.tu.current
        step = 75
        first = data[0] * step
        second = data[1] * step
        third = data[2] * step
        fourth = data[3] * step
        fifth = data[4] * step

        turtle_data = '[[0, ["start", 219], 248, 92, [null, 1]],' +\
                      '[1, ["repeat", 189], 266, 138, [0, 2, 3, null]],' +\
                      '[2, ["number", 4], 322, 138, [1, null]],' +\
                      '[3, "forward", 284, 180, [1, 4, 5]],' +\
                      ('[4, ["number", %s], 348, 180, [3, null]],' % first) +\
                      '[5, "right", 284, 222, [3, 6, 7]],' +\
                      '[6, ["number", 90], 342, 222, [5, null]],' +\
                      '[7, "forward", 284, 264, [5, 8, 9]],' +\
                      ('[8, ["number", %s], 348, 264, [7, null]],' % second) +\
                      '[9, "right", 284, 306, [7, 10, 11]],' +\
                      '[10, ["number", 90], 342, 306, [9, null]],' +\
                      '[11, "forward", 284, 348, [9, 12, 13]],' +\
                      ('[12, ["number", %s], 348, 348, [11, null]],'% third)  +\
                      '[13, "right", 284, 390, [11, 14, 15]],' +\
                      '[14, ["number", 90], 342, 390, [13, null]],' +\
                      '[15, "forward", 284, 432, [13, 16, 17]],' +\
                      ('[16, ["number", %s], 348, 432, [15, null]],'% fourth)  +\
                      '[17, "right", 284, 474, [15, 18, 19]],' +\
                      '[18, ["number", 90], 342, 474, [17, null]],' +\
                      '[19, "forward", 284, 516, [17, 20, 21]],' +\
                      ('[20, ["number", %s], 348, 516, [19, null]],'% fifth)  +\
                      '[21, "right", 284, 558, [19, 22, null]],' +\
                      '[22, ["number", 90], 342, 558, [21, null]]]'

        file_path = os.path.join(self.datapath, 'output.tb')
        with open(file_path, "w") as file:
            file.write(turtle_data)

        dsobject = datastore.create()
        dsobject.metadata['title'] = '%s %s' % (self.metadata['title'], _('TurtleBlocks'))
        dsobject.metadata['icon-color'] = profile.get_color().to_string()
        dsobject.metadata['mime_type'] = 'application/x-turtle-art'
        dsobject.metadata['activity'] = 'org.laptop.TurtleArtActivity'
        dsobject.set_file_path(file_path)
        datastore.write(dsobject)
        dsobject.destroy()
        os.remove(file_path)

        GObject.timeout_add(1000, self._remove_alert, alert)

    def _remove_alert(self, alert):
        self.remove_alert(alert)
