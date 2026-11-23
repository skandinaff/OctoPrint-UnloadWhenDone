# OctoPrint-UnloadWhenDone

Per-print toggle: unload the filament after a successful print (reheat to the print temperature → `M702` → cool down).

Arm/disarm from:
- the "Unload filament after print" button under Print / Pause / Cancel (a ⏏ icon in the navbar reminds you while it is armed);
- Telegram bot: `/ctrl` → "Unload ON" / "Unload OFF";
- any G-code sender (OctoApp, terminal): `@UNLOAD_ON`, `@UNLOAD_OFF`, `@UNLOAD_TOGGLE`, `@UNLOAD_STATUS`.

The toggle can be flipped at any time, also while printing: only its state at the end of the print counts.
It disarms itself after every print. Cancelled/failed prints never unload.

Note: `@` commands are not processed while printing from the printer's SD card; use the web UI button then.

## Printer compatibility

Tested on a Prusa i3 MK3 (Prusa firmware 3.14) with OctoPrint 2.0.1.

The default unload sequence is:

```
M109 S{temp}   ; reheat to the hotend temperature the print used
M702           ; unload filament
M104 S0        ; hotend off
```

`{temp}` is the last non-zero hotend target seen during the print (falls back to a configurable value).
On Marlin, `M702` needs `FILAMENT_LOAD_UNLOAD_GCODES` / `ADVANCED_PAUSE_FEATURE`; if your firmware lacks it,
replace it in the plugin settings with a plain retract, e.g. `G91` / `G1 E-100 F1200` / `G90`.

## Telegram

If the [Telegram plugin](https://plugins.octoprint.org/plugins/telegram/) is installed, the "⏏ Unload" custom
controls show up under `/ctrl`, and one message with the unload state is sent when a print starts
(enable "User Notification" for the chat in the Telegram plugin settings). This is optional.

## Install

Plugin Manager → Get More → from URL:
`https://github.com/skandinaff/OctoPrint-UnloadWhenDone/archive/main.zip`

## License

AGPLv3
