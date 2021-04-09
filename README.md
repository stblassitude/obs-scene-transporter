# OBS Scene Transporter

[![Build and Publish to PyPI](https://github.com/stblassitude/obs-scene-transporter/actions/workflows/publish-to-pypi.yml/badge.svg)](https://github.com/stblassitude/obs-scene-transporter/actions/workflows/publish-to-pypi.yml)

Package OBS Studio scenes into a convenient ZIP file, including all assets, and import them again.

## Overview

[OBS Studio](https://obsproject.com) can export the  JSON file for a scene collection, but it does not copy the images, video, etc. that might be used in that collection. Also, the JSON file will contain absolute paths that are unlikely to work on another computer. obs-scene-transporter will collect all referenced asset files and fix the paths to them in the JSON file.

In addition, the IDs of certain sources are updated on the fly to adapt them to the target operating system on import. OBS Studio uses platform-specific IDs for camera and screen sharing sources; when you import a scene collection that was created on Windows into a Linux system, the sources cannot be used and would need to be created from scratch. By patching the IDs on the fly, OBS Scene Transporter allows these sources to be used on another computer with minimal configuration. In particular, the positioning of the sources is maintained, and it is only necessary to select the correct camera or screen on the new computer.

## Installing and Running

Use [pip](https://docs.python.org/3/installing/index.html) to install this package:

```shell
$ python -m pip install obs-scene-transporter
```

The package installs a command-line tool `obs-scene-transporter` which you can run directly:
```shell
$ obs-scene-transporter -h
```

Alternatively, you can run the module:
```shell
$ python -m obs-scene-transporter -h
```

## Exporting a scene collection

Use the `list` command to obtain a list of scenes in OBS Studio:
```shell
$ obs-scene-transporter list
summer-conference
castle-wolfenstein-speedrun
```

Then use the `export` command to create a ZIP archive of the scene collection and all assets:
```shell
$ obs-scene-transporter summer-conference summer-conference.zip
```

## Importing a scene

Run the `ìmport` command to import a ZIP archive into OBS:
```shell
$ obs-scene-transporter summer-conference.zip
```

If you'd like to import the collection under a different name, use the `-n` option:
```shell
$ obs-scene-transporter -n fall-conference summer-conference.zip
```
