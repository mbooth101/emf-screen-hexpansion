# Screen Hexpansion

More screens is more better. Plug-in an auxialliary screen or two to maximise the amount of data you can display at a time! Or use them to create a multiocular Tildagon, just like everyone's favourite unicode glyph, the [multiocular O](https://en.wikipedia.org/wiki/Cyrillic_O_variants#Multiocular_O) "ꙮ".

## Firmware Install

If your Screen Hexpansion arrived uninitialised, or you need to manually re-flash the Hexpansion firmware for any reason, you can do so by inserting the Screen Hexpansion into port 2 of your Tildagon, and running the following commands:

```
cd emf-screen-hexpansion
mpremote mount EEPROM + run EEPROM/prepare_eeprom.py + cp EEPROM/app.mpy :/hexpansion/app.mpy
```

Once complete, the Screen Hexpansion may be inserted into any port. The script is just hard-coded to port 2 for flashing the firmware.

## License

This repo is MIT licensed and CERN Open Hardware licensed.
