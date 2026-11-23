from setuptools import setup

setup(
    name="OctoPrint-UnloadWhenDone",
    version="0.1.0",
    description="Per-print toggle to unload the filament after a successful print",
    packages=["octoprint_unloadwhendone"],
    include_package_data=True,
    package_data={"octoprint_unloadwhendone": ["static/js/*", "static/css/*", "templates/*"]},
    author="skandinaff",
    url="https://github.com/skandinaff/OctoPrint-UnloadWhenDone",
    license="AGPLv3",
    python_requires=">=3.9,<4",
    entry_points={"octoprint.plugin": ["unloadwhendone = octoprint_unloadwhendone"]},
)
