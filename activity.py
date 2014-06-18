# -*- coding: utf-8 -*-
# Copyright 2010, Peter Hewitt
# Copyright 2013, 14, Walter Bender
# Copyright 2013, Ignacio Rodriguez

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" This is a refactoring of Spirolaterals by Peter Hewitt. Peter's
version was based on the pygame library. This version uses Gtk and
Cairo. """

import os
from gettext import gettext as _
import logging

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf

from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton, StopButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.style import GRID_CELL_SIZE
from sugar3 import profile

import Spirolaterals


def _luminance(color):
    ''' Calculate luminance value '''
    return int(color[1:3], 16) * 0.3 + int(color[3:5], 16) * 0.6 + \
        int(color[5:7], 16) * 0.1


def lighter_color(colors):
    ''' Which color is lighter? Use that one for the text nick color '''
    if _luminance(colors[0]) > _luminance(colors[1]):
        return 0
    return 1


class PeterActivity(activity.Activity):
    LOWER = 0
    UPPER = 1000

    def __init__(self, handle):
        super(PeterActivity, self).__init__(handle)

        # Get user's Sugar colors
        sugarcolors = profile.get_color().to_string().split(',')
        i = lighter_color(sugarcolors)
        self.sugarcolors = [sugarcolors[i], sugarcolors[1 - i]]
        colors = [[int(self.sugarcolors[0][1:3], 16),
                   int(self.sugarcolors[0][3:5], 16),
                   int(self.sugarcolors[0][5:7], 16)],
                  [int(self.sugarcolors[1][1:3], 16),
                   int(self.sugarcolors[1][3:5], 16),
                   int(self.sugarcolors[1][5:7], 16)]]

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

        self.cyan = ToolButton('cyan')
        toolbox.toolbar.insert(self.cyan, -1)
        self.cyan.set_tooltip(_('Next pattern'))
        self.cyan.connect('clicked', self._button_cb, 'cyan')
        self.cyan.set_sensitive(False)
        self.cyan.show()

        self.separator2 = Gtk.SeparatorToolItem()
        self.separator2.props.draw = False
        if Gdk.Screen.width() > 1023:
            toolbox.toolbar.insert(self.separator2, -1)
        self.separator2.show()

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
        stop_button.props.accelerator = _('<Ctrl>Q')
        toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

        toolbox.show()
        self.set_toolbar_box(toolbox)

        self._toolbar = toolbox.toolbar

        # Create a canvas
        canvas = Gtk.DrawingArea()
        canvas.set_size_request(Gdk.Screen.width(),
                                Gdk.Screen.height())
        self.set_canvas(canvas)
        canvas.show()
        self.show_all()

        # Initialize the canvas
        logging.error(canvas)
        self.game = Spirolaterals.Spirolaterals(canvas, colors, parent=self)

        Gdk.Screen.get_default().connect('size-changed', self.__configure_cb)

    def __configure_cb(self, event):
        ''' Screen size has changed '''
        if Gdk.Screen.width() < 1024 and \
                self.separator1 in self._toolbar:
            self._toolbar.remove(self.separator0)
            self._toolbar.remove(self.separator1)
            self._toolbar.remove(self.separator2)
        elif self.separator1 not in self._toolbar:
            self._toolbar.insert(self.separator0, 1)
            self._toolbar.insert(self.separator1, 5)
            self._toolbar.insert(self.separator2, 9)

        # TODO: rearrange all the bits and pieces

    '''
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
    '''

    def _button_cb(self, button=None, color=None):
        self.game.do_button(color)

    def _add_speed_slider(self, toolbar):
        self._speed_stepper_down = ToolButton('speed-down')
        self._speed_stepper_down.set_tooltip(_('Slow down'))
        self._speed_stepper_down.connect('clicked',
                                         self._speed_stepper_down_cb)
        self._speed_stepper_down.show()

        self._adjustment = Gtk.Adjustment.new(
            500, self.LOWER, self.UPPER, 25, 100, 0)
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
        self.game.do_slider(int(self._adjustment.get_value()))
        return True

    def update_score(self, score):
        pixbuf = _svg_str_to_pixbuf(_score_icon(score))
        self._score_image.set_from_pixbuf(pixbuf)
        self._score_image.show()

    def good_job_image_path(self):
        pixbuf = _svg_str_to_pixbuf(_good_job_icon(self.sugarcolors[0]))
        path = os.path.join(activity.get_activity_root(), 'tmp',
                            'good-job.png')
        pixbuf.savev(path, 'png', [], [])
        return path

    def good_job_pixbuf(self, color):
        return _svg_str_to_pixbuf(_good_job_icon(color))

    def background_pixbuf(self):
        size = max(Gdk.Screen.width(), Gdk.Screen.height())
        return _svg_str_to_pixbuf(_rect(size, size, 0, self.sugarcolors[1]))

    def turtle_pixbuf(self):
        return _svg_str_to_pixbuf(_turtle_icon(self.sugarcolors[0]))

    def box_pixbuf(self, size):
        return _svg_str_to_pixbuf(_rect(size, size, 10, '#000000'))

    def number_pixbuf(self, size, number, color):
        return _svg_str_to_pixbuf(_number(size, 4, number, color))


def _turtle_icon(color):
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
            'height="55">\n' + \
            '<g>\n' + \
            '<path d="M 27.497 48.279 C 26.944 48.279 26.398 48.244 25.86 48.179 L 27.248 50.528 L 28.616 48.215 C 28.245 48.245 27.875 48.279 27.497 48.279 Z " fill="#FFFFFF" stroke="%s" stroke-width="3.5"/>\n' % color + \
            '<g>\n' + \
            '<path d="M 40.16 11.726 C 37.996 11.726 36.202 13.281 35.817 15.333 C 37.676 16.678 39.274 18.448 40.492 20.541 C 42.777 20.369 44.586 18.48 44.586 16.151 C 44.586 13.707 42.604 11.726 40.16 11.726 Z " fill="#FFFFFF" stroke="%s" stroke-width="3.5"/>\n' % color + \
            '<path d="M 40.713 39.887 C 39.489 42.119 37.853 44.018 35.916 45.443 C 36.437 47.307 38.129 48.682 40.16 48.682 C 42.603 48.682 44.586 46.702 44.586 44.258 C 44.586 42.003 42.893 40.162 40.713 39.887 Z " fill="#FFFFFF" stroke="%s" stroke-width="3.5"/>\n' % color + \
            '<path d="M 14.273 39.871 C 12.02 40.077 10.249 41.95 10.249 44.258 C 10.249 46.701 12.229 48.682 14.673 48.682 C 16.737 48.682 18.457 47.262 18.945 45.35 C 17.062 43.934 15.47 42.061 14.273 39.871 Z " fill="#FFFFFF" stroke="%s" stroke-width="3.5"/>\n' % color + \
            '<path d="M 19.026 15.437 C 18.683 13.334 16.872 11.726 14.673 11.726 C 12.229 11.726 10.249 13.707 10.249 16.15 C 10.249 18.532 12.135 20.46 14.494 20.556 C 15.68 18.513 17.226 16.772 19.026 15.437 Z " fill="#FFFFFF" stroke="%s" stroke-width="3.5"/>\n' % color + \
            '</g>\n' + \
            '<path d="M 27.497 12.563 C 29.405 12.563 31.225 12.974 32.915 13.691 C 33.656 12.615 34.093 11.314 34.093 9.908 C 34.093 6.221 31.104 3.231 27.416 3.231 C 23.729 3.231 20.74 6.221 20.74 9.908 C 20.74 11.336 21.192 12.657 21.956 13.742 C 23.68 12.993 25.543 12.563 27.497 12.563 Z " fill="#FFFFFF" stroke="%s" stroke-width="3.5"/>\n' % color + \
            '<g>\n' + \
            '<path d="M 43.102 30.421 C 43.102 35.1554 41.4568 39.7008 38.5314 43.0485 C 35.606 46.3963 31.6341 48.279 27.497 48.279 C 23.3599 48.279 19.388 46.3963 16.4626 43.0485 C 13.5372 39.7008 11.892 35.1554 11.892 30.421 C 11.892 20.6244 18.9364 12.563 27.497 12.563 C 36.0576 12.563 43.102 20.6244 43.102 30.421 Z " fill="#FFFFFF" stroke="%s" stroke-width="3.5"/>\n' % color + \
            '</g>\n' + \
            '<g>\n' + \
            '<path d="M 25.875 33.75 L 24.333 29.125 L 27.497 26.538 L 31.112 29.164 L 29.625 33.833 Z " fill="%s" stroke="none" stroke-width="3.5"/>\n' + \
            '<path d="M 27.501 41.551 C 23.533 41.391 21.958 39.542 21.958 39.542 L 25.528 35.379 L 29.993 35.547 L 33.125 39.667 C 33.125 39.667 30.235 41.661 27.501 41.551 Z " fill="%s" stroke="none" />\n' % color + \
            '<path d="M 18.453 33.843 C 17.604 30.875 18.625 26.959 18.625 26.959 L 22.625 29.126 L 24.118 33.755 L 20.536 37.988 C 20.536 37.987 19.071 35.998 18.453 33.843 Z " fill="%s" stroke="none" />\n' % color + \
            '<path d="M 19.458 25.125 C 19.458 25.125 19.958 23.167 22.497 21.303 C 24.734 19.66 26.962 19.583 26.962 19.583 L 26.925 24.564 L 23.404 27.314 L 19.458 25.125 Z " fill="%s" stroke="none" />\n' % color + \
            '<path d="M 32.084 27.834 L 28.625 24.959 L 29 19.75 C 29 19.75 30.834 19.708 32.959 21.417 C 35.187 23.208 36.321 26.4 36.321 26.4 L 32.084 27.834 Z " fill="%s" stroke="none" />\n' % color + \
            '<path d="M 31.292 34.042 L 32.605 29.578 L 36.792 28.042 C 36.792 28.042 37.469 30.705 36.75 33.709 C 36.21 35.965 34.666 38.07 34.666 38.07 L 31.292 34.042 Z " fill="%s" stroke="none" />\n' % color + \
            '</g>\n' + \
            '</g>\n' + \
            '</svg>'


def _good_job_icon(color):
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


def _score_icon(score):
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


def _number(size, radius, number, color):
    x = size / 2.
    y = size * 4 / 5.
    pt = size * 0.96
    return \
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + \
            '<svg\n' + \
            'xmlns:dc="http://purl.org/dc/elements/1.1/"\n' + \
            'xmlns:cc="http://creativecommons.org/ns#"\n' + \
            'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n' + \
            'xmlns:svg="http://www.w3.org/2000/svg"\n' + \
            'xmlns="http://www.w3.org/2000/svg"\n' + \
            'version="1.1"\n' + \
            'width="%d"\n' % size + \
            'height="%d"\n' % size + \
            'viewBox="0 0 %d %d">\n' % (size, size) + \
            '<rect\n' + \
            'width="%d"\n' % size + \
            'height="%d"\n' % size + \
            'ry="%d"\n' % radius + \
            'x="0"\n' + \
            'y="0"\n' + \
            'style="fill:#A0A0A0;fill-opacity:1;stroke:none;" />\n' + \
            '<text>\n' + \
            '<tspan\n' + \
            'x="%f" ' % x + \
            'y="%f" ' % y + \
            'style="font-size:%fpx;' % pt + \
            'text-align:center;text-anchor:middle;fill:%s">' % color + \
            str(number) + \
            '</tspan></text>\n' + \
            '</svg>'


def _rect(height, width, radius, color):
    return \
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + \
            '<svg\n' + \
            'xmlns:dc="http://purl.org/dc/elements/1.1/"\n' + \
            'xmlns:cc="http://creativecommons.org/ns#"\n' + \
            'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n' + \
            'xmlns:svg="http://www.w3.org/2000/svg"\n' + \
            'xmlns="http://www.w3.org/2000/svg"\n' + \
            'version="1.1"\n' + \
            'width="%d"\n' % width + \
            'height="%d"\n' % height + \
            'viewBox="0 0 %d %d">\n' % (width, height) + \
            '<rect\n' + \
            'width="%d"\n' % width + \
            'height="%d"\n' % height + \
            'ry="%d"\n' % radius + \
            'x="0"\n' + \
            'y="0"\n' + \
            'style="fill:%s;fill-opacity:1;stroke:none;" />\n' % color + \
            '</svg>'


def _svg_str_to_pixbuf(svg_string):
    ''' Load pixbuf from SVG string '''
    pl = GdkPixbuf.PixbufLoader.new_with_type('svg') 
    pl.write(svg_string)
    pl.close()
    pixbuf = pl.get_pixbuf()
    return pixbuf
