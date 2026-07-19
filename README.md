# Screen Hexpansion

More screens is more better. Plug-in an auxialliary screen or two to maximise the amount of data you can display at a time! Or use them to create a multiocular Tildagon, just like everyone's favourite unicode glyph, the [multiocular O](https://en.wikipedia.org/wiki/Cyrillic_O_variants#Multiocular_O) "ꙮ".

## Firmware Install/Update

### Over-The-Air

You can initialise (and subsequently update) the Screen Hexpansion's firmware using the Tildagon badge's built-in "Hexpansions" app. Select the port it's plugged into and enter the VID `0x4D42` and PID `0x5EE5` to get the correct firmware.

### Manually

If you need to manually re-flash the Hexpansion firmware for any reason, or you want to install custom firmware, you can do so by inserting the Screen Hexpansion into port 2 of your Tildagon, and running the following commands:

```
cd emf-screen-hexpansion
mpremote mount EEPROM + run EEPROM/prepare_eeprom.py + cp EEPROM/app.mpy :/hexpansion/app.mpy
```

Once complete, the Screen Hexpansion may be inserted into any port. The script is just hard-coded to port 2 for flashing the firmware.

## License

This repo is MIT licensed and CERN Open Hardware licensed.
