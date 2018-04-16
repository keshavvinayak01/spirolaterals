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

import os
from gettext import gettext as _
import logging

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf

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
        self._sugarcolors = profile.get_color().to_string().split(',')
        colors = [[int(self._sugarcolors[0][1:3], 16),
                   int(self._sugarcolors[0][3:5], 16),
                   int(self._sugarcolors[0][5:7], 16)],
                  [int(self._sugarcolors[1][1:3], 16),
                   int(self._sugarcolors[1][3:5], 16),
                   int(self._sugarcolors[1][5:7], 16)]]

        # No sharing
        self.max_participants = 1

        # Build the activity toolbar.
        toolbox = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbox.toolbar.insert(activity_button, 0)
        activity_button.show()

        self.separator0 = Gtk.SeparatorToolItem()
        self.separator0.props.draw = False
        if Gdk.Screen.width() > 1023:
            toolbox.toolbar.insert(self.separator0, -1)
        self.separator0.show()

        self._add_speed_slider(toolbox.toolbar)

        self.separator1 = Gtk.SeparatorToolItem()
        self.separator1.props.draw = False
        if Gdk.Screen.width() > 1023:
            toolbox.toolbar.insert(self.separator1, -1)
        self.separator1.show()

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

        cyan = ToolButton('cyan')
        toolbox.toolbar.insert(cyan, -1)
        cyan.set_tooltip(_('Next pattern'))
        cyan.connect('clicked', self._button_cb, 'cyan')
        cyan.set_sensitive(False)
        cyan.show()

        self.separator2 = Gtk.SeparatorToolItem()
        self.separator2.props.draw = False
        if Gdk.Screen.width() > 1023:
            toolbox.toolbar.insert(self.separator2, -1)
        self.separator2.show()

        label = Gtk.Label('')
        label.set_use_markup(True)
        label.show()
        labelitem = Gtk.ToolItem()
        labelitem.add(label)
        toolbox.toolbar.insert(labelitem, -1)
        labelitem.show()

        self._score_image = Gtk.Image()
        item = Gtk.ToolItem()
        item.add(self._score_image)
        toolbox.toolbar.insert(item, -1)
        item.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbox.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

        toolbox.show()
        self.set_toolbar_box(toolbox)

        self.game = Spirolaterals.Spirolaterals(colors, self)
        # Build the Pygame canvas.
        self.game.canvas = self._pygamecanvas = \
            sugargame.canvas.PygameCanvas(self,
                main=self.game.run,
                modules=[pygame.display, pygame.font])


        # Note that set_canvas implicitly calls
        # read_file when resuming from the Journal.
        self.set_canvas(self._pygamecanvas)

        Gdk.Screen.get_default().connect('size-changed', self.__configure_cb)

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

    def update_score(self, score):
        pixbuf = _svg_str_to_pixbuf(self._score_icon(score))
        self._score_image.set_from_pixbuf(pixbuf)
        self._score_image.show()

    def _score_icon(self, score):
        return \
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + \
            '<svg\n' + \
            'xmlns:dc="http://purl.org/dc/elements/1.1/"\n' + \
            'xmlns:cc="http://creativecommons.org/ns#"\n' + \
            'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n' + \
            'xmlns:svg="http://www.w3.org/2000/svg"\n' + \
            'xmlns="http://www.w3.org/2000/svg"\n' + \
            'version="1.1"\n' + \
            'width="55"\n' + \
            'height="55"\n' + \
            'viewBox="0 0 55 55">\n' + \
            '<path\n' + \
            'd="M 27.497,50.004 C 39.927,50.004 50,39.937 50,27.508 50,'\
            '15.076 39.927,4.997 27.497,4.997 15.071,4.997 5,15.076 5,27.508 '\
            '5,39.937 15.071,50.004 27.497,50.004 z"\n' + \
            'style="fill:#ffffff;fill-opacity:1" /><text\n' + \
            'style="fill:#000000;fill-opacity:1;stroke:none;font-family:Sans">'\
            '<tspan\n' + \
            'x="27.5"\n' + \
            'y="37.3"\n' + \
            'style="font-size:24px;text-align:center;text-anchor:middle">'\
            '%d' % score + \
            '</tspan></text>\n' + \
            '</svg>'

    def good_job_image_path(self):
        pixbuf = _svg_str_to_pixbuf(self._good_job_icon(self._sugarcolors[0]))
        path = os.path.join(activity.get_activity_root(), 'tmp',
                            'good-job.png')
        pixbuf.savev(path, 'png', [], [])
        return path

    def good_job_pixbuf(self, color):
        return _svg_str_to_pixbuf(self._good_job_icon(color))

    def _good_job_icon(self, color):
        return \
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + \
            '<svg\n' + \
            'xmlns:dc="http://purl.org/dc/elements/1.1/"\n' + \
            'xmlns:cc="http://creativecommons.org/ns#"\n' + \
            'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n' + \
            'xmlns:svg="http://www.w3.org/2000/svg"\n' + \
            'xmlns="http://www.w3.org/2000/svg"\n' + \
            'version="1.1"\n' + \
            'width="700"\n' + \
            'height="150">\n' + \
            '<g\n' + \
            'transform="translate(-322.5,-409.12501)">\n' + \
            '<g\n' + \
            'transform="translate(-1,1)"\n' + \
            'style="stroke-width:3;stroke-miterlimit:4;">\n' + \
            '<path\n' + \
            'd="m 325,470.5 197,1 0,68 -196.5,17 z"\n' + \
            'style="fill:%s;' % color + \
            'fill-opacity:1;stroke:#ffffff;stroke-width:3;\n' + \
            'stroke-linejoin:miter;stroke-miterlimit:4;\n' + \
            'stroke-opacity:1;" />\n' + \
            '<path\n' + \
            'd="m 523.58046,470.41954 c -0.13908,-5.262 5.74754,-7.078\n' + \
            '9.44636,-9 8.61617,-4.2445 9.8557,-8.02297 12.473,-16.41954\n' + \
            '1.76159,-5.65019 1.81398,-11.7016 3,-17.5 0.72099,-3.52486\n' + \
            '0.49972,-7.50946 2.5,-10.5 2.0574,-3.07595 5.4789,-5.36144\n' + \
            '9,-6.5 2.6959,-0.8717 5.8359,-0.96454 8.5,0 2.4479,0.88627\n' + \
            '4.49712,2.87417 6,5 2.77016,3.91842 4.78743,10.31663 \n' + \
            '4.20977,15.08046 -1.40645,11.59866 -4.33199,20.55541\n' + \
            '-6.91954,29.18295 2.63914,4.35385 1.09045,0.91477\n' + \
            '19.37546,1.70977 4.12891,2.16337 7.61581,4.72782\n' + \
            '6.59773,10.23659 1.52418,5.05477 -3.98096,6.45467\n' + \
            '-3.15615,9.34387 5.05679,2.02909 10.82214,5.37105\n' + \
            '9.94637,10.268 0.7607,9.8204 -3.3900,8.29484 -5.5,11.67817\n' + \
            '1.54287,3.42335 2.23857,5.25348 2.91954,9.16 0.8917,5.11047\n' + \
            '-2.53079,8.96195 -9.55364,11.05363 -1.03862,3.55186\n' + \
            '1.99938,6.551 2.5536,10.20977 0.64307,4.245 -1.56067,7.6627\n' + \
            '-4.47318,9.08046 -25.61313,0.54849 -33.0002,0.80747 -57.5,0\n' + \
            '-2.385,-0.0786 -3.62433,0.62247 -6.20977,-2.02682\n' + \
            '-1.45872,-1.49473 -2.77989,-1.80492 -2.79023,-3.44636 z"\n' + \
            'style="fill:%s;' % color + \
            'fill-opacity:1;stroke:#ffffff;stroke-width:3;\n' + \
            'stroke-linejoin:miter;stroke-miterlimit:4;\n' + \
            'stroke-opacity:1;stroke-dasharray:none" />\n' + \
            '<rect\n' + \
            'width="45"\n' + \
            'height="20"\n' + \
            'ry="10"\n' + \
            'x="571.5"\n' + \
            'y="461"\n' + \
            'style="fill:%s;' % color + \
            'fill-opacity:1;stroke:#ffffff;\n' + \
            'stroke-width:3;stroke-linecap:round;stroke-linejoin:round;\n' + \
            'stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none;\n' + \
            'stroke-dashoffset:0" />\n' + \
            '<rect\n' + \
            'width="57"\n' + \
            'height="20"\n' + \
            'ry="10"\n' + \
            'x="566"\n' + \
            'y="483"\n' + \
            'style="fill:%s;' % color + \
            'fill-opacity:1;stroke:#ffffff;\n' + \
            'stroke-width:3;stroke-linecap:round;stroke-linejoin:round;\n' + \
            'stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none;\n' + \
            'stroke-dashoffset:0" />\n' + \
            '<rect\n' + \
            'width="54.5"\n' + \
            'height="20"\n' + \
            'ry="10"\n' + \
            'x="566.5"\n' + \
            'y="502.5"\n' + \
            'style="fill:%s;' % color + \
            'fill-opacity:1;stroke:#ffffff;\n' + \
            'stroke-width:3;stroke-linecap:round;stroke-linejoin:round;\n' + \
            'stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none;\n' + \
            'stroke-dashoffset:0" />\n' + \
            '<rect\n' + \
            'width="40.5"\n' + \
            'height="20"\n' + \
            'ry="10"\n' + \
            'x="574"\n' + \
            'y="523"\n' + \
            'style="fill:%s;' % color + \
            'fill-opacity:1;stroke:#ffffff;\n' + \
            'stroke-width:3;stroke-linecap:round;stroke-linejoin:round;\n' + \
            'stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none;\n' + \
            'stroke-dashoffset:0" />\n' + \
            '</g>\n' + \
            '<text\n' + \
            'style="font-size:16px;font-style:normal;font-weight:normal;\n' + \
            'text-align:end;line-height:125%;letter-spacing:0px;\n' + \
            'text-anchor:end;fill:#ff0000;fill-opacity:1;\n' + \
            'stroke:none;font-family:Sans"><tspan\n' + \
            'x="880" y="507"\n' + \
            'style="font-size:48px;fill:%s;fill-opacity:1">\n' % color + \
            _('Good job!') + \
            '</tspan></text>\n' + \
            '</g>\n' + \
            '</svg>'


def _svg_str_to_pixbuf(svg_string):
    ''' Load pixbuf from SVG string '''
    pl = GdkPixbuf.PixbufLoader.new_with_type('svg')
    pl.write(svg_string.encode())
    pl.close()
    pixbuf = pl.get_pixbuf()
    return pixbuf
