# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2020 Daniel Thompson

"""Digital clock
~~~~~~~~~~~~~~~~
Modified version of Daniel Thompson's Digital clock.
Used purlupar's literal clock as base for a red and white themed literal clock.
Code is a mess, needs to be tidied.
Shows a time (as HH:MM) together with a battery meter and the date.

.. figure:: res/ClockApp.png
    :width: 179
"""

import wasp
import icons
import fonts.clock as digits
import fonts.sans36 as sans36
import fonts.sans24 as sans24

DIGITS = (
        digits.clock_0, digits.clock_1, digits.clock_2, digits.clock_3,
        digits.clock_4, digits.clock_5, digits.clock_6, digits.clock_7,
        digits.clock_8, digits.clock_9
)


MONTH = '010203040506070809101112'

class ClockApp():
    """Simple digital clock application."""
    NAME = 'Clock'
    ICON = icons.clock
    
    def battery(self):
        draw = wasp.watch.drawable
        h = wasp.watch.battery.level() * 2
        c = 0xffff
        if wasp.watch.battery.charging():
            c = 0xf800
        draw.fill(c, 235, 1, 5, h) 

    def foreground(self):
        """Activate the application.

        Configure the status bar, redraw the display and request a periodic
        tick callback every second.
        """
        wasp.system.bar.clock = False
        self._draw(True)
        wasp.system.request_tick(1000)
        self.battery()

    def sleep(self):
        """Prepare to enter the low power mode.

        :returns: True, which tells the system manager not to automatically
                  switch to the default application before sleeping.
        """
        return True

    def wake(self):
        """Return from low power mode.

        Time will have changes whilst we have been asleep so we must
        udpate the display (but there is no need for a full redraw because
        the display RAM is preserved during a sleep.
        """
        self._draw()
        self.battery()

    def tick(self, ticks):
        """Periodic callback to update the display."""
        self._draw()

    def _draw(self, redraw=False):
        """Draw or lazily update the display.

        The updates are as lazy by default and avoid spending time redrawing
        if the time on display has not changed. However if redraw is set to
        True then a full redraw is be performed.
        """
        draw = wasp.watch.drawable
        hi =  wasp.system.theme('bright')
        lo =  wasp.system.theme('mid')
        mid = draw.lighten(lo, 1)

        if redraw:
            now = wasp.watch.rtc.get_localtime()

            # Clear the display and draw that static parts of the watch face
            draw.fill()
            #draw.blit(digits.clock_colon, 2*48, 120, fg=mid)
            # Redraw the status bar
            #wasp.system.bar.draw()
            self.battery()
             
        else:
            # The update is doubly lazy... we update the status bar and if
            # the status bus update reports a change in the time of day 
            # then we compare the minute on display to make sure we 
            # only update the main clock once per minute.
            now = wasp.watch.rtc.get_localtime()
            if not now or self._min == now[4]:
                # Skip the update
                self.battery()
                return

        draw = wasp.watch.drawable
        month = now[1] - 1
        month = MONTH[month*2:(month+1)*2]

        stunda = ["twelve", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven"]
        minuta = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
        self._min = now[4]
        if now[4] == 0:
            say = ("", "", stunda[now[3] % 12])
        elif now[4] == 15:
            say = ("quarter", "after", "", stunda[now[3] % 12])
        elif now[4] == 30:
            say = ("", stunda[(now[3]) % 12], "thirty")
        elif 0 < now[4] < 21:
            say = (minuta[now[4]], "after", "", stunda[now[3] % 12])
        elif 30 < now[4] < 40:
            say = (stunda[(now[3]) % 12], "", "thirty", minuta[now[4]-30])
        elif 20 < now[4] < 30:
            say = (minuta[30-now[4]], "till ", stunda[(now[3]) % 12], "thirty")
        elif now[4] == 45:
            say = ("quarter", "till", "", stunda[(now[3]+1) % 12])
        elif 39 < now[4] < 60:
            say = (minuta[60-now[4]], "till", "", stunda[(now[3]+1) % 12])
        else:
            say = ("s", "h", "i t", now[4])
        
        draw.fill(0)
        self.battery()
        draw.set_color(0xf800, bg=0xffff)
        draw.set_font(sans36)
        draw.string(say[0], 0, 20)
        draw.string("{}{}".format(say[1],say[2]), 0, 80)
        draw.string(say[3], 0, 140)
        draw.set_color(0xffff, bg=0x0000)
        draw.set_font(sans24)
        draw.string("{}{}:{}{}        {}/{}".format(now[3] // 10, now[3] % 10,now[4] // 10, now[4] % 10, month, now[2]), 0, 200) 
        return True
