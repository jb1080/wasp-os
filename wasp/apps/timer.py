# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2020 Wolfgang Ginolas
"""Timer Application
~~~~~~~~~~~~~~~~~~~~

An application to set a vibration in a specified amount of time. Like a kitchen timer.

    .. figure:: res/TimerApp.png
        :width: 179

        Screenshot of the Timer Application

"""

import wasp
import fonts
import time
import widgets
import math
from micropython import const

# 2-bit RLE, generated from res/timer_icon.png, 345 bytes
icon = (
    b'\x02'
    b'`@'
    b'?\xff\r@\xb4I?\x14Q?\rW?\x08[?'
    b'\x04_?\x00c<Q\xc3Q:L\xc7\x01\xc7L8'
    b'K\xc9\x01\xc9K6J\xcb\x01\xcbJ4I\xcd\x01\xcd'
    b'I2I\xddI0I\xc3\x01\xd7\x01\xc3I.H\xc6'
    b'\x01\xd5\x01\xc6H-H\xe3H,H\xd2\x01\xd2H+'
    b'G\xd2\x03\xd2G*G\xd2\x05\xd2G)G\xd2\x05\xd2'
    b"G(G\xc2\x01\xcf\x07\xcf\x01\xc2G'G\xc3\x01\xce"
    b"\x07\xce\x01\xc3G'F\xd3\x07\xd3F&G\xd3\x07\xd3"
    b'G%F\xd4\x07\xd4F%F\xd4\x07\xd4F%F\xd4'
    b'\x07\xd4F$G\xd4\x07\xd4G#G\xd4\x07\xd4G#'
    b'G\xd4\x07\xd4G#F\xd5\x07\xd5F#F\xc1\x04\xd0'
    b'\x07\xd0\x04\xc1F#F\xd5\x07\xd5F#G\xd4\x07\xd4'
    b'G#G\xd4\x07\xd4G#G\xd4\x07\xd4G$F\xd4'
    b'\x07\xd4F%F\xd4\x07\xd4F%F\xd4\x07\xd4F%'
    b"G\xd3\x07\xd3G%G\xd3\x07\xd3F'G\xc3\x01\xce"
    b"\x07\xce\x01\xc3G'G\xc2\x01\xcf\x07\xcf\x01\xc2G("
    b'G\xd2\x05\xd2G)G\xd3\x03\xd3G*G\xe7G+'
    b'H\xe5H,G\xe5G-H\xc6\x01\xdcH.H\xc4'
    b'\x01\xd6\x01\xc5H0I\xda\x01\xc2I1J\xcd\x01\xcd'
    b'J2K\xcb\x01\xcbK4K\xca\x01\xc9L5N\xc7'
    b'\x01\xc7N5S\xc5S5k5k5k5k5'
    b'k5k\x1b'
)

_STOPPED = const(0)
_RUNNING = const(1)
_RINGING = const(2)

_BUTTON_Y = const(200)

class TimerApp():
    """Allows the user to set a vibration alarm.
    """
    NAME = 'Timer'
    ICON = icon

    def __init__(self):
        """Initialize the application."""
        self.minutes = widgets.Spinner(50, 60, 0, 99, 2)
        self.seconds = widgets.Spinner(130, 60, 0, 59, 2)
        self.current_alarm = None

        self.minutes.value = 10
        self.state = _STOPPED

    def foreground(self):
        """Activate the application."""
        self._draw()
        wasp.system.request_event(wasp.EventMask.TOUCH)
        wasp.system.request_tick(1000)

    def background(self):
        """De-activate the application."""
        if self.state == _RINGING:
            self.state = _STOPPED

    def tick(self, ticks):
        """Notify the application that its periodic tick is due."""
        if self.state == _RINGING:
            wasp.watch.vibrator.pulse(duty=50, ms=500)
            wasp.system.keep_awake()
        self._update()

    def touch(self, event):
        """Notify the application of a touchscreen touch event."""
        if self.state == _RINGING:
            mute = wasp.watch.display.mute
            mute(True)
            self._stop()
            mute(False)
        elif self.state == _RUNNING:
            self._stop()
        else:  # _STOPPED
            if self.minutes.touch(event) or self.seconds.touch(event):
                pass
            else:
                y = event[2]
                if y >= _BUTTON_Y:
                    self._start()


    def _start(self):
        self.state = _RUNNING
        now = wasp.watch.rtc.time()
        self.current_alarm = now + self.minutes.value * 60 + self.seconds.value
        wasp.system.set_alarm(self.current_alarm, self._alert)
        self._draw()

    def _stop(self):
        self.state = _STOPPED
        wasp.system.cancel_alarm(self.current_alarm, self._alert)
        self._draw()

    def _draw(self):
        """Draw the display from scratch."""
        draw = wasp.watch.drawable
        draw.fill()
        sbar = wasp.system.bar
        sbar.clock = True
        sbar.draw()

        if self.state == _RINGING:
            draw.set_font(fonts.sans24)
            draw.string(self.NAME, 0, 150, width=240)
            draw.blit(icon, 73, 50)
        elif self.state == _RUNNING:
            self._draw_stop(104, _BUTTON_Y)
            draw.string(':', 110, 120-14, width=20)
            self._update()
        else:  # _STOPPED
            draw.set_font(fonts.sans28)
            draw.string(':', 110, 120-14, width=20)

            self.minutes.draw()
            self.seconds.draw()

            self._draw_play(114, _BUTTON_Y)

    def _update(self):
        wasp.system.bar.update()
        draw = wasp.watch.drawable
        if self.state == _RUNNING:
            now = wasp.watch.rtc.time()
            s = self.current_alarm - now
            if s<0:
                s = 0
            m = str(math.floor(s // 60))
            s = str(math.floor(s) % 60)
            if len(m) < 2:
                m = '0' + m
            if len(s) < 2:
                s = '0' + s
            draw.set_font(fonts.sans28)
            draw.string(m, 50, 120-14, width=60)
            draw.string(s, 130, 120-14, width=60)

    def _draw_play(self, x, y):
        draw = wasp.watch.drawable
        for i in range(0,20):
            draw.fill(0xffff, x+i, y+i, 1, 40 - 2*i)

    def _draw_stop(self, x, y):
        wasp.watch.drawable.fill(0xffff, x, y, 40, 40)

    def _alert(self):
        self.state = _RINGING
        wasp.system.wake()
        wasp.system.switch(self)
