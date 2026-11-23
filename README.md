# OctoPrint-UnloadWhenDone

Per-print toggle: unload the filament after a successful print (reheat to the print temperature → `M702` → cool down).

Arm/disarm from:
- the "Unload filament after print" button under Print / Pause / Cancel (a ⏏ icon in the navbar reminds you while it is armed);
- Telegram bot: `/ctrl` → "Unload ON" / "Unload OFF";
- any G-code sender (OctoApp, terminal): `@UNLOAD_ON`, `@UNLOAD_OFF`, `@UNLOAD_TOGGLE`, `@UNLOAD_STATUS`.

The toggle can be flipped at any time, also while printing: only its state at the end of the print counts.
It disarms itself after every print. Cancelled/failed prints never unload.

Note: `@` commands are not processed while printing from the printer's SD card; use the web UI button then.

## Install

Plugin Manager → Get More → from URL:
`https://github.com/skandinaff/OctoPrint-UnloadWhenDone/archive/main.zip`

## License

AGPLv3
