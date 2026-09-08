"""Built-in Python graphical user interface (Tkinter) for Python Color Math."""

from __future__ import annotations

import ctypes
import os
import sys
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from .adapters import AdapterError, detect_format, transform_document
from .config import (
    COLORS,
    DEFAULT_COLORS,
    ROLE_DESCRIPTIONS,
    THEMES,
    ColorMathOptions,
    get_theme,
    reset_colors,
)
from .io import encode_utf8, read_utf8, replace_bytes
from .main import collect_target_files, generate_diff


def enable_high_dpi() -> None:
    """Enable Per-Monitor DPI awareness on Windows before creating the Tk root."""
    if sys.platform == "win32":
        try:
            # 2 = PROCESS_PER_MONITOR_DPI_AWARE
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def configure_dpi_scaling(root: tk.Tk) -> float:
    """Query display DPI and configure Tk scaling factor."""
    try:
        dpi = root.winfo_fpixels("1i")
        scale = dpi / 72.0
        root.tk.call("tk", "scaling", scale)
        return scale
    except Exception:
        return 1.0


class ColorMathApp:
    def __init__(
        self,
        root: tk.Tk,
        initial_path: str | None = None,
        initial_write: bool = False,
        palette: dict[str, str] | None = None,
        options: ColorMathOptions | None = None,
    ) -> None:
        self.root = root
        self.root.title("Python Color Math")
        self.root.minsize(620, 680)
        self.root.geometry("680x720")

        self.scale = configure_dpi_scaling(root)

        # State
        self.target_path_var = tk.StringVar(value=initial_path or "")
        self.is_recursive_var = tk.BooleanVar(value=False)
        self.mode_var = tk.StringVar(value="write" if initial_write else "preview")

        self.palette: dict[str, str] = dict(palette if palette else DEFAULT_COLORS)
        self.options: ColorMathOptions = options or ColorMathOptions.all_enabled()

        self.theme_var = tk.StringVar(value="default")
        self.preset_var = tk.StringVar(value="all")

        # Options BooleanVars
        self.opt_units = tk.BooleanVar(value=self.options.color_units)
        self.opt_differentials = tk.BooleanVar(value=self.options.color_differentials)
        self.opt_rainbow = tk.BooleanVar(value=self.options.rainbow_delimiters)
        self.opt_braket = tk.BooleanVar(value=self.options.color_braket)
        self.opt_dimensionless = tk.BooleanVar(value=self.options.color_dimensionless)
        self.opt_taxonomy = tk.BooleanVar(value=self.options.enable_taxonomy)
        self.opt_data_flow = tk.BooleanVar(value=self.options.variable_data_flow)

        self.color_buttons: dict[str, tk.Button] = {}

        self._apply_theme_styling()
        self._build_ui()

    def _apply_theme_styling(self) -> None:
        self.style = ttk.Style()
        try:
            if sys.platform == "win32" and "vista" in self.style.theme_names():
                self.style.theme_use("vista")
            elif "clam" in self.style.theme_names():
                self.style.theme_use("clam")
        except Exception:
            pass

        base_font = ("Segoe UI", 9) if sys.platform == "win32" else ("Helvetica", 10)
        bold_font = ("Segoe UI", 9, "bold") if sys.platform == "win32" else ("Helvetica", 10, "bold")
        title_font = ("Segoe UI", 11, "bold") if sys.platform == "win32" else ("Helvetica", 12, "bold")

        self.style.configure(".", font=base_font)
        self.style.configure("TLabelframe.Label", font=bold_font, foreground="#2b5b84")
        self.style.configure("Title.TLabel", font=title_font)
        self.style.configure("Primary.TButton", font=bold_font)

        # On Linux / macOS or non-vista platforms, ensure checkboxes display a clean checkmark (✓) instead of 'X'
        if self.style.theme_use() != "vista":
            try:
                self._cb_unchecked = tk.PhotoImage(width=16, height=16)
                self._cb_checked = tk.PhotoImage(width=16, height=16)

                self._cb_unchecked.put("#ffffff", to=(1, 1, 15, 15))
                for x in range(1, 15):
                    self._cb_unchecked.put("#888888", (x, 1))
                    self._cb_unchecked.put("#888888", (x, 14))
                for y in range(1, 15):
                    self._cb_unchecked.put("#888888", (1, y))
                    self._cb_unchecked.put("#888888", (14, y))

                self._cb_checked.put("#2563eb", to=(1, 1, 15, 15))
                check_coords = [
                    (4, 7), (4, 8), (5, 8), (5, 9), (6, 9), (6, 10),
                    (7, 9), (7, 8), (8, 8), (8, 7), (9, 7), (9, 6),
                    (10, 6), (10, 5), (11, 5), (11, 4),
                ]
                for x, y in check_coords:
                    self._cb_checked.put("#ffffff", (x, y))

                self.style.element_create(
                    "Checkmark.indicator",
                    "image",
                    self._cb_unchecked,
                    ("selected", self._cb_checked),
                )
                self.style.layout(
                    "TCheckbutton",
                    [
                        (
                            "Checkbutton.padding",
                            {
                                "children": [
                                    ("Checkmark.indicator", {"side": "left"}),
                                    ("Checkbutton.label", {"side": "left", "expand": 1}),
                                ]
                            },
                        )
                    ],
                )
            except Exception:
                pass

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self.root, padding=14)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(title_frame, text="🎨 Python Color Math", style="Title.TLabel").pack(side=tk.LEFT)
        dpi_val = self.root.winfo_fpixels("1i")
        ttk.Label(title_frame, text=f"DPI: {int(dpi_val)} ({int(self.scale * 100 / 1.33)}% Scale)", foreground="#666666").pack(side=tk.RIGHT)

        # Section 1: Target Selection
        file_frame = ttk.LabelFrame(main_frame, text=" 📁 Target Note or Directory ", padding=10)
        file_frame.pack(fill=tk.X, pady=5)

        entry_row = ttk.Frame(file_frame)
        entry_row.pack(fill=tk.X, expand=True)
        ttk.Entry(entry_row, textvariable=self.target_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(entry_row, text="Browse File...", command=self._browse_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(entry_row, text="Browse Folder...", command=self._browse_dir).pack(side=tk.LEFT, padx=2)

        ttk.Checkbutton(file_frame, text="Process subfolders recursively (-r)", variable=self.is_recursive_var).pack(anchor=tk.W, pady=(6, 0))

        # Section 2: Mode Selection
        mode_frame = ttk.LabelFrame(main_frame, text=" ⚙️ Action Mode ", padding=10)
        mode_frame.pack(fill=tk.X, pady=5)

        mode_row = ttk.Frame(mode_frame)
        mode_row.pack(fill=tk.X)
        ttk.Radiobutton(
            mode_row,
            text="Preview Mode (Inspect changes safely without modifying disk)",
            variable=self.mode_var,
            value="preview",
        ).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(
            mode_row,
            text="Write In-Place Mode (Save color wrappers directly to file on disk)",
            variable=self.mode_var,
            value="write",
        ).pack(anchor=tk.W, pady=2)

        # Section 3: Colors & Palette
        palette_frame = ttk.LabelFrame(main_frame, text=" 🎨 Active Colors & Palette ", padding=10)
        palette_frame.pack(fill=tk.X, pady=5)

        ctrl_row = ttk.Frame(palette_frame)
        ctrl_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(ctrl_row, text="Theme:").pack(side=tk.LEFT, padx=(0, 6))
        theme_combo = ttk.Combobox(ctrl_row, textvariable=self.theme_var, values=list(THEMES.keys()), state="readonly", width=12)
        theme_combo.pack(side=tk.LEFT, padx=(0, 10))
        theme_combo.bind("<<ComboboxSelected>>", self._on_theme_changed)

        ttk.Button(ctrl_row, text="Reset Colors", command=self._on_reset_colors).pack(side=tk.RIGHT)

        # Color Swatches Grid
        swatches_frame = ttk.Frame(palette_frame)
        swatches_frame.pack(fill=tk.X)

        roles = list(DEFAULT_COLORS.keys())
        cols = 3
        for idx, role in enumerate(roles):
            row_idx = idx // cols
            col_idx = (idx % cols) * 2

            lbl_text = f"{role}:"
            ttk.Label(swatches_frame, text=lbl_text, width=11, anchor=tk.W).grid(row=row_idx, column=col_idx, sticky=tk.W, padx=(4, 2), pady=2)

            btn = tk.Button(
                swatches_frame,
                text=self.palette.get(role, "#7aa2f7"),
                bg=self._normalize_bg(self.palette.get(role, "#7aa2f7")),
                fg=self._get_contrast_fg(self.palette.get(role, "#7aa2f7")),
                relief=tk.RIDGE,
                width=9,
                font=("Consolas", 8),
                command=lambda r=role: self._pick_color(r),
            )
            btn.grid(row=row_idx, column=col_idx + 1, sticky=tk.W, padx=(0, 12), pady=2)
            self.color_buttons[role] = btn

        # Section 4: Basic Settings
        settings_frame = ttk.LabelFrame(main_frame, text=" 🛠️ Basic Settings & Engine Features ", padding=10)
        settings_frame.pack(fill=tk.X, pady=5)

        preset_row = ttk.Frame(settings_frame)
        preset_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(preset_row, text="Feature Preset:").pack(side=tk.LEFT, padx=(0, 6))
        preset_combo = ttk.Combobox(
            preset_row,
            textvariable=self.preset_var,
            values=["all", "minimal"],
            state="readonly",
            width=12,
        )
        preset_combo.pack(side=tk.LEFT)
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_changed)

        toggles_grid = ttk.Frame(settings_frame)
        toggles_grid.pack(fill=tk.X)

        ttk.Checkbutton(toggles_grid, text="Units (m/s, \\mu m)", variable=self.opt_units).grid(row=0, column=0, sticky=tk.W, padx=6, pady=2)
        ttk.Checkbutton(toggles_grid, text="Differentials (dx, dt)", variable=self.opt_differentials).grid(row=0, column=1, sticky=tk.W, padx=6, pady=2)
        ttk.Checkbutton(toggles_grid, text="Rainbow Delimiters", variable=self.opt_rainbow).grid(row=0, column=2, sticky=tk.W, padx=6, pady=2)

        ttk.Checkbutton(toggles_grid, text="Bra-Ket Notation", variable=self.opt_braket).grid(row=1, column=0, sticky=tk.W, padx=6, pady=2)
        ttk.Checkbutton(toggles_grid, text="Dimensionless (Re)", variable=self.opt_dimensionless).grid(row=1, column=1, sticky=tk.W, padx=6, pady=2)
        ttk.Checkbutton(toggles_grid, text="Semantic Taxonomy", variable=self.opt_taxonomy).grid(row=1, column=2, sticky=tk.W, padx=6, pady=2)
        ttk.Checkbutton(toggles_grid, text="Variable Data-Flow (Hash)", variable=self.opt_data_flow).grid(row=2, column=0, sticky=tk.W, padx=6, pady=2)

        # Section 5: Action Buttons
        footer = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Button(footer, text="Close", command=self.root.destroy).pack(side=tk.RIGHT, padx=4)
        run_btn = ttk.Button(footer, text="▶ Run / Process", style="Primary.TButton", command=self._execute_action)
        run_btn.pack(side=tk.RIGHT, padx=4)

    def _normalize_bg(self, color_code: str) -> str:
        code = color_code.strip()
        if code.lower() == "white":
            return "#ffffff"
        if code.lower() == "black":
            return "#000000"
        if code.startswith("#") and len(code) == 7:
            return code
        return "#dddddd"

    def _get_contrast_fg(self, hex_color: str) -> str:
        color = hex_color.strip()
        if color.lower() == "white":
            return "#000000"
        if color.startswith("#") and len(color) == 7:
            try:
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
                return "#000000" if luminance > 0.65 else "#ffffff"
            except Exception:
                pass
        return "#000000"

    def _browse_file(self) -> None:
        file_selected = filedialog.askopenfilename(
            title="Select LaTeX / Markdown Document",
            filetypes=[
                ("Markdown & LaTeX", "*.md;*.markdown;*.qmd;*.ipynb;*.tex;*.latex"),
                ("All Files", "*.*"),
            ],
        )
        if file_selected:
            self.target_path_var.set(file_selected)

    def _browse_dir(self) -> None:
        dir_selected = filedialog.askdirectory(title="Select Notes Directory")
        if dir_selected:
            self.target_path_var.set(dir_selected)

    def _pick_color(self, role: str) -> None:
        current = self.palette.get(role, "#7aa2f7")
        chosen = colorchooser.askcolor(color=current, title=f"Select color for '{role}'")
        if chosen and chosen[1]:
            new_hex = chosen[1].lower()
            self.palette[role] = new_hex
            btn = self.color_buttons[role]
            btn.config(
                text=new_hex,
                bg=new_hex,
                fg=self._get_contrast_fg(new_hex),
            )

    def _on_theme_changed(self, event: object = None) -> None:
        name = self.theme_var.get()
        try:
            theme_colors = get_theme(name)
            self.palette.update(theme_colors)
            for role, btn in self.color_buttons.items():
                col = self.palette.get(role, "#7aa2f7")
                btn.config(
                    text=col,
                    bg=self._normalize_bg(col),
                    fg=self._get_contrast_fg(col),
                )
        except Exception as e:
            messagebox.showerror("Error", f"Could not load theme '{name}': {e}")

    def _on_reset_colors(self) -> None:
        self.palette.clear()
        self.palette.update(DEFAULT_COLORS)
        self.theme_var.set("default")
        for role, btn in self.color_buttons.items():
            col = self.palette.get(role, DEFAULT_COLORS[role])
            btn.config(
                text=col,
                bg=self._normalize_bg(col),
                fg=self._get_contrast_fg(col),
            )

    def _on_preset_changed(self, event: object = None) -> None:
        preset = self.preset_var.get()
        if preset == "minimal":
            opts = ColorMathOptions()
        else:
            opts = ColorMathOptions.all_enabled()

        self.opt_units.set(opts.color_units)
        self.opt_differentials.set(opts.color_differentials)
        self.opt_rainbow.set(opts.rainbow_delimiters)
        self.opt_braket.set(opts.color_braket)
        self.opt_dimensionless.set(opts.color_dimensionless)
        self.opt_taxonomy.set(opts.enable_taxonomy)
        self.opt_data_flow.set(opts.variable_data_flow)

    def _collect_current_options(self) -> ColorMathOptions:
        return ColorMathOptions(
            color_units=self.opt_units.get(),
            color_differentials=self.opt_differentials.get(),
            rainbow_delimiters=self.opt_rainbow.get(),
            color_braket=self.opt_braket.get(),
            color_dimensionless=self.opt_dimensionless.get(),
            enable_taxonomy=self.opt_taxonomy.get(),
            variable_data_flow=self.opt_data_flow.get(),
        )

    def _execute_action(self) -> None:
        target_str = self.target_path_var.get().strip()
        if not target_str:
            messagebox.showwarning("Warning", "Please select a target file or folder first.")
            return

        target_path = Path(target_str)
        if not target_path.exists():
            messagebox.showerror("Error", f"Target does not exist:\n{target_str}")
            return

        options = self._collect_current_options()
        mode = self.mode_var.get()
        is_recursive = self.is_recursive_var.get()

        try:
            files = collect_target_files(
                [target_str],
                recursive=is_recursive,
                excludes=[],
                force_file=True,
            )
        except Exception as err:
            messagebox.showerror("Error", f"Error scanning files:\n{err}")
            return

        if not files:
            messagebox.showinfo("No Files Found", "No supported document files (.md, .ipynb, .tex) found.")
            return

        if mode == "preview":
            self._show_preview_window(files, options)
        else:
            self._perform_write(files, options)

    def _show_preview_window(self, files: list[Path], options: ColorMathOptions) -> None:
        preview_win = tk.Toplevel(self.root)
        preview_win.title("Conversion Preview (Diff)")
        preview_win.geometry("750x550")

        txt_frame = ttk.Frame(preview_win, padding=8)
        txt_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(txt_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(
            txt_frame,
            wrap=tk.NONE,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 10),
            bg="#fdfdfd",
            fg="#222222",
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        # Diff color tags
        text_widget.tag_configure("diff_add", foreground="#1a7f37", background="#e6ffed")
        text_widget.tag_configure("diff_del", foreground="#cf222e", background="#ffebe9")
        text_widget.tag_configure("diff_header", foreground="#0969da", font=("Consolas", 10, "bold"))

        total_diffs = 0
        for p in files:
            try:
                content, _ = read_utf8(p)
                fmt = detect_format(p, "auto")
                converted = transform_document(content, fmt, undo=False, palette=self.palette, options=options)
                diff = generate_diff(content, converted, str(p))
                if diff:
                    total_diffs += 1
                    for line in diff.splitlines(keepends=True):
                        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
                            text_widget.insert(tk.END, line, "diff_header")
                        elif line.startswith("+"):
                            text_widget.insert(tk.END, line, "diff_add")
                        elif line.startswith("-"):
                            text_widget.insert(tk.END, line, "diff_del")
                        else:
                            text_widget.insert(tk.END, line)
            except Exception as e:
                text_widget.insert(tk.END, f"\nError processing {p}: {e}\n", "diff_del")

        if total_diffs == 0:
            text_widget.insert(tk.END, "All examined files are already cleanly formatted with color wrappers!\nNo changes required.")

        text_widget.config(state=tk.DISABLED)

    def _perform_write(self, files: list[Path], options: ColorMathOptions) -> None:
        count_modified = 0
        count_total = len(files)

        for p in files:
            try:
                content, source = read_utf8(p)
                fmt = detect_format(p, "auto")
                converted = transform_document(content, fmt, undo=False, palette=self.palette, options=options)
                if converted != content:
                    output = encode_utf8(converted, source)
                    replace_bytes(p, output, source)
                    count_modified += 1
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save {p}:\n{e}")
                return

        msg = f"Processed {count_total} file(s).\n\nSuccessfully modified: {count_modified}\nUnchanged: {count_total - count_modified}"
        messagebox.showinfo("Conversion Complete", msg)


def launch_gui(
    initial_path: str | None = None,
    initial_write: bool = False,
    palette: dict[str, str] | None = None,
    options: ColorMathOptions | None = None,
) -> int:
    """Initialize DPI awareness and launch the Python Color Math Tkinter UI."""
    enable_high_dpi()
    root = tk.Tk()
    app = ColorMathApp(
        root,
        initial_path=initial_path,
        initial_write=initial_write,
        palette=palette,
        options=options,
    )

    # Bring window to front
    root.state("normal")
    root.deiconify()
    root.lift()
    root.attributes("-topmost", True)
    root.after(250, lambda: root.attributes("-topmost", False))
    root.focus_force()

    if sys.platform == "win32":
        try:
            root.update_idletasks()
            hwnd = int(root.wm_frame(), 16)
            ctypes.windll.user32.ShowWindow(hwnd, 1)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

    root.mainloop()
    return 0

