# DayZ Auto Retexture Generator

A desktop tool for generating color variants of DayZ item textures. Load a source texture, pick your colors, and batch-export recolored variants in seconds.

## Features

- **Colorize Mode** — Pick target colors from presets or a custom color picker, and recolor textures while preserving original detail and luminance
- **Hue Shift Mode** — Automatically generate evenly-spaced hue rotations around the color wheel
- **PAA Support** — Read and write DayZ's PAA texture format directly (requires DayZ Tools)
- **Multiple Formats** — Input/output support for PNG, TGA, PAA, JPG, and BMP
- **Auto-Detect DayZ Tools** — Scans Steam library folders to find ImageToPAA.exe automatically
- **Preset Color Palettes** — Military, Urban, Earth Tones, Survival, and Bright presets with 8 colors each
- **Adjustable Strength** — Control how aggressively colors are applied (10–100%)
- **Dark/Light Theme** — Toggle between themes, preference is saved between sessions
- **Auto-Update** — Checks GitHub for new releases and can update in-place

## Getting Started

### Option 1: Download the exe
Grab the latest `DayZ Auto Retexture Generator.exe` from [Releases](https://github.com/SeanML8/DayZ-Auto-Retexture-Generator/releases).

### Option 2: Run from source
```
pip install Pillow numpy
python texture_maker.py
```

## Requirements

- **DayZ Tools** (via Steam) — needed for PAA file conversion
- **Python 3.10+** (if running from source)
- **Pillow** and **numpy** (if running from source)

## Usage

1. Launch the app — on first run it will auto-detect your DayZ Tools installation
2. Click **Browse** to select a source texture (PNG, TGA, PAA, etc.)
3. Choose a mode:
   - **Colorize** — select colors from presets or add custom colors
   - **Hue Shift** — set the number of variants to generate
4. Set your output folder, filename prefix, and format
5. Click **Generate Textures**

Output files are named `{prefix}_{color}.{format}` and saved to your chosen folder.

---

built with <3 by Sean
