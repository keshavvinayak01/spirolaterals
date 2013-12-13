# g.py - spirolaterals globals
"""
    Copyright (C) 2010  Peter Hewitt

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

"""
import pygame

import utils


XO = False  # affects the pygame.display.set_mode() call only
app = 'Spirolaterals'
ver = '1.0'
ver = '1.1'
# new system - 32x24 display to allow scaling
ver = '1.2'
# smooth scaling, nos display, mouse, utils
ver = '1.3'
# moved nos & right buttons up .5 - looks better on XO
# smiley on win
ver = '1.4'
# utils.message now has drop shadow
# global gdelay & pause before 1st turtle move by setting tu.ms to current time
# improved smiley
# help on magician click
# gwins - add 1 to level each 5
ver = '1.5'  # <<<< Release 2
# no image scaling if factor  =  1.0 ie on XO box
ver = '1.6'
# fixed for widescreen
# smiley on left
ver = '2.0'
# new style - i.e g.py etc
# sugar cursor
# save level
# scale font
# no music
# right button -> decrease nos
ver = '2.1'
# floating point comparisons necessary on XO resolution
ver = '2.2'
# check cyan button b4 magician pic
ver = '2.3'
# cursor off on button press
ver = '2.4'
# speed -/+ (saved)
# No Esc on XO
# click on player pic for Big Pic - click to return
# blue button delay fixed
# black button funny fixed
# green & cyan buttons alternate
# smaller smiley
# help & score implemented
ver = '2.5'
# pattern library
# speed slider
# uses mouse_on_image for magician pic - see utils.ImgClickClass
ver = '2.6'
# fixed number click bug
ver = '2.7'
# no number glow when pattern finished
# smiley - less glow
ver = '2.8'  # <<<<Release 11
# pattern number displayed
ver = '2.9'
# help only on wrong digits
ver = '3.0'
# sugar
ver = '3.1'
# redraw implented
ver = '3.2'
# crash only shows after mouse move - fixed - g.crash_drawn
# red mouse after crash + help - fixed
# change help # -> 2 numbers - fixed
# blue button  =  new pattern but run button fails - fixed
ver = '3.2'
# help - if all correct, still show path
ver = '4.0'
# proper sugar cursor
# no frame rate
ver = '4.1'
# no version display on XO
# doesn't bother with pygame.mouse.get_focused() in run()
# help starts off by ensuring current numbers are in self.tu.current
ver = '4.2'
# drop g.current
ver = '4.3'
# g.help2 limit check fixed
# magician "holes" filled
ver = '21'
# flush_queue() added after button press and key press
ver = '22'
# flush_queue() doesn't use gtk on non-XO
ver = '23'
# removed patterns 9 & 10 - now have 122 patterns
ver = '24'
# sugar style

UP = (264, 273)
DOWN = (258, 274)
LEFT = (260, 276)
RIGHT = (262, 275)
CROSS = (259, 120)
CIRCLE = (265, 111)
SQUARE = (263, 32)
TICK = (257, 13)


def init():  # called by main()
    global redraw
    global screen, w, h, font1, font2, font3, clock
    global factor, offset, imgf, message, version_display
    global pos, pointer
    redraw = True
    version_display = False
    screen = pygame.display.get_surface()
    pygame.display.set_caption(app)
    screen.fill((70, 0, 70))
    pygame.display.flip()
    w, h = screen.get_size()
    if float(w) / float(h) > 1.5:  # widescreen
        offset = (w - 4 * h / 3) / 2  # we assume 4:3 - centre on widescreen
    else:
        h = int(.75 * w)  # allow for toolbar - works to 4:3
        offset = 0
    clock = pygame.time.Clock()
    factor = float(h) / 24  # measurement scaling factor (32x24 = design units)
    imgf = float(h) / 900  # image scaling factor; images built for 1200x900
    if pygame.font:
        t = int(54 * imgf)
        font1 = pygame.font.Font(None, t)
        t = int(72 * imgf)
        font2 = pygame.font.Font(None, t)
        t = int(46 * imgf)
        font3 = pygame.font.Font(None, t)
    message = ''
    pos = pygame.mouse.get_pos()
    pointer = utils.load_image('pointer.png', True)
    pygame.mouse.set_visible(False)

    # this activity only
    global x0, y0, x1, y1, goal, steps, pattern, delay, help1, help2, show_help
    global big, big_surface, score, slider, level, finale, player_surface
    global crash_drawn, magician, magician_c
    global bgd, box, dd, magician, turtle, crash, smiley, n, n_glow
    global n_cx0, n_cy0
    global n_dx, bw, sparkle
    x0 = sx(2.0)
    y0 = sy(1.1)  # left frame
    w, h = screen.get_size()
    if w > h:
        x1 = sx(16.8)
        y1 = sy(1.1)  # right frame
    else:
        x1 = sx(2.0)
        y1 = sy(17)  # right frame
    goal = []
    steps = 40  # number of steps to draw pic
    pattern = 1
    level = 1
    delay = (3 - level) * 400
    help1 = 0
    help2 = 0
    show_help = False
    score = 0
    finale = False
    crash_drawn = True  # used to make sure crash is drawn
    magician = utils.load_image('magician.png', True)
    magician_c = (sx(5.5), sy(20))
    sparkle = utils.load_image('sparkle.png', True)
    bgd = utils.load_image('sunset.jpg')
    box = utils.load_image('box.png', True)
    bw = box.get_width()
    s = bw - 2 * sy(1)
    player_surface = pygame.Surface((s, s))
    big = False
    big_surface = None
    dd = box.get_width() / 8  # turtle step size
    turtle = utils.load_image('turtle.png', True)
    crash = utils.load_image('crash.png', True)
    smiley = utils.load_image('smiley.png', True)
    n = []  # 1, 2, 3, 4, 5 images
    n_glow = []  # ... with glow
    for i in range(5):
        img = utils.load_image(str(i + 1) + '.png', True)
        n.append(img)
        img = utils.load_image(str(i + 1) + 'g.png', True)
        n_glow.append(img)
    if w > h:
        n_cx0 = sx(17.4) + n[3].get_width() / 2  # "4" is widest
        n_cy0 = sy(17)
        n_dx = sy(2.6)
    else:
        n_cx0 = sx(2.6) + n[3].get_width() / 2  # "4" is widest
        n_cy0 = sy(34)
        n_dx = sy(2.6)


def sx(f):  # scale x function
    return f * factor + offset


def sy(f):  # scale y function
    return f * factor
