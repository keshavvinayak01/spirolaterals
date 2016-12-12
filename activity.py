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

import gtk
import gobject

from sugar.activity import activity
from sugar.graphics.toolbarbox import ToolbarBox
from sugar.activity.widgets import ActivityToolbarButton, StopButton
from sugar.graphics.toolbarbox import ToolbarButton
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.style import GRID_CELL_SIZE
from sugar import profile

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
        self._saved_file = None

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

        separator = gtk.SeparatorToolItem()
        separator.props.draw = True
        toolbox.toolbar.insert(separator, -1)
        separator.show()

        label = gtk.Label('')
        label.set_use_markup(True)
        label.show()
        labelitem = gtk.ToolItem()
        labelitem.add(label)
        toolbox.toolbar.insert(labelitem, -1)
        labelitem.show()

        export = ToolButton('export-turtleblocks')
        toolbox.toolbar.insert(export, -1)
        export.set_tooltip(_('Export to TurtleBlocks'))
        export.connect('clicked', self._export_turtleblocks_cb)
        export.show()

        separator = gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbox.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        stop_button.props.accelerator = _('<Ctrl>Q')
        toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

        toolbox.show()
        self.set_toolbox(toolbox)

        # Create the game instance.
        self.game = Spirolaterals.Spirolaterals(colors)

        # Build the Pygame canvas.
        self._pygamecanvas = \
            sugargame.canvas.PygameCanvas(self)
        # Note that set_canvas implicitly calls
        # read_file when resuming from the Journal.
        self.set_canvas(self._pygamecanvas)
        self.game.canvas = self._pygamecanvas

        gtk.gdk.screen_get_default().connect('size-changed',
                                             self.__configure_cb)

        # Start the game running.
        self.game.set_cyan_button(cyan)
        self.game.set_label(label)
        self._speed_range.set_value(200)
        self._pygamecanvas.run_pygame(self.game.run)

    def __configure_cb(self, event):
        ''' Screen size has changed '''
        logging.debug(self._pygamecanvas.get_allocation())
        pygame.display.set_mode((gtk.gdk.screen_width(),
                                 gtk.gdk.screen_height() - GRID_CELL_SIZE),
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

        self._adjustment = gtk.Adjustment(
            200, self.LOWER, self.UPPER, 25, 100, 0)
        self._adjustment.connect('value_changed', self._speed_change_cb)
        self._speed_range = gtk.HScale(self._adjustment)
        self._speed_range.set_inverted(True)
        self._speed_range.set_draw_value(False)
        self._speed_range.set_update_policy(gtk.UPDATE_CONTINUOUS)
        self._speed_range.set_size_request(120, 15)
        self._speed_range.show()

        self._speed_stepper_up = ToolButton('speed-up')
        self._speed_stepper_up.set_tooltip(_('Speed up'))
        self._speed_stepper_up.connect('clicked', self._speed_stepper_up_cb)
        self._speed_stepper_up.show()

        self._speed_range_tool = gtk.ToolItem()
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
        logging.debug(self._adjustment.value)
        self.game.do_slider(self._adjustment.value)
        return True

    def _export_turtleblocks_cb(self, button=None):
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

        dialog = gtk.FileChooserDialog("Export to TurtleBlocks", None,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                       gtk.STOCK_SAVE, gtk.RESPONSE_OK))

        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_keep_above(True)
        dialog.set_do_overwrite_confirmation(True)

        if self._saved_file != None:
            dialog.set_filename(self._saved_file)

        if dialog.run() == gtk.RESPONSE_OK:
            filename = dialog.get_filename()

            if not filename.endswith(".tb"):
                filename += ".tb"

            self._saved_file = filename

            file = open(self._saved_file, "w")
            file.write(turtle_data)
            file.close()

        dialog.destroy()
