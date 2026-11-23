---
layout: plugin

id: unloadwhendone
title: Unload When Done
description: Per-print toggle to unload the filament after a successful print.
authors:
- skandinaff
license: AGPLv3

date: 2026-11-23

homepage: https://github.com/skandinaff/OctoPrint-UnloadWhenDone
source: https://github.com/skandinaff/OctoPrint-UnloadWhenDone
archive: https://github.com/skandinaff/OctoPrint-UnloadWhenDone/archive/main.zip

tags:
- filament
- unload
- telegram

compatibility:
  octoprint:
  - ">=1.11.2"
  os:
  - linux
  - windows
  - macos
  - freebsd
  python: ">=3.9,<4"
---

Adds a toggle under Print / Pause / Cancel: when armed, the filament is unloaded after the
current print finishes successfully (reheat to the print temperature, unload, cool down).
The toggle disarms itself after every print and can also be flipped from Telegram (`/ctrl`)
or any G-code sender (`@UNLOAD_ON` / `@UNLOAD_OFF`).
