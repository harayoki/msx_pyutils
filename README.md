# MSX PyUtils

MSX PyUtils is a collection of Python-based tools and libraries designed to assist with various tasks related to the MSX computer platform.

# Projects

Each project has its own README with usage details.

## Python-based utilities

* [Basic Sc2/Sc4 Viewer](projects/basic_sc2_viewer/README.md): Builds a disk image that auto-runs a BASIC program to display SC2/SC4 images in MSX emulators or real hardware (via 2DD disks).
* [MSX Disk](projects/msxdisk/README.md): Creates MSX-compatible 2DD (720KiB) FAT12 disk images from specified files and folders.
* [MMSXX ASM Helper](projects/mmsxxasmhelper/README.md): WIP utility library exposing MSX Z80 mnemonics as Python callables.
* [SC2 Viewer ROM Tools](projects/sc2_viewer_rom/README.md): Tools to build MSX ROMs for viewing SCREEN 2 images (including a 32KiB toggle viewer and a scrolling MegaROM builder).
* [Simple SC2 Converter](projects/simple_sc2_converter/README.md): Converts PNG images into MSX Screen 2 (`.sc2`) binaries or palette-constrained PNG previews (no further feature updates planned).

# Repository structure

* `docs/`: Documentation assets for the repository.
* `projects/`: Project source folders (each with its own README).
* `techdocs/`: Technical notes and design documentation.
* `tests/`: Test assets and fixtures.
* `tools/`: Helper scripts and utilities.
* `requirements.in` / `requirements.txt`: Python dependency definitions for the Python tooling in this repo.
* `README.md` / `README_ja.md`: Top-level documentation (English/Japanese).

# Python requirements

This directory hosts Python (3.11 or later) based tools for the project.


# 依存関係のインストール

```
uv pip compile requirements.in -o requirements.txt
uv venv
uv pip sync requirements.txt
source .venv/Scripts/activate
```
