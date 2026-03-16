# DayZ Auto Retexture Generator

A desktop tool for generating color variants of DayZ item textures. Load a source texture, pick your colors, paint masks for fine detail, and batch-export recolored variants in seconds.

## Features

### Live Preview
- **Side-by-side preview** — Original and recolored textures update in real-time
- **Synchronized zoom & pan** — Scroll to zoom, drag to pan, both images stay in sync
- **Pan past edges** — Zoom in and pan beyond image borders for comfortable edge editing
- **Minimap overlay** — Shows viewport position when zoomed in

### Color Picker
- **Color square** — HSV color square with hue bar for precise color selection
- **Hex input** — Enter hex codes directly
- **Eyedropper tool** — Pick colors directly from the loaded texture
- **Named colors** — Name your colors when adding, or double-click to rename later
- **Color presets** — Create, save, load, and delete named color presets
- **All Saved Colors** — Permanent preset that auto-collects every color you add
- **Auto-save** — Selected colors persist across sessions

### Zones System
- **Multi-zone colorization** — Create named zones (e.g., "Fabric", "Straps", "Buckles") with independent colors
- **Base zone** — First zone covers the entire texture automatically, additional zones paint over specific areas
- **Per-zone adjustments** — Each zone has its own brightness, contrast, saturation, and color strength
- **Set Color dialog** — Full color picker with saved swatches, presets, and strength control
- **Color sets** — Snapshot all zone colors as a set, generate one output per set

### Paint Mask Tools
- **Paint / Erase** — Brush tool with adjustable size to define zone areas
- **Fill** — Flood fill enclosed regions within a mask
- **Eyedropper** — Pick a color from the texture and set it as the zone's color
- **Soften** — Blur mask edges for smooth transitions between zones
- **Invert / Fill All / Clear All** — Quick mask operations
- **Undo (Ctrl+Z)** — Up to 20 levels of mask undo
- **Right-click pan** — Pan the image while in paint mode
- **Colored overlays** — See each zone's mask tinted with its actual color on the original preview
- **Tooltips** — Hover over any tool for a description of what it does

### PAA Viewer / Converter
- **Browse textures** — Open any file and navigate through all textures in the folder with arrow keys
- **Zoom & pan** — Scroll to zoom, drag to pan, same controls as the main preview
- **Convert single files** — PAA to PNG or PNG to PAA with save-as dialog
- **Batch convert** — Convert all PAAs in a folder to PNG (or vice versa) with progress bar
- **Persistent disk cache** — PAA conversions are cached so repeat visits load instantly
- **Background preloading** — Adjacent files preload for smooth navigation
- **Always on top** — Viewer stays above the main tool

### RVMAT Editor
- **Visual editor** — Edit ambient, diffuse, emissive, specular colors with live color preview swatches
- **Specular power & shaders** — Numeric and text inputs for material properties
- **Texture stages** — View and edit texture paths for each stage, browse for PAA/PNG files
- **Add/remove stages** — Modify the number of texture stages
- **Raw text editor** — Full raw RVMAT text editor for advanced changes
- **Sync buttons** — Apply between visual and raw editors in either direction
- **New / Open / Save** — Full file management with DayZ-standard defaults
- **Help button** — Built-in guide explaining material properties and texture stages

### Color Modes
- **Colorize Mode** — Pick target colors, preserving original detail and luminance
- **Hue Shift Mode** — Generate evenly-spaced hue rotations with an interactive preview slider
- **Adjustable strength** — Control how aggressively colors are applied

### Texture Adjustments
- **Brightness / Contrast / Saturation** — Fine-tune with sliders, per-zone when zones are enabled
- **Base mask support** — Load a grayscale mask to restrict all zones to specific regions
- **Wear & tear** — Apply overlay-based wear with 27 bundled overlays, desaturation in worn areas
- **Custom overlays** — Load your own wear overlay images
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
- **Tooltips** — Hover over buttons and tools for helpful descriptions
- **Auto-update** — Checks GitHub for new releases with changelog dialog and in-place update

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
3. **Colors tab** — Pick colors using the color square, hex input, or eyedropper
   - Add colors with names, create and manage presets
4. **Adjustments tab** — Create zones for multi-color retexturing:
   - Add zones, paint masks to define areas, set per-zone colors and adjustments
   - Use Paint, Erase, Fill, Eyedropper, and Soften tools
   - Add wear & tear from bundled or custom overlays
5. **Output tab** — Set output folder, naming, and format; optionally enable Config Generator export
6. Click **Generate Textures**
7. Use **PAA Viewer** to browse and convert DayZ textures
8. Use **RVMAT Editor** to modify material properties

Output files are named `{prefix}_{color}.{format}` and saved to your chosen folder.

---

built with <3 by Sean
