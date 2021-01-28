# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2020 Daniel Thompson
# Copyright (C) 2020 Joris Warmbier
"""Alarm Application
~~~~~~~~~~~~~~~~~~~~
Modified Icon
An application to set a vibration alarm. All settings can be accessed from the Watch UI.

    .. figure:: res/AlarmApp.png
        :width: 179

        Screenshot of the Alarm Application

"""

import wasp
import fonts
import time
import widgets

# 2-bit RLE, generated from /home/pi/Downloads/alarm_icon.png, 386 bytes
icon = (
    b'\x02'
    b'`@'
    b'\x17\xc7#\xc7-\xcb\x1f\xcb)\xcf\x1b\xcf&\xcf\n@'
    b'\xb4I\x0b\xce$\xce\x08Q\t\xcd"\xcd\x07W\x07\xcd'
    b'!\xcc\x06[\x07\xcb \xcb\x06_\x06\xcb\x1f\xca\x05c'
    b'\x05\xca\x1e\xca\x05Q\xc3Q\x05\xca\x1d\xc9\x05L\xcfL'
    b'\x05\xc9\x1d\xc8\x05K\xd3K\x05\xc8\x1d\xc7\x05J\xd7J'
    b'\x05\xc7\x1d\xc7\x04I\xdbI\x05\xc6\x1d\xc6\x04I\xcc\x05'
    b'\xccI\x04\xc6\x1d\xc5\x04I\xcd\x05\xcdI\x04\xc5\x1e\xc4'
    b'\x03H\xce\x07\xceH\x04\xc3\x1f\xc3\x04H\xce\x07\xceH'
    b'\x04\xc3\x1f\xc3\x03H\xcf\x07\xcfH\x04\xc1!\xc1\x04G'
    b'\xd0\x07\xd0G\x04\xc1%G\xd1\x07\xd1G)G\xd1\x07'
    b"\xd1G(G\xd2\x07\xd2G'G\xd2\x07\xd2G'F"
    b'\xd3\x07\xd3F&G\xd3\x07\xd3G%F\xd4\x07\xd4F'
    b'%F\xd4\x07\xd4F%F\xd4\x07\xd4F$G\xd4\x07'
    b'\xd4G#G\xd4\x07\xd4G#G\xd4\x07\xd4G#F'
    b'\xd4\x08\xd5F#F\xd3\t\xd5F#F\xd2\t\xd6F'
    b'#G\xd0\n\xd5G#G\xcf\n\xd6G#G\xce\n'
    b'\xd7G$F\xce\t\xd8F%F\xce\x08\xd9F%F'
    b'\xcd\x08\xdaF%G\xcc\x07\xdaG%G\xcc\x06\xdbF'
    b"'G\xcc\x03\xdcG'G\xebG(G\xe9G)G"
    b'\xe9G*G\xe7G+H\xe5H,G\xe5G-H'
    b'\xe3H.H\xe1H0I\xddI2I\xdbI3K'
    b'\xd7K2M\xd4N0Q\xcfQ.W\xc5W,u'
    b'+H\x03_\x03H*H\x05]\x05H)G\tW'
    b'\tG*E\x0cS\x0cE,C\x11K\x11C\x17'
)

class AlarmApp():
    """Allows the user to set a vibration alarm.
    """
    NAME = 'Alarm'
    ICON = icon

    def __init__(self):
        """Initialize the application."""
        self.active = widgets.Checkbox(104, 200)
        self.hours = widgets.Spinner(50, 60, 0, 23, 2)
        self.minutes = widgets.Spinner(130, 60, 0, 59, 2)

        self.hours.value = 7
        self.ringing = False

    def foreground(self):
        """Activate the application."""
        self._draw()
        wasp.system.request_event(wasp.EventMask.TOUCH)
        wasp.system.request_tick(1000)
        if self.active.state:
            wasp.system.cancel_alarm(self.current_alarm, self._alert)

    def background(self):
        """De-activate the application."""
        if self.active.state:
            self._set_current_alarm()
            wasp.system.set_alarm(self.current_alarm, self._alert)
            if self.ringing:
                self.ringing = False

    def tick(self, ticks):
        """Notify the application that its periodic tick is due."""
        if self.ringing:
            wasp.watch.vibrator.pulse(duty=50, ms=500)
            wasp.system.keep_awake()
        else:
            wasp.system.bar.update()

    def touch(self, event):
        """Notify the application of a touchscreen touch event."""
        if self.ringing:
            mute = wasp.watch.display.mute
            self.ringing = False
            mute(True)
            self._draw()
            mute(False)
        elif self.hours.touch(event) or self.minutes.touch(event) or \
             self.active.touch(event):
            pass

    def _draw(self):
        """Draw the display from scratch."""
        draw = wasp.watch.drawable
        if not self.ringing:
            draw.fill()

            sbar = wasp.system.bar
            sbar.clock = True
            sbar.draw()

            draw.set_font(fonts.sans28)
            draw.string(':', 110, 120-14, width=20)

            self.active.draw()
            self.hours.draw()
            self.minutes.draw()
        else:
            draw.fill()
            draw.set_font(fonts.sans24)
            draw.string("Alarm", 0, 150, width=240)
            draw.blit(icon, 73, 50)

    def _alert(self):
        self.ringing = True
        wasp.system.wake()
        wasp.system.switch(self)

    def _set_current_alarm(self):
        now = wasp.watch.rtc.get_localtime()
        yyyy = now[0]
        mm = now[1]
        dd = now[2]
        HH = self.hours.value
        MM = self.minutes.value
        if HH < now[3] or (HH == now[3] and MM <= now[4]):
            dd += 1
        self.current_alarm = (time.mktime((yyyy, mm, dd, HH, MM, 0, 0, 0, 0)))
