"""Unload When Done: unload the filament after the current print, armed per print.

The toggle can be flipped from:
  * the navbar button in the OctoPrint web UI,
  * the Telegram bot (/ctrl -> custom controls this plugin adds),
  * anything that can send G-code (OctoApp, terminal): @UNLOAD_ON / @UNLOAD_OFF /
    @UNLOAD_TOGGLE / @UNLOAD_STATUS.

When armed and the print finishes successfully, the unload sequence is appended to
the afterPrintDone script: reheat to the temperature the print used, unload, cool down.
After any print end (done, cancelled, failed) the toggle disarms itself.
"""

import re
import threading

import flask
import octoprint.plugin
from octoprint.events import Events

CONTROL_GROUP_NAME = "Unload filament after print"
AT_COMMANDS = {"UNLOAD_ON", "UNLOAD_OFF", "UNLOAD_TOGGLE", "UNLOAD_STATUS"}
TEMP_RE = re.compile(r"^M10[49]\b.*?\bS(\d+(?:\.\d+)?)", re.IGNORECASE)
TOOL_RE = re.compile(r"\bT(\d+)\b", re.IGNORECASE)


class UnloadWhenDonePlugin(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.EventHandlerPlugin,
):
    def __init__(self):
        self._lock = threading.RLock()
        self._armed = False
        self._print_temp = None  # last non-zero hotend target seen during the job

    # ------------------------------------------------------------------ settings

    def get_settings_defaults(self):
        return {
            "fallback_temp": 215,
            "min_temp": 170,
            "unload_script": "M117 Unloading filament...\n"
            "M109 S{temp}\n"
            "M702\n"
            "M104 S0\n"
            "M117 Filament unloaded",
            "lcd_feedback": True,
            "remind_on_start": True,
            "add_custom_controls": True,
        }

    def is_template_autoescaped(self):
        return True

    # ------------------------------------------------------------------ startup

    def on_after_startup(self):
        if self._settings.get_boolean(["add_custom_controls"]):
            self._ensure_custom_controls()

    def _ensure_custom_controls(self):
        """Add a custom-controls group so Telegram's /ctrl (and the Control tab) can arm it."""
        controls = self._settings.global_get(["controls"]) or []
        if any(isinstance(c, dict) and c.get("name") == CONTROL_GROUP_NAME for c in controls):
            return
        controls.append(
            {
                "name": CONTROL_GROUP_NAME,
                "layout": "horizontal",
                "children": [
                    {"name": "Unload ON", "command": "@UNLOAD_ON"},
                    {"name": "Unload OFF", "command": "@UNLOAD_OFF"},
                ],
            }
        )
        self._settings.global_set(["controls"], controls)
        self._settings.save()
        self._logger.info("Added custom controls group '%s'", CONTROL_GROUP_NAME)

    # ------------------------------------------------------------------ state

    def _set_armed(self, value, source):
        with self._lock:
            changed = self._armed != value
            self._armed = value
        self._logger.info("Unload after print %s (via %s)", "ARMED" if value else "disarmed", source)
        self._push_state()
        if changed or source in ("gcode", "status"):
            self._lcd("Unload after: ON" if value else "Unload after: OFF")

    def _state_text(self):
        if self._armed:
            return "⏏ Филамент будет выгружен после печати"
        return "Филамент НЕ будет выгружен после печати"

    def _push_state(self):
        self._plugin_manager.send_plugin_message(self._identifier, {"armed": self._armed})

    def _lcd(self, text):
        if self._settings.get_boolean(["lcd_feedback"]) and self._printer.is_operational():
            self._printer.commands(f"M117 {text[:20]}", tags={"source:plugin"})

    def _telegram(self, text):
        plugin = self._plugin_manager.get_plugin_info("telegram", require_enabled=True)
        if plugin is None or plugin.implementation is None:
            return
        try:
            plugin.implementation.on_event("UserNotif", {"UserNotif": text})
        except Exception:
            self._logger.exception("Could not send Telegram notification")

    # ------------------------------------------------------------------ API (web UI)

    def is_api_protected(self):
        return True

    def get_api_commands(self):
        return {"arm": [], "disarm": [], "toggle": []}

    def on_api_command(self, command, data):
        if command == "arm":
            self._set_armed(True, "web")
        elif command == "disarm":
            self._set_armed(False, "web")
        elif command == "toggle":
            self._set_armed(not self._armed, "web")
        return flask.jsonify(armed=self._armed)

    def on_api_get(self, request):
        return flask.jsonify(armed=self._armed, print_temp=self._print_temp)

    # ------------------------------------------------------------------ hooks

    def hook_atcommand(self, comm, phase, command, parameters, tags=None, *args, **kwargs):
        cmd = command.upper()
        if cmd not in AT_COMMANDS:
            return
        if cmd == "UNLOAD_ON":
            self._set_armed(True, "gcode")
        elif cmd == "UNLOAD_OFF":
            self._set_armed(False, "gcode")
        elif cmd == "UNLOAD_TOGGLE":
            self._set_armed(not self._armed, "gcode")
        else:
            self._set_armed(self._armed, "status")

    def hook_gcode_sent(self, comm, phase, cmd, cmd_type, gcode, *args, **kwargs):
        """Remember the hotend temperature the print is using."""
        if gcode not in ("M104", "M109") or not self._printer.is_printing():
            return
        m = TEMP_RE.match(cmd)
        if not m:
            return
        tool = TOOL_RE.search(cmd)
        if tool and tool.group(1) != "0":
            return
        temp = float(m.group(1))
        if temp > 0:
            self._print_temp = temp

    def hook_scripts(self, comm, script_type, script_name, *args, **kwargs):
        if script_type != "gcode" or script_name != "afterPrintDone":
            return None
        with self._lock:
            if not self._armed:
                return None
            self._armed = False

        temp = self._print_temp
        min_temp = self._settings.get_float(["min_temp"]) or 170
        if temp is None or temp < min_temp:
            temp = self._settings.get_float(["fallback_temp"]) or 215
        temp = int(round(temp))

        script = self._settings.get(["unload_script"]).replace("{temp}", str(temp))
        lines = [line.strip() for line in script.splitlines() if line.strip()]
        self._logger.info("Print done, unloading filament at %s°C", temp)
        self._push_state()
        return None, lines

    # ------------------------------------------------------------------ events

    def on_event(self, event, payload):
        if event == Events.PRINT_STARTED:
            self._print_temp = None
            self._push_state()
            if self._settings.get_boolean(["remind_on_start"]):
                # LCD shows print progress now; only remind via Telegram.
                hint = "" if self._armed else " (включить: /ctrl)"
                self._telegram(self._state_text() + hint)
        elif event in (Events.PRINT_FAILED, Events.PRINT_CANCELLED):
            with self._lock:
                was_armed = self._armed
                self._armed = False
            if was_armed:
                self._logger.info("Print ended (%s), not unloading; disarmed", event)
                self._push_state()
        elif event == Events.CLIENT_OPENED:
            self._push_state()

    # ------------------------------------------------------------------ UI

    def get_assets(self):
        return {"js": ["js/unloadwhendone.js"], "css": ["css/unloadwhendone.css"]}

    def get_template_configs(self):
        return [
            {"type": "navbar", "custom_bindings": True},
            {"type": "settings", "custom_bindings": False},
        ]


    # ------------------------------------------------------------------ software update

    def get_update_information(self):
        return {
            "unloadwhendone": {
                "displayName": "Unload When Done",
                "displayVersion": self._plugin_version,
                "type": "github_release",
                "user": "skandinaff",
                "repo": "OctoPrint-UnloadWhenDone",
                "current": self._plugin_version,
                "pip": "https://github.com/skandinaff/OctoPrint-UnloadWhenDone/archive/{target_version}.zip",
            }
        }


__plugin_name__ = "Unload When Done"
__plugin_pythoncompat__ = ">=3.9,<4"
__plugin_description__ = "Per-print toggle to unload the filament after a successful print"
__plugin_author__ = "skandinaff"
__plugin_url__ = "https://github.com/skandinaff/OctoPrint-UnloadWhenDone"
__plugin_license__ = "AGPLv3"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = UnloadWhenDonePlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.atcommand.queuing": __plugin_implementation__.hook_atcommand,
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.hook_gcode_sent,
        "octoprint.comm.protocol.scripts": __plugin_implementation__.hook_scripts,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
    }
