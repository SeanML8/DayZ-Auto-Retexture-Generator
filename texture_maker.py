"""
DayZ Auto Retexture Generator
Generates color variations of DayZ item textures (PAA/PNG/TGA).
Matches the design scheme of the DayZ Retexture Config Generator.
"""

import json
import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from pathlib import Path

try:
    from PIL import Image, ImageEnhance
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

VERSION = "1.0.0"

# ─── PAA Conversion Paths ────────────────────────────────────────────────────

DAYZ_TOOLS_REL = r"steamapps\common\DayZ Tools\Bin\ImageToPAA\ImageToPAA.exe"

DAYZ_TOOLS_PATHS = [
    r"C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\ImageToPAA\ImageToPAA.exe",
    r"C:\Program Files\Steam\steamapps\common\DayZ Tools\Bin\ImageToPAA\ImageToPAA.exe",
    r"P:\DayZ Tools\Bin\ImageToPAA\ImageToPAA.exe",
]


def _get_steam_library_paths():
    """Parse Steam's libraryfolders.vdf to find all Steam library directories."""
    vdf_locations = [
        r"C:\Program Files (x86)\Steam\config\libraryfolders.vdf",
        r"C:\Program Files\Steam\config\libraryfolders.vdf",
    ]
    for vdf_path in vdf_locations:
        if os.path.isfile(vdf_path):
            try:
                with open(vdf_path, "r", encoding="utf-8") as f:
                    content = f.read()
                import re
                paths = re.findall(r'"path"\s+"([^"]+)"', content)
                return [p.replace("\\\\", "\\") for p in paths]
            except Exception:
                pass
    return []


def auto_detect_imagetopaa():
    """Auto-detect ImageToPAA.exe by scanning all Steam library folders."""
    # Check hardcoded paths first
    for path in DAYZ_TOOLS_PATHS:
        if os.path.isfile(path):
            return path
    # Scan Steam libraries
    for lib_path in _get_steam_library_paths():
        candidate = os.path.join(lib_path, DAYZ_TOOLS_REL)
        if os.path.isfile(candidate):
            return candidate
    return None

# ─── Preset Color Palettes ───────────────────────────────────────────────────

DAYZ_PRESETS = {
    "Military": [
        ("Olive Drab", (107, 142, 35)),
        ("Forest Green", (34, 85, 34)),
        ("Woodland Tan", (180, 160, 120)),
        ("Coyote Brown", (150, 120, 70)),
        ("Flat Dark Earth", (170, 145, 100)),
        ("OD Green", (80, 100, 50)),
        ("Ranger Green", (90, 110, 75)),
        ("Multicam Tan", (190, 170, 130)),
    ],
    "Urban": [
        ("Black", (25, 25, 25)),
        ("Charcoal", (55, 55, 55)),
        ("Slate Gray", (100, 100, 110)),
        ("White", (230, 230, 230)),
        ("Navy", (20, 30, 60)),
        ("Dark Blue", (30, 50, 90)),
        ("Gunmetal", (70, 75, 80)),
        ("Ash Gray", (140, 140, 140)),
    ],
    "Earth Tones": [
        ("Tan", (200, 175, 130)),
        ("Brown", (100, 70, 40)),
        ("Dark Brown", (60, 40, 25)),
        ("Khaki", (190, 180, 140)),
        ("Rust", (140, 60, 30)),
        ("Terracotta", (170, 90, 50)),
        ("Sand", (210, 190, 150)),
        ("Mahogany", (80, 35, 25)),
    ],
    "Survival": [
        ("Hunter Orange", (220, 120, 20)),
        ("Red", (180, 30, 30)),
        ("Crimson", (140, 20, 20)),
        ("Deep Purple", (60, 20, 80)),
        ("Teal", (30, 100, 100)),
        ("Moss", (80, 100, 40)),
        ("Burgundy", (100, 20, 40)),
        ("Burnt Sienna", (160, 80, 40)),
    ],
    "Bright": [
        ("Bright Red", (220, 40, 40)),
        ("Electric Blue", (30, 100, 220)),
        ("Neon Green", (50, 200, 50)),
        ("Yellow", (220, 200, 30)),
        ("Orange", (240, 140, 20)),
        ("Hot Pink", (220, 50, 120)),
        ("Cyan", (30, 200, 210)),
        ("Lime", (140, 220, 40)),
    ],
}

# ─── Color Manipulation ──────────────────────────────────────────────────────


def rgb_to_hsl(r, g, b):
    """Convert RGB (0-255) to HSL (0-360, 0-1, 0-1)."""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2.0

    if mx == mn:
        h = s = 0.0
    else:
        d = mx - mn
        s = d / (2.0 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif mx == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h /= 6.0

    return h * 360, s, l


def hsl_to_rgb(h, s, l):
    """Convert HSL (0-360, 0-1, 0-1) to RGB (0-255)."""
    h = h / 360.0

    if s == 0:
        r = g = b = l
    else:
        def hue_to_rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p

        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)

    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


def _rgb_array_to_hsl(arr):
    """Convert an RGB numpy array (H,W,3) uint8 to HSL float arrays.
    Returns (H_arr, S_arr, L_arr) each (H,W) float64, H in [0,360], S/L in [0,1]."""
    rgb = arr.astype(np.float64) / 255.0
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    l = (mx + mn) / 2.0
    d = mx - mn

    denom_hi = np.maximum(2.0 - mx - mn, 1e-10)
    denom_lo = np.maximum(mx + mn, 1e-10)
    s = np.where(d == 0, 0.0,
                 np.where(l > 0.5, d / denom_hi, d / denom_lo))

    h = np.zeros_like(l)
    mask_r = (mx == r) & (d > 0)
    mask_g = (mx == g) & (d > 0) & ~mask_r
    mask_b = (d > 0) & ~mask_r & ~mask_g

    h[mask_r] = ((g[mask_r] - b[mask_r]) / d[mask_r]) % 6
    h[mask_g] = (b[mask_g] - r[mask_g]) / d[mask_g] + 2
    h[mask_b] = (r[mask_b] - g[mask_b]) / d[mask_b] + 4
    h = (h / 6.0) * 360.0

    return h, s, l


def _hsl_to_rgb_array(h, s, l):
    """Convert HSL arrays to RGB uint8 array (H,W,3).
    h in [0,360], s/l in [0,1]."""
    h_norm = h / 360.0

    q = np.where(l < 0.5, l * (1 + s), l + s - l * s)
    p = 2 * l - q

    def hue_to_rgb(p, q, t):
        t = t % 1.0
        out = np.copy(p)
        mask1 = t < 1/6
        mask2 = (~mask1) & (t < 1/2)
        mask3 = (~mask1) & (~mask2) & (t < 2/3)
        out[mask1] = (p + (q - p) * 6 * t)[mask1]
        out[mask2] = q[mask2]
        out[mask3] = (p + (q - p) * (2/3 - t) * 6)[mask3]
        return out

    r = np.where(s == 0, l, hue_to_rgb(p, q, h_norm + 1/3))
    g = np.where(s == 0, l, hue_to_rgb(p, q, h_norm))
    b = np.where(s == 0, l, hue_to_rgb(p, q, h_norm - 1/3))

    rgb = np.stack([r, g, b], axis=-1)
    return np.clip(rgb * 255, 0, 255).astype(np.uint8)


def colorize_image(img, target_rgb, strength=0.85):
    """Colorize an image toward a target color while preserving luminance detail.
    Uses numpy for fast processing of large textures."""
    had_alpha = img.mode == "RGBA"
    if had_alpha:
        alpha = img.split()[3]
        img_rgb = img.convert("RGB")
    else:
        img_rgb = img.convert("RGB")

    if HAS_NUMPY:
        arr = np.array(img_rgb)
        target_h, target_s, _ = rgb_to_hsl(*target_rgb)

        _, _, l = _rgb_array_to_hsl(arr)

        # Create colorized version with target hue/saturation, original luminance
        h_arr = np.full_like(l, target_h)
        s_arr = np.full_like(l, target_s)
        colorized = _hsl_to_rgb_array(h_arr, s_arr, l)

        # Blend original and colorized
        result_arr = (arr.astype(np.float64) * (1 - strength) + colorized.astype(np.float64) * strength)
        result_arr = np.clip(result_arr, 0, 255).astype(np.uint8)
        result = Image.fromarray(result_arr, "RGB")
    else:
        # Fallback: pure Python (slow for large images)
        target_h, target_s, _ = rgb_to_hsl(*target_rgb)
        pixels = img_rgb.load()
        w, h = img_rgb.size
        result = Image.new("RGB", (w, h))
        rp = result.load()
        for y in range(h):
            for x in range(w):
                r, g, b = pixels[x, y]
                _, _, lum = rgb_to_hsl(r, g, b)
                cr, cg, cb = hsl_to_rgb(target_h, target_s, lum)
                rp[x, y] = (
                    max(0, min(255, int(r + (cr - r) * strength))),
                    max(0, min(255, int(g + (cg - g) * strength))),
                    max(0, min(255, int(b + (cb - b) * strength))),
                )

    if had_alpha:
        result = result.convert("RGBA")
        result.putalpha(alpha)
    return result


def hue_shift_image(img, degrees):
    """Shift the hue of an image by a given number of degrees.
    Uses numpy for fast processing of large textures."""
    had_alpha = img.mode == "RGBA"
    if had_alpha:
        alpha = img.split()[3]
        img_rgb = img.convert("RGB")
    else:
        img_rgb = img.convert("RGB")

    if HAS_NUMPY:
        arr = np.array(img_rgb)
        h, s, l = _rgb_array_to_hsl(arr)
        h = (h + degrees) % 360
        result_arr = _hsl_to_rgb_array(h, s, l)
        result = Image.fromarray(result_arr, "RGB")
    else:
        # Fallback: pure Python
        pixels = img_rgb.load()
        w, h = img_rgb.size
        result = Image.new("RGB", (w, h))
        rp = result.load()
        for y in range(h):
            for x in range(w):
                r, g, b = pixels[x, y]
                hue, sat, lum = rgb_to_hsl(r, g, b)
                nr, ng, nb = hsl_to_rgb((hue + degrees) % 360, sat, lum)
                rp[x, y] = (nr, ng, nb)

    if had_alpha:
        result = result.convert("RGBA")
        result.putalpha(alpha)
    return result


# ─── PAA Tools ────────────────────────────────────────────────────────────────


def find_imagetopaa():
    """Find the ImageToPAA.exe tool from DayZ Tools.
    Checks saved custom path first, then auto-detects from Steam libraries."""
    settings = _load_settings()
    custom = settings.get("imagetopaa_path", "")
    if custom and os.path.isfile(custom):
        return custom
    return auto_detect_imagetopaa()


def paa_to_png(paa_path, output_path):
    """Convert a PAA file to PNG using DayZ Tools."""
    tool = find_imagetopaa()
    if not tool:
        return False, "ImageToPAA.exe not found. Install DayZ Tools via Steam."
    try:
        result = subprocess.run(
            [tool, str(paa_path), str(output_path)],
            capture_output=True, text=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        return os.path.isfile(output_path), result.stderr or ""
    except Exception as e:
        return False, str(e)


def png_to_paa(png_path, output_path):
    """Convert a PNG file to PAA using DayZ Tools."""
    tool = find_imagetopaa()
    if not tool:
        return False, "ImageToPAA.exe not found. Install DayZ Tools via Steam."
    try:
        result = subprocess.run(
            [tool, str(png_path), str(output_path)],
            capture_output=True, text=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        return os.path.isfile(output_path), result.stderr or ""
    except Exception as e:
        return False, str(e)


# ─── Settings ─────────────────────────────────────────────────────────────────


def _settings_path():
    return os.path.join(os.path.expanduser("~"), ".dayz_texture_maker_settings.json")


def _load_settings():
    try:
        with open(_settings_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_settings(settings):
    try:
        with open(_settings_path(), "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except OSError:
        pass


# ─── Main Application ────────────────────────────────────────────────────────


class TextureMakerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"DayZ Auto Retexture Generator v{VERSION}")

        # Center window
        win_w, win_h = 900, 750
        try:
            import ctypes
            from ctypes import wintypes
            rect = wintypes.RECT()
            ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
            work_w = rect.right - rect.left
            work_h = rect.bottom - rect.top
            work_x = rect.left
            work_y = rect.top
        except Exception:
            work_w = self.root.winfo_screenwidth()
            work_h = self.root.winfo_screenheight()
            work_x, work_y = 0, 0
        margin = 40
        max_w = work_w - margin * 2
        max_h = work_h - margin * 2
        win_w = min(win_w, max_w)
        win_h = min(win_h, max_h)
        x = work_x + (work_w - win_w) // 2
        y = work_y + (work_h - win_h) // 2
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.root.minsize(min(900, max_w), min(750, max_h))

        # Theme
        self.dark_mode = True
        settings = _load_settings()
        if "dark_mode" in settings:
            self.dark_mode = settings["dark_mode"]

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._configure_styles()

        # State
        self.source_path = None
        self.source_image = None  # PIL Image
        self.selected_colors = []  # list of (name, (r,g,b))
        self.output_format = tk.StringVar(value="PNG")
        self.color_strength = tk.DoubleVar(value=0.85)
        self.mode_var = tk.StringVar(value="colorize")  # colorize or hue_shift
        self.hue_steps = tk.IntVar(value=8)
        self.output_dir = tk.StringVar(value="")
        self.name_prefix = tk.StringVar(value="")

        self._build_ui()

    # ─── Theme ────────────────────────────────────────────────────────────

    def _get_theme_colors(self):
        if self.dark_mode:
            return {
                "bg": "#1e1e1e", "fg": "#d4d4d4", "accent": "#569cd6",
                "entry_bg": "#2d2d2d", "btn_bg": "#3c3c3c", "btn_active": "#505050",
                "title_fg": "#ffffff", "subtitle_fg": "#808080", "section_fg": "#ffffff",
                "warning_fg": "#cca700", "accent_active": "#4a8abf",
                "list_bg": "#2d2d2d", "list_fg": "#d4d4d4", "list_select_bg": "#569cd6",
                "list_highlight": "#569cd6", "list_highlight_bg": "#3c3c3c",
                "output_bg": "#1a1a1a", "output_fg": "#d4d4d4",
                "match_good": "#6a9955", "match_bad": "#f44747",
                "placeholder_fg": "#666666",
                "error_fg": "#f44747",
            }
        else:
            return {
                "bg": "#f5f5f5", "fg": "#1e1e1e", "accent": "#0066cc",
                "entry_bg": "#ffffff", "btn_bg": "#e0e0e0", "btn_active": "#c8c8c8",
                "title_fg": "#1e1e1e", "subtitle_fg": "#666666", "section_fg": "#1e1e1e",
                "warning_fg": "#a67c00", "accent_active": "#004c99",
                "list_bg": "#ffffff", "list_fg": "#1e1e1e", "list_select_bg": "#0066cc",
                "list_highlight": "#0066cc", "list_highlight_bg": "#cccccc",
                "output_bg": "#ffffff", "output_fg": "#1e1e1e",
                "match_good": "#2d8a30", "match_bad": "#cc0000",
                "placeholder_fg": "#999999",
                "error_fg": "#cc0000",
            }

    def _configure_styles(self):
        c = self._get_theme_colors()
        self._colors = c
        self.root.configure(bg=c["bg"])

        self.style.configure("TFrame", background=c["bg"])
        self.style.configure("TLabel", background=c["bg"], foreground=c["fg"], font=("Segoe UI", 10))
        self.style.configure("Title.TLabel", background=c["bg"], foreground=c["title_fg"], font=("Segoe UI", 16, "bold"))
        self.style.configure("Subtitle.TLabel", background=c["bg"], foreground=c["subtitle_fg"], font=("Segoe UI", 9))
        self.style.configure("Status.TLabel", background=c["bg"], foreground=c["accent"], font=("Segoe UI", 9))
        self.style.configure("Section.TLabel", background=c["bg"], foreground=c["section_fg"], font=("Segoe UI", 10, "bold"))
        self.style.configure("TButton", background=c["btn_bg"], foreground=c["fg"], font=("Segoe UI", 9), borderwidth=0, padding=(8, 4))
        self.style.map("TButton", background=[("active", c["btn_active"])])
        self.style.configure("Accent.TButton", background=c["accent"], foreground="#ffffff", font=("Segoe UI", 9, "bold"), padding=(12, 5))
        self.style.map("Accent.TButton", background=[("active", c["accent_active"])])
        self.style.configure("TEntry", fieldbackground=c["entry_bg"], foreground=c["fg"], insertcolor=c["fg"], borderwidth=0, padding=6)
        self.style.configure("TLabelframe", background=c["bg"], foreground=c["fg"])
        self.style.configure("TLabelframe.Label", background=c["bg"], foreground=c["section_fg"], font=("Segoe UI", 10, "bold"))
        self.style.configure("Warning.TLabel", background=c["bg"], foreground=c["warning_fg"], font=("Segoe UI", 9))
        self.style.configure("TCheckbutton", background=c["bg"], foreground=c["fg"], font=("Segoe UI", 9))
        self.style.map("TCheckbutton", background=[("active", c["bg"])])
        self.style.configure("TRadiobutton", background=c["bg"], foreground=c["fg"], font=("Segoe UI", 9))
        self.style.map("TRadiobutton", background=[("active", c["bg"])])
        self.style.configure("TScale", background=c["bg"], troughcolor=c["entry_bg"])
        self.style.configure("TSpinbox", fieldbackground=c["entry_bg"], foreground=c["fg"], insertcolor=c["fg"], borderwidth=0, padding=4)

        # Color swatch label
        self.style.configure("Swatch.TLabel", background=c["bg"], foreground=c["fg"], font=("Segoe UI", 9), padding=(4, 2))

    # ─── UI Build ─────────────────────────────────────────────────────────

    def _build_ui(self):
        c = self._colors

        main = ttk.Frame(self.root, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        # ── Title Bar ─────────────────────────────────────────────────────
        title_frame = ttk.Frame(main)
        title_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(title_frame, text="DayZ Auto Retexture Generator", style="Title.TLabel").pack(side=tk.LEFT)

        self.theme_btn = ttk.Button(title_frame, text="Light Mode" if self.dark_mode else "Dark Mode",
                                     command=self._toggle_theme)
        self.theme_btn.pack(side=tk.RIGHT)

        ttk.Label(title_frame, text=f"v{VERSION}", style="Subtitle.TLabel").pack(side=tk.RIGHT, padx=(0, 10))

        # ── Source File ───────────────────────────────────────────────────
        src_frame = ttk.LabelFrame(main, text="Source Texture", padding=8)
        src_frame.pack(fill=tk.X, pady=(0, 8))

        src_row = ttk.Frame(src_frame)
        src_row.pack(fill=tk.X)

        self.source_label = ttk.Label(src_row, text="No file selected", style="Subtitle.TLabel")
        self.source_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(src_row, text="Browse...", command=self._browse_source).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(src_row, text="Set DayZ Tools Path", command=self._browse_dayz_tools).pack(side=tk.RIGHT, padx=(8, 0))

        self.source_info_label = ttk.Label(src_frame, text="", style="Status.TLabel")
        self.source_info_label.pack(fill=tk.X, pady=(4, 0))

        # Show DayZ Tools status
        tool = find_imagetopaa()
        if tool:
            self.source_info_label.configure(text=f"DayZ Tools found: {tool}")
        else:
            self.source_info_label.configure(text="DayZ Tools not found — click 'Set DayZ Tools Path' to locate ImageToPAA.exe")

        if not HAS_PIL:
            ttk.Label(src_frame, text="Pillow not installed! Run: pip install Pillow",
                      style="Warning.TLabel").pack(fill=tk.X, pady=(4, 0))

        # ── Mode Selection ────────────────────────────────────────────────
        mode_frame = ttk.LabelFrame(main, text="Generation Mode", padding=8)
        mode_frame.pack(fill=tk.X, pady=(0, 8))

        mode_row = ttk.Frame(mode_frame)
        mode_row.pack(fill=tk.X)

        ttk.Radiobutton(mode_row, text="Colorize (pick target colors)",
                        variable=self.mode_var, value="colorize",
                        command=self._on_mode_change).pack(side=tk.LEFT, padx=(0, 16))
        ttk.Radiobutton(mode_row, text="Hue Shift (rotate hue evenly)",
                        variable=self.mode_var, value="hue_shift",
                        command=self._on_mode_change).pack(side=tk.LEFT)

        # ── Colorize Options ──────────────────────────────────────────────
        self.colorize_frame = ttk.LabelFrame(main, text="Color Selection", padding=8)
        self.colorize_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Preset buttons
        preset_row = ttk.Frame(self.colorize_frame)
        preset_row.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(preset_row, text="Presets:", style="Section.TLabel").pack(side=tk.LEFT, padx=(0, 8))
        for name in DAYZ_PRESETS:
            ttk.Button(preset_row, text=name,
                       command=lambda n=name: self._load_preset(n)).pack(side=tk.LEFT, padx=2)

        # Custom color button + clear
        action_row = ttk.Frame(self.colorize_frame)
        action_row.pack(fill=tk.X, pady=(0, 6))

        ttk.Button(action_row, text="+ Add Custom Color", command=self._add_custom_color).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(action_row, text="Clear All", command=self._clear_colors).pack(side=tk.LEFT)

        # Strength slider
        strength_row = ttk.Frame(self.colorize_frame)
        strength_row.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(strength_row, text="Color Strength:").pack(side=tk.LEFT, padx=(0, 8))
        self.strength_scale = ttk.Scale(strength_row, from_=0.1, to=1.0,
                                         variable=self.color_strength, orient=tk.HORIZONTAL)
        self.strength_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.strength_label = ttk.Label(strength_row, text="85%", width=5)
        self.strength_label.pack(side=tk.LEFT)
        self.color_strength.trace_add("write", self._update_strength_label)

        # Color swatches area (scrollable)
        swatch_outer = ttk.Frame(self.colorize_frame)
        swatch_outer.pack(fill=tk.BOTH, expand=True)

        self.swatch_canvas = tk.Canvas(swatch_outer, bg=c["bg"], highlightthickness=0, height=150)
        swatch_scrollbar = ttk.Scrollbar(swatch_outer, orient=tk.VERTICAL, command=self.swatch_canvas.yview)
        self.swatch_inner = ttk.Frame(self.swatch_canvas)

        self.swatch_inner.bind("<Configure>",
                                lambda e: self.swatch_canvas.configure(scrollregion=self.swatch_canvas.bbox("all")))
        self.swatch_canvas.create_window((0, 0), window=self.swatch_inner, anchor="nw")
        self.swatch_canvas.configure(yscrollcommand=swatch_scrollbar.set)

        self.swatch_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        swatch_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ── Hue Shift Options ─────────────────────────────────────────────
        self.hue_frame = ttk.LabelFrame(main, text="Hue Shift Options", padding=8)
        # Don't pack yet — toggled by mode

        hue_row = ttk.Frame(self.hue_frame)
        hue_row.pack(fill=tk.X)

        ttk.Label(hue_row, text="Number of variants:").pack(side=tk.LEFT, padx=(0, 8))
        self.hue_spinbox = ttk.Spinbox(hue_row, from_=2, to=36, textvariable=self.hue_steps, width=6)
        self.hue_spinbox.pack(side=tk.LEFT, padx=(0, 16))
        ttk.Label(hue_row, text="(evenly spaced around the color wheel)", style="Subtitle.TLabel").pack(side=tk.LEFT)

        # ── Output Options ────────────────────────────────────────────────
        out_frame = ttk.LabelFrame(main, text="Output", padding=8)
        out_frame.pack(fill=tk.X, pady=(0, 8))

        # Output directory
        out_dir_row = ttk.Frame(out_frame)
        out_dir_row.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(out_dir_row, text="Output Folder:").pack(side=tk.LEFT, padx=(0, 8))
        self.out_dir_entry = ttk.Entry(out_dir_row, textvariable=self.output_dir)
        self.out_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(out_dir_row, text="Browse...", command=self._browse_output).pack(side=tk.RIGHT)

        # Name prefix + format
        opt_row = ttk.Frame(out_frame)
        opt_row.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(opt_row, text="Name Prefix:").pack(side=tk.LEFT, padx=(0, 8))
        self.prefix_entry = ttk.Entry(opt_row, textvariable=self.name_prefix, width=20)
        self.prefix_entry.pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(opt_row, text="Format:").pack(side=tk.LEFT, padx=(0, 8))
        fmt_combo = ttk.Combobox(opt_row, textvariable=self.output_format,
                                  values=["PNG", "TGA", "PAA"], state="readonly", width=6)
        fmt_combo.pack(side=tk.LEFT)

        # ── Generate Button ───────────────────────────────────────────────
        gen_row = ttk.Frame(main)
        gen_row.pack(fill=tk.X, pady=(0, 8))

        self.generate_btn = ttk.Button(gen_row, text="Generate Textures", style="Accent.TButton",
                                        command=self._generate)
        self.generate_btn.pack(side=tk.LEFT)

        self.progress_label = ttk.Label(gen_row, text="", style="Status.TLabel")
        self.progress_label.pack(side=tk.LEFT, padx=(12, 0))

        # ── Progress Bar ──────────────────────────────────────────────────
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(main, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 8))

        # ── Footer ────────────────────────────────────────────────────────
        footer = ttk.Frame(main)
        footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(4, 0))

        ttk.Label(footer, text="built with <3 by Sean", style="Subtitle.TLabel").pack(side=tk.RIGHT, padx=16)

        # Initialize mode visibility
        self._on_mode_change()

    # ─── Mode Toggle ──────────────────────────────────────────────────────

    def _on_mode_change(self):
        mode = self.mode_var.get()
        if mode == "colorize":
            self.hue_frame.pack_forget()
            self.colorize_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8),
                                      after=self._find_widget_after_mode())
        else:
            self.colorize_frame.pack_forget()
            self.hue_frame.pack(fill=tk.X, pady=(0, 8),
                                 after=self._find_widget_after_mode())

    def _find_widget_after_mode(self):
        """Find the mode frame to pack after it."""
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.LabelFrame) and "Mode" in str(child.cget("text")):
                        return child
        return None

    # ─── DayZ Tools Path ─────────────────────────────────────────────────

    def _browse_dayz_tools(self):
        path = filedialog.askopenfilename(
            title="Locate ImageToPAA.exe",
            filetypes=[("ImageToPAA.exe", "ImageToPAA.exe"), ("All files", "*.*")],
        )
        if not path:
            return
        if not path.lower().endswith("imagetopaa.exe"):
            messagebox.showerror("Error", "Please select ImageToPAA.exe")
            return
        settings = _load_settings()
        settings["imagetopaa_path"] = path
        _save_settings(settings)
        self.source_info_label.configure(text=f"DayZ Tools found: {path}")
        # Reload source if it was a PAA that failed
        if self.source_path and Path(self.source_path).suffix.lower() == ".paa" and self.source_image is None:
            self._load_source_image(self.source_path)

    # ─── Source File ──────────────────────────────────────────────────────

    def _browse_source(self):
        filetypes = [
            ("Image files", "*.png *.tga *.paa *.jpg *.jpeg *.bmp"),
            ("PAA files", "*.paa"),
            ("PNG files", "*.png"),
            ("TGA files", "*.tga"),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(title="Select Source Texture", filetypes=filetypes)
        if not path:
            return

        self.source_path = path
        self.source_label.configure(text=os.path.basename(path))

        # Auto-set output dir and prefix
        src_dir = os.path.dirname(path)
        src_name = Path(path).stem
        if not self.output_dir.get():
            self.output_dir.set(os.path.join(src_dir, f"{src_name}_variants"))
        if not self.name_prefix.get():
            self.name_prefix.set(src_name)

        # Try to load the image
        self._load_source_image(path)

    def _load_source_image(self, path):
        if not HAS_PIL:
            self.source_info_label.configure(text="Cannot preview — Pillow not installed")
            return

        ext = Path(path).suffix.lower()

        if ext == ".paa":
            # Convert PAA to temp PNG first
            import tempfile
            temp_png = os.path.join(tempfile.gettempdir(), "dayz_tex_preview.png")
            success, err = paa_to_png(path, temp_png)
            if not success:
                self.source_info_label.configure(text=f"PAA conversion failed: {err}")
                self.source_image = None
                return
            path = temp_png

        try:
            img = Image.open(path)
            self.source_image = img.copy()
            w, h = img.size
            mode = img.mode
            self.source_info_label.configure(text=f"{w} x {h} px  |  {mode}  |  Ready")
        except Exception as e:
            self.source_info_label.configure(text=f"Failed to load: {e}")
            self.source_image = None

    # ─── Color Management ─────────────────────────────────────────────────

    def _load_preset(self, preset_name):
        self.selected_colors = list(DAYZ_PRESETS[preset_name])
        self._refresh_swatches()

    def _add_custom_color(self):
        result = colorchooser.askcolor(title="Pick a Color")
        if result and result[0]:
            rgb = tuple(int(v) for v in result[0])
            hex_str = result[1]
            name = hex_str.upper()
            self.selected_colors.append((name, rgb))
            self._refresh_swatches()

    def _clear_colors(self):
        self.selected_colors.clear()
        self._refresh_swatches()

    def _remove_color(self, index):
        if 0 <= index < len(self.selected_colors):
            self.selected_colors.pop(index)
            self._refresh_swatches()

    def _refresh_swatches(self):
        for widget in self.swatch_inner.winfo_children():
            widget.destroy()

        c = self._colors

        if not self.selected_colors:
            ttk.Label(self.swatch_inner, text="No colors selected. Use presets or add custom colors.",
                      style="Subtitle.TLabel").pack(pady=8)
            return

        # Grid of color swatches
        cols = 4
        for i, (name, rgb) in enumerate(self.selected_colors):
            row, col = divmod(i, cols)

            frame = ttk.Frame(self.swatch_inner, padding=4)
            frame.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

            hex_color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

            # Color square
            swatch = tk.Canvas(frame, width=40, height=40, highlightthickness=1,
                               highlightbackground=c["fg"], bg=hex_color)
            swatch.pack()

            # Name label
            ttk.Label(frame, text=name, font=("Segoe UI", 8), wraplength=80).pack()

            # Remove button
            rm_btn = ttk.Button(frame, text="x", width=2,
                                command=lambda idx=i: self._remove_color(idx))
            rm_btn.pack(pady=(2, 0))

    def _update_strength_label(self, *args):
        try:
            val = self.color_strength.get()
            self.strength_label.configure(text=f"{int(val * 100)}%")
        except Exception:
            pass

    # ─── Output ───────────────────────────────────────────────────────────

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.output_dir.set(path)

    # ─── Generation ───────────────────────────────────────────────────────

    def _generate(self):
        if not HAS_PIL:
            messagebox.showerror("Error", "Pillow is required.\nInstall it with: pip install Pillow")
            return

        if self.source_image is None:
            messagebox.showerror("Error", "Please select a source texture first.")
            return

        out_dir = self.output_dir.get().strip()
        if not out_dir:
            messagebox.showerror("Error", "Please select an output folder.")
            return

        mode = self.mode_var.get()
        if mode == "colorize" and not self.selected_colors:
            messagebox.showerror("Error", "Please select at least one color.")
            return

        # Disable button during generation
        self.generate_btn.configure(state=tk.DISABLED)
        self.progress_var.set(0)
        self.progress_label.configure(text="Starting...")

        thread = threading.Thread(target=self._generate_worker, daemon=True)
        thread.start()

    def _generate_worker(self):
        try:
            out_dir = self.output_dir.get().strip()
            os.makedirs(out_dir, exist_ok=True)

            prefix = self.name_prefix.get().strip() or "texture"
            fmt = self.output_format.get()
            mode = self.mode_var.get()
            img = self.source_image.copy()

            if mode == "colorize":
                variants = self.selected_colors
                total = len(variants)
            else:
                steps = self.hue_steps.get()
                step_deg = 360 / steps
                variants = [(f"hue_{int(i * step_deg)}deg", i * step_deg) for i in range(steps)]
                total = len(variants)

            for i, variant in enumerate(variants):
                if mode == "colorize":
                    name, rgb = variant
                    strength = self.color_strength.get()
                    result_img = colorize_image(img, rgb, strength)
                else:
                    name, degrees = variant
                    result_img = hue_shift_image(img, degrees)

                # Clean up filename
                safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name).strip()
                safe_name = safe_name.replace(" ", "_")

                if fmt == "PAA":
                    # Save as PNG first, then convert
                    png_path = os.path.join(out_dir, f"{prefix}_{safe_name}.png")
                    paa_path = os.path.join(out_dir, f"{prefix}_{safe_name}.paa")
                    result_img.save(png_path)
                    success, err = png_to_paa(png_path, paa_path)
                    if success:
                        os.remove(png_path)  # Clean up intermediate PNG
                    else:
                        self._update_progress(i + 1, total, f"PAA conversion failed for {safe_name}: {err}")
                        continue
                elif fmt == "TGA":
                    out_path = os.path.join(out_dir, f"{prefix}_{safe_name}.tga")
                    result_img.save(out_path)
                else:
                    out_path = os.path.join(out_dir, f"{prefix}_{safe_name}.png")
                    result_img.save(out_path)

                self._update_progress(i + 1, total, f"Generated: {safe_name}")

            self._update_progress(total, total, f"Done! {total} variants saved to {out_dir}")
            self.root.after(0, lambda: self.generate_btn.configure(state=tk.NORMAL))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, lambda: self.generate_btn.configure(state=tk.NORMAL))

    def _update_progress(self, current, total, message):
        pct = (current / total) * 100 if total > 0 else 0
        self.root.after(0, lambda: self.progress_var.set(pct))
        self.root.after(0, lambda: self.progress_label.configure(text=message))

    # ─── Theme Toggle ─────────────────────────────────────────────────────

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self._configure_styles()
        self.theme_btn.configure(text="Light Mode" if self.dark_mode else "Dark Mode")
        self._apply_theme_to_widgets()
        self._refresh_swatches()

        settings = _load_settings()
        settings["dark_mode"] = self.dark_mode
        _save_settings(settings)

    def _apply_theme_to_widgets(self):
        c = self._colors
        self.swatch_canvas.configure(bg=c["bg"])


# ─── First Launch Setup ──────────────────────────────────────────────────────


def _first_launch_setup(root):
    """Show a setup dialog on first launch to locate DayZ Tools.
    Returns True if a path was set, False if user cancelled."""
    settings = _load_settings()
    if settings.get("imagetopaa_path"):
        return True  # Already configured

    # Try auto-detect first
    detected = auto_detect_imagetopaa()

    # Show setup dialog (always on first launch)
    setup = tk.Toplevel(root)
    setup.title("DayZ Tools Setup")
    setup.resizable(False, False)
    setup.grab_set()

    win_w, win_h = 500, 220
    sx = root.winfo_screenwidth() // 2 - win_w // 2
    sy = root.winfo_screenheight() // 2 - win_h // 2
    setup.geometry(f"{win_w}x{win_h}+{sx}+{sy}")
    setup.configure(bg="#1e1e1e")

    result = {"path": detected}

    tk.Label(setup, text="Welcome to DayZ Auto Retexture Generator",
             font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#1e1e1e").pack(pady=(16, 4))

    if detected:
        tk.Label(setup, text="DayZ Tools was automatically detected at:",
                 font=("Segoe UI", 10), fg="#d4d4d4", bg="#1e1e1e").pack(pady=(0, 4))
        tk.Label(setup, text=detected,
                 font=("Segoe UI", 9), fg="#569cd6", bg="#1e1e1e", wraplength=460).pack(pady=(0, 12))
    else:
        tk.Label(setup, text="DayZ Tools could not be auto-detected.\nPlease locate ImageToPAA.exe from your DayZ Tools installation.",
                 font=("Segoe UI", 10), fg="#d4d4d4", bg="#1e1e1e").pack(pady=(0, 12))

    def confirm():
        if result["path"]:
            settings["imagetopaa_path"] = result["path"]
            _save_settings(settings)
        setup.destroy()

    def browse():
        path = filedialog.askopenfilename(
            title="Locate ImageToPAA.exe",
            filetypes=[("ImageToPAA.exe", "ImageToPAA.exe"), ("All files", "*.*")],
        )
        if path and path.lower().endswith("imagetopaa.exe"):
            result["path"] = path
            settings["imagetopaa_path"] = path
            _save_settings(settings)
            setup.destroy()
        elif path:
            messagebox.showerror("Error", "Please select ImageToPAA.exe", parent=setup)

    btn_frame = tk.Frame(setup, bg="#1e1e1e")
    btn_frame.pack(pady=(0, 16))

    if detected:
        tk.Button(btn_frame, text="Continue", command=confirm,
                  font=("Segoe UI", 10, "bold"), bg="#569cd6", fg="#ffffff",
                  padx=16, pady=6, relief="flat").pack(side=tk.LEFT, padx=8)
        tk.Button(btn_frame, text="Change Path...", command=browse,
                  font=("Segoe UI", 9), bg="#3c3c3c", fg="#d4d4d4",
                  padx=12, pady=6, relief="flat").pack(side=tk.LEFT, padx=8)
    else:
        tk.Button(btn_frame, text="Browse for ImageToPAA.exe", command=browse,
                  font=("Segoe UI", 10, "bold"), bg="#569cd6", fg="#ffffff",
                  padx=16, pady=6, relief="flat").pack(side=tk.LEFT, padx=8)
        tk.Button(btn_frame, text="Skip for now", command=confirm,
                  font=("Segoe UI", 9), bg="#3c3c3c", fg="#d4d4d4",
                  padx=12, pady=6, relief="flat").pack(side=tk.LEFT, padx=8)

    tk.Label(setup, text="built with <3 by Sean",
             font=("Segoe UI", 8), fg="#808080", bg="#1e1e1e").pack(side=tk.BOTTOM, pady=(0, 8))

    setup.protocol("WM_DELETE_WINDOW", confirm)
    root.wait_window(setup)
    return result["path"] is not None


# ─── Entry Point ──────────────────────────────────────────────────────────────


def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default="")
    except Exception:
        pass
    root.withdraw()  # Hide main window during setup
    _first_launch_setup(root)
    root.deiconify()
    app = TextureMakerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
