"""
Copyright (c) 2026 Mat Booth.

This file is part of the Screen Hexpansion for the Tildagon
(see https://github.com/mbooth101/emf-screen-hexpansion).

License: MIT
"""
import app
import math

import display_aux

from events.input import Buttons, BUTTON_TYPES
from system.eventbus import eventbus
from system.hexpansion.config import HexpansionConfig
from system.hexpansion.events import HexpansionMountedEvent, HexpansionUnmountedEvent
from system.hexpansion.util import get_slots_by_vid_pid, get_app_by_slot


class ScreenTest(app.App):

    def __init__(self):
        self.button_states = Buttons(self)

        eventbus.on_async(HexpansionMountedEvent, self._mounted, self)
        eventbus.on_async(HexpansionUnmountedEvent, self._unmounted, self)

        self.aux_screen = self._detect_screen()

    def _detect_screen(self):
        screen_slots = get_slots_by_vid_pid(0x4D42, 0x5EE5)
        for slot in screen_slots:
            print(f"ScreenTest: Screen found in port {slot}")
        if screen_slots:
            print(f"ScreenTest: Using screen in slot {screen_slots[0]}")
            config = HexpansionConfig(screen_slots[0])
            display_aux.gfx_init(config)
            return screen_slots[0]
        else:
            print(f"ScreenTest: No screen found!")
            return 0

    def update(self, delta):
        # Exit the app
        if self.button_states.get(BUTTON_TYPES["CANCEL"]):
            self.button_states.clear()
            self.minimise()

    def draw(self, ctx):
        ctx.gray(0.0).rectangle(-120, -120, 240, 240).fill()

        ctx.save()
        ctx.font_size = 25
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.gray(0.95)
        ctx.move_to(0, -50).text("Screen Test")

        if self.aux_screen > 0:
            direction = (math.pi / 3) * self.aux_screen - (math.pi / 6)
            self._draw_arrow(ctx, direction)

            ctx.move_to(0, 50).text("Aux Screen In")
            ctx.move_to(0, 75).text(f"Port {self.aux_screen}")

        else:
            ctx.arc(0, 0, 30, 0, math.pi * 2, False).fill()

            ctx.move_to(0, 50).text("No Auxilliary")
            ctx.move_to(0, 75).text("Screens")

        ctx.restore()

        # Draw on the auxilliary screen if present
        if self.aux_screen:
            ctx_aux = display_aux.get_ctx()
            self.draw_aux(ctx_aux)
            display_aux.end_frame(ctx_aux)

    def draw_aux(self, ctx):
        ctx.gray(0.0).rectangle(-120, -120, 240, 240).fill()

        ctx.save()
        ctx.font_size = 25
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.gray(0.95)
        ctx.move_to(0, -50).text("Screen Test")

        direction = (math.pi / 3) * self.aux_screen - (math.pi / 6)
        self._draw_arrow(ctx, direction + math.pi)

        ctx.move_to(0, 50).text("Hello from")
        ctx.move_to(0, 75).text(f"port {self.aux_screen}!")

        ctx.restore()

    def _draw_arrow(self, ctx, direction):
        """Util to draw an arrow pointing in the direction given in radians"""
        ctx.save()
        ctx.rotate(direction)
        ctx.begin_path().move_to(0, -30)
        for vert in [ (-30, 0), (-15, 0), (-15, 30), (15, 30), (15, 0), (30, 0) ]:
            ctx.line_to(*vert)
        ctx.close_path().fill()
        ctx.restore()

    async def _mounted(self, _: HexpansionMountedEvent):
        self.aux_screen = self._detect_screen()

    async def _unmounted(self, e: HexpansionUnmountedEvent):
        if e.port == self.aux_screen:
            display_aux.gfx_deinit(self.aux_screen)
            self.aux_screen = 0


__app_export__ = ScreenTest # pylint: disable=invalid-name
