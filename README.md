# DayZ Auto Retexture Generator

A desktop tool for generating color variants of DayZ item textures. Load a source texture, pick your colors, tweak adjustments, and batch-export recolored variants in seconds.

## Features

### Live Preview
- **Side-by-side preview** — Original and recolored textures update in real-time
- **Synchronized zoom & pan** — Scroll to zoom, drag to pan, both images stay in sync
- **Minimap overlay** — Shows viewport position when zoomed in
- **Always-on preview** — See adjustments applied even before selecting colors

### Color Modes
- **Colorize Mode** — Pick target colors from presets or a custom color picker, preserving original detail and luminance
- **Hue Shift Mode** — Generate evenly-spaced hue rotations with an interactive preview slider
- **5 preset palettes** — Military, Urban, Earth Tones, Survival, and Bright (8 colors each)
- **Adjustable strength** — Control how aggressively colors are applied

### Texture Adjustments
- **Brightness / Contrast / Saturation** — Fine-tune with sliders, live preview updates instantly
- **Mask support** — Load a grayscale mask to colorize specific regions only (white = colorize, black = keep original)
- **Wear & tear** — Apply procedural scratches, dirt, or weathering overlays with adjustable intensity
- **Normal map detection** — Warns you if you accidentally load a normal/specular map

### Config Generator Integration
- **Export to Config Generator** — Output PAA files named for auto-matching in the DayZ Retexture Config Generator
- Configurable mod folder, prefix, and item name with live filename preview

### File Support
- **Input** — PNG, TGA, PAA, JPG, BMP
- **Output** — PNG, TGA, or PAA (via DayZ Tools)
- **Auto-detect DayZ Tools** — Scans Steam library folders automatically
- **First-launch setup** — Guided DayZ Tools detection with manual path fallback

### UI
- **Tabbed interface** — Colors, Adjustments, and Output tabs keep controls organized
- **Dark/Light theme** — Toggle between themes, preference saved between sessions
- **Auto-update** — Checks GitHub for new releases and can update in-place

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
3. **Colors tab** — Choose a mode and select colors:
   - **Colorize** — pick from presets or add custom colors, click a swatch to preview
   - **Hue Shift** — set variant count and use the preview slider to scrub through shifts
4. **Adjustments tab** — Fine-tune brightness, contrast, saturation; load a mask; add wear & tear
5. **Output tab** — Set output folder, naming, and format; optionally enable Config Generator export
6. Click **Generate Textures**

Output files are named `{prefix}_{color}.{format}` and saved to your chosen folder.

---

built with <3 by Sean
