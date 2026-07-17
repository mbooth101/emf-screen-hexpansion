"""
Copyright (c) 2026 Mat Booth.

This file is part of the Screen Hexpansion for the Tildagon
(see https://github.com/mbooth101/emf-screen-hexpansion).

License: MIT
"""
import app
import math
import time

from ctx import Context, RGB565_BYTESWAPPED
from machine import SoftSPI, SPI, Pin

from system.eventbus import eventbus
from system.scheduler.events import RequestForegroundPushEvent

class AuxScreen(app.App):

    # Increment this when making changes to the app that require the hexpansion to be re-flashed with the new code.
    VERSION = 1

    # Screen dimension maximums
    WIDTH = 240
    HEIGHT = 240

    # Cargo culted commands to initialise the GC9A01, the meaning of some of
    # these can be found in the datasheet, but most are mysterious and stolen
    # from other GC9A01 driver implementations
    INIT_CMDS = [
        ( 0xef, ),
        ( 0xeb, [ 0x14 ] ),
        ( 0xfe, ),
        ( 0xef, ),
        ( 0xeb, [ 0x14 ] ),
        ( 0x84, [ 0x40 ] ),
        ( 0x85, [ 0xff ] ),
        ( 0x86, [ 0xff ] ),
        ( 0x87, [ 0xff ] ),
        ( 0x88, [ 0x0a ] ),
        ( 0x89, [ 0x21 ] ),
        ( 0x8a, [ 0x00 ] ),
        ( 0x8b, [ 0x80 ] ),
        ( 0x8c, [ 0x01 ] ),
        ( 0x8d, [ 0x01 ] ),
        ( 0x8e, [ 0xff ] ),
        ( 0x8f, [ 0xff ] ),
        ( 0xb6, [ 0x00, 0x20 ] ),
        ( 0x90, [ 0x08, 0x08, 0x08, 0x08 ] ),
        ( 0xbd, [ 0x06 ] ),
        ( 0xbc, [ 0x00 ] ),
        ( 0xff, [ 0x60, 0x01, 0x04 ] ),
        ( 0xC3, [ 0x13 ] ),
        ( 0xC4, [ 0x13 ] ),
        ( 0xC9, [ 0x22 ] ),
        ( 0xbe, [ 0x11 ] ),
        ( 0xe1, [ 0x10, 0x0e ] ),
        ( 0xdf, [ 0x21, 0x0c, 0x02 ] ),
        ( 0xf0, [ 0x45, 0x09, 0x08, 0x08, 0x26, 0x2a ] ),
        ( 0xf1, [ 0x43, 0x70, 0x72, 0x36, 0x37, 0x6f ] ),
        ( 0xf2, [ 0x45, 0x09, 0x08, 0x08, 0x26, 0x2a ] ),
        ( 0xf3, [ 0x43, 0x70, 0x72, 0x36, 0x37, 0x6f ] ),
        ( 0xed, [ 0x1b, 0x0b ] ),
        ( 0xae, [ 0x77 ] ),
        ( 0xcd, [ 0x63 ] ),
        ( 0x70, [ 0x07, 0x07, 0x04, 0x0e, 0x0f, 0x09, 0x07, 0x08, 0x03 ] ),
        ( 0xe8, [ 0x34 ] ),
        ( 0x62, [ 0x18, 0x0D, 0x71, 0xED, 0x70, 0x70, 0x18, 0x0F, 0x71, 0xEF, 0x70, 0x70 ] ),
        ( 0x63, [ 0x18, 0x11, 0x71, 0xF1, 0x70, 0x70, 0x18, 0x13, 0x71, 0xF3, 0x70, 0x70 ] ),
        ( 0x64, [ 0x28, 0x29, 0xF1, 0x01, 0xF1, 0x00, 0x07 ] ),
        ( 0x66, [ 0x3C, 0x00, 0xCD, 0x67, 0x45, 0x45, 0x10, 0x00, 0x00, 0x00 ] ),
        ( 0x67, [ 0x00, 0x3C, 0x00, 0x00, 0x00, 0x01, 0x54, 0x10, 0x32, 0x98 ] ),
        ( 0x74, [ 0x10, 0x85, 0x80, 0x00, 0x00, 0x4E, 0x00 ] ),
        ( 0x98, [ 0x3e, 0x07 ] ),
        ( 0x35, ),
        ( 0x36, [ 0xC8 ] ),
        ( 0x3A, [ 0x05 ] ),
        ( 0x21, ),
        ( 0x11, None, 150 ),
        ( 0x29, None, 150 ),
    ]

    def __init__(self, config=None):
        super().__init__()

        # Config is mandatory, we're running from the EEPROM
        if config is None:
            raise TypeError
        self.config = config

        # Data/command select pin
        self.dc = config.pin[3]
        self.dc.init(mode=Pin.OUT, pull=0)

        # Chip select pin
        # Always pull low, there's only one device on the bus
        self.cs = config.pin[2]
        self.cs.init(mode=Pin.OUT, pull=0, value=0)

        # Initialise the SPI bus
        self.spi = SPI(1, baudrate=40 * 1000 * 1000,
            sck=config.pin[1], mosi=config.pin[0], miso=config.pin[2])

        # Fire intialisation sequence at the display
        for init_cmd in AuxScreen.INIT_CMDS:
            self._write_cmd(init_cmd[0])
            if len(init_cmd) > 1 and init_cmd[1]:
                self._write_data(init_cmd[1])
            if len(init_cmd) > 2 and init_cmd[2]:
                time.sleep_ms(init_cmd[2])

        # Blit the full frame
        self._column_addr_set(0, AuxScreen.WIDTH - 1)
        self._row_addr_set(0, AuxScreen.HEIGHT - 1)

        # Allocate a frame buffer 16 bits per pixel
        self._fb = bytearray(AuxScreen.WIDTH * AuxScreen.HEIGHT * 2)

        # Create a CTX Context for the frame buffer
        self._ctx = Context(width=AuxScreen.WIDTH, height=AuxScreen.HEIGHT,
            stride=AuxScreen.WIDTH * 2, format=RGB565_BYTESWAPPED, buffer=self._fb)

        # Does it expose additional methods for animation?
        self.capable = hasattr(self._ctx, "identity")

        self.foregrounded = False
        self.drawn = False

    def _write_cmd(self, cmd):
        self.dc.off()
        self.spi.write(bytes([cmd]))

    def _write_data(self, data):
        self.dc.on()
        self.spi.write(bytes(data))

    def _column_addr_set(self, start, end):
        self._write_cmd(0x2A) # CASET(2Ah)
        self._write_data([start >> 8, start & 0xFF, end >> 8, end & 0xFF])

    def _row_addr_set(self, start, end):
        self._write_cmd(0x2B) # PASET(2Bh)
        self._write_data([start >> 8, start & 0xFF, end >> 8, end & 0xFF])

    def _blit(self):
        self._write_cmd(0x2C) # RAMWR(2Ch)
        self._write_data(self._fb)

    def get_ctx(self):
        """Starts the frame and returns the context"""
        self._ctx.save()

        # Reset to identity matrix, I think the tildagon OS driver does this
        # because it's not doing a proper CTX end_frame() call
        if self.capable:
            self._ctx.identity()

        # Move the origin to the centre of the screen
        offset_x = AuxScreen.WIDTH / 2
        offset_y = AuxScreen.HEIGHT / 2
        self._ctx.apply_transform(1.0, 0.0, offset_x, 0.0, 1.0, offset_y, 0.0, 0.0, 1.0)

        # Rotate according to which hexpansion port we're plugged into
        factor = self.config.port - 2
        self._ctx.rotate(math.pi / 2 - factor * math.pi / 3)

        return self._ctx

    def end_frame(self):
        """Blits to the screen and ends the frame"""
        self._ctx.restore()
        self._blit()

        # From the tildagon OS driver:
        # display.end_frame() cannot call ctx_end_frame() directly here: that resets
        # rasterizer state, including the framebuffer clip bounds, which leaves
        # subsequent frames blank. Advance only the texture eviction clock.
        if self.capable:
            self._ctx.set_textureclock(self._ctx.textureclock() + 1)
        
    def update(self, delta):
        # Just draw the eye logo and terminate the app
        self._draw_eye(self.get_ctx())
        self.end_frame()
        self.terminate()

    def _draw_eye(self, ctx):
        ctx.gray(0.0).rectangle(-120, -120, 240, 240).fill()
        ctx.gray(0.95).arc(0, 0, 110, 0, 2 * math.pi, False).stroke()
        ctx.gray(0.95).arc(0, 0, 50, 0, 2 * math.pi, False).fill()
        ctx.gray(0.0).arc(0, 0, 20, 0, 2 * math.pi, False).fill()
        ctx.rgb(1, 0.84, 0).arc(-9, -9, 4, 0, 2 * math.pi, False).fill()
        ctx.gray(0.95).move_to(-110, 0).quad_to(0, -110, 110, 0).stroke()
        ctx.gray(0.95).move_to(-110, 0).quad_to(0, 110, 110, 0).stroke()


__app_export__ = AuxScreen # pylint: disable=invalid-name
