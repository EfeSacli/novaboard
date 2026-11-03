import os
import sys
import math
import ctypes
from datetime import datetime
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageDraw

from ui_kit import (
    ThemedMixin, font, set_window_icon,
    BTN_ACCENT, BTN_DANGER_SOFT, BTN_INNER,
    CARD, CARD_INNER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
)

if sys.platform == "win32":
    user32 = ctypes.windll.user32
else:
    user32 = None

TRANSPARENT_KEY = "#000001"

PALETTE = [
    ("#ef4444", "Kırmızı"),
    ("#2563eb", "Mavi"),
    ("#16a34a", "Yeşil"),
    ("#eab308", "Sarı"),
    ("#f97316", "Turuncu"),
    ("#9333ea", "Mor"),
    ("#0f172a", "Siyah"),
    ("#ffffff", "Beyaz"),
]

THICKNESS_MAP = {
    "İnce": 2.5,
    "Orta": 4.5,
    "Kalın": 8.0,
    "Çok Kalın": 13.0,
}

BOARD_MODES = [
    "Şeffaf Ekran",
    "Beyaz Tahta",
    "Yeşil Tahta",
    "Siyah Tahta",
    "Kareli Tahta",
    "Çizgili Tahta",
]

TOOL_NAMES = {
    "hand": "Fare / Seçim",
    "pen": "Kalem",
    "highlighter": "Fosforlu Kalem",
    "marker": "Tahta Kalemi",
    "eraser": "Bölgesel Silgi",
    "laser": "Lazer İşaretçi",
    "line": "Düz Çizgi",
    "arrow": "Ok Çizimi",
    "rect": "Dikdörtgen",
    "oval": "Çember / Elips",
    "triangle": "Üçgen",
    "text": "Metin Yaz",
}

SHAPE_TOOLS = ("line", "arrow", "rect", "oval", "triangle", "laser")


def _rounded_rect(d, xy, radius=8, **kwargs):
    if hasattr(d, "rounded_rectangle"):
        d.rounded_rectangle(xy, radius=radius, **kwargs)
    else:
        d.rectangle(xy, **kwargs)


def _make_icon(kind: str, size: int = 26, accent_hex: str = "#ef4444") -> ctk.CTkImage:
    """
    4x supersampling (128x128 -> size x size LANCZOS) ile gerçekçi, net, renkli
    araç ikonları üretir (kalem, fosforlu kalem, silgi, imleç, şekiller, tahta vb.).
    """
    S = 128
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if kind == "hand":
        # Klasik beyaz/mavi fare imleci oku
        pts = [(28, 16), (28, 98), (48, 80), (64, 112), (78, 105), (62, 73), (90, 73)]
        d.polygon(pts, fill="#ffffff", outline="#0f172a")
        d.line(pts + [pts[0]], fill="#0f172a", width=6, joint="curve")
        d.polygon([(34, 28), (34, 84), (49, 70), (76, 68)], fill="#e0f2fe")

    elif kind == "pen":
        # Gerçekçi kurşun/renkli kalem görseli (çapraz)
        # Gövde
        body = [(32, 76), (76, 32), (98, 54), (54, 98)]
        d.polygon(body, fill="#f59e0b", outline="#78350f")
        d.line([(39, 83), (83, 39)], fill="#fbbf24", width=7)
        # Metal halka + pembe tepe silgisi
        cap = [(76, 32), (90, 18), (112, 40), (98, 54)]
        d.polygon(cap, fill="#f43f5e", outline="#881337")
        ferrule = [(72, 36), (80, 28), (102, 50), (94, 58)]
        d.polygon(ferrule, fill="#cbd5e1", outline="#475569")
        # Ahşap uç + aktif renkli kalem ucu
        wood = [(32, 76), (54, 98), (20, 110)]
        d.polygon(wood, fill="#fde68a", outline="#78350f")
        tip = [(26, 92), (38, 104), (18, 110)]
        d.polygon(tip, fill=accent_hex, outline="#0f172a")

    elif kind == "highlighter":
        # Kalın fosforlu kalem (kesik neon sarı/yeşil uçlu)
        body = [(34, 70), (78, 26), (106, 54), (62, 98)]
        d.polygon(body, fill="#facc15", outline="#713f12")
        stripe = [(44, 76), (84, 36), (94, 46), (54, 86)]
        d.polygon(stripe, fill="#fef08a")
        # Gri boyunluk
        neck = [(26, 78), (34, 70), (62, 98), (54, 106)]
        d.polygon(neck, fill="#334155", outline="#0f172a")
        # Kesik fosforlu keçe uç
        nib = [(14, 98), (26, 78), (50, 102), (30, 114)]
        d.polygon(nib, fill="#a3e635", outline="#15803d")

    elif kind == "marker":
        # Beyaz gövdeli akıllı tahta kalemi (kesik uç)
        body = [(34, 72), (82, 24), (106, 48), (58, 96)]
        d.polygon(body, fill="#f8fafc", outline="#334155")
        band = [(68, 38), (82, 24), (106, 48), (92, 62)]
        d.polygon(band, fill=accent_hex, outline="#1e293b")
        nib = [(16, 98), (34, 72), (56, 94), (32, 112)]
        d.polygon(nib, fill=accent_hex, outline="#0f172a")

    elif kind == "eraser":
        # Klasik pembe-mavi iki renkli gerçek silgi görseli
        pink_part = [(18, 74), (56, 36), (92, 72), (54, 110)]
        blue_part = [(56, 36), (82, 18), (114, 50), (92, 72)]
        sleeve = [(46, 46), (66, 28), (100, 62), (80, 82)]
        d.polygon(pink_part, fill="#fb7185", outline="#881337")
        d.polygon(blue_part, fill="#38bdf8", outline="#0369a1")
        d.polygon(sleeve, fill="#f8fafc", outline="#475569")
        d.line([(18, 74), (54, 110), (92, 72)], fill="#881337", width=4)

    elif kind == "shapes":
        # Geometrik şekiller grubu (dikdörtgen + çember + üçgen)
        d.rectangle([16, 20, 68, 68], fill="#3b82f6", outline="#ffffff", width=5)
        d.ellipse([54, 50, 112, 108], fill="#10b981", outline="#ffffff", width=5)
        d.polygon([(68, 14), (112, 54), (44, 54)], fill="#f59e0b", outline="#ffffff")

    elif kind == "line":
        d.line([(20, 104), (108, 24)], fill="#38bdf8", width=12)
        d.ellipse([12, 96, 30, 114], fill="#ffffff", outline="#0284c7", width=4)
        d.ellipse([98, 14, 116, 32], fill="#ffffff", outline="#0284c7", width=4)

    elif kind == "arrow":
        d.line([(20, 104), (102, 22)], fill="#f97316", width=12)
        d.polygon([(112, 16), (70, 22), (104, 56)], fill="#f97316", outline="#ffffff")

    elif kind == "rect":
        d.rectangle([18, 26, 110, 102], fill=None, outline="#38bdf8", width=11)

    elif kind == "oval":
        d.ellipse([18, 22, 110, 106], fill=None, outline="#a855f7", width=11)

    elif kind == "triangle":
        d.polygon([(64, 18), (16, 106), (112, 106)], fill=None, outline="#eab308")
        d.line([(64, 18), (16, 106), (112, 106), (64, 18)], fill="#eab308", width=10, joint="curve")

    elif kind == "laser":
        # Parlayan kırmızı/sarı lazer ışını
        for ang in range(0, 360, 45):
            rad = math.radians(ang)
            x2 = 64 + int(46 * math.cos(rad))
            y2 = 64 + int(46 * math.sin(rad))
            d.line([(64, 64), (x2, y2)], fill="#ef4444", width=7)
        d.ellipse([36, 36, 92, 92], fill="#ef4444", outline="#fca5a5", width=4)
        d.ellipse([48, 48, 80, 80], fill="#fef08a")

    elif kind == "text":
        # Çerçeveli büyük 'T' metin ikonu
        d.rectangle([16, 16, 112, 112], outline="#94a3b8", width=5)
        d.rectangle([30, 30, 98, 46], fill="#38bdf8")
        d.rectangle([56, 30, 72, 100], fill="#38bdf8")

    elif kind == "palette":
        # Renk paleti + aktif renk halkası
        d.ellipse([14, 14, 114, 114], fill="#1e293b", outline="#cbd5e1", width=6)
        ring_cols = ["#ef4444", "#3b82f6", "#16a34a", "#eab308", "#f97316", "#a855f7"]
        for idx, c in enumerate(ring_cols):
            ang = math.radians(idx * 60)
            cx = 64 + int(33 * math.cos(ang))
            cy = 64 + int(33 * math.sin(ang))
            d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=c)
        d.ellipse([42, 42, 86, 86], fill=accent_hex, outline="#ffffff", width=5)

    elif kind == "board":
        # Yeşil sınıf tahtası ikonu
        _rounded_rect(d, [12, 20, 116, 98], radius=10, fill="#0f3822", outline="#d97706", width=8)
        d.line([(28, 46), (82, 46)], fill="#ffffff", width=6)
        d.line([(28, 66), (64, 66)], fill="#86efac", width=6)
        d.rectangle([28, 98, 100, 110], fill="#b45309")

    elif kind == "curtain":
        # Ekran perdesi ikonu
        _rounded_rect(d, [14, 16, 114, 112], radius=8, fill="#0f172a", outline="#38bdf8", width=6)
        d.rectangle([20, 68, 108, 106], fill="#cbd5e1")
        d.ellipse([48, 54, 80, 82], fill="#0284c7", outline="#ffffff", width=4)

    elif kind == "undo":
        # Geri al kıvrımlı sol ok
        d.arc([24, 34, 108, 108], start=180, end=350, fill="#e2e8f0", width=12)
        d.polygon([(14, 66), (48, 36), (48, 76)], fill="#e2e8f0")

    elif kind == "redo":
        # İleri al kıvrımlı sağ ok
        d.arc([20, 34, 104, 108], start=190, end=360, fill="#e2e8f0", width=12)
        d.polygon([(114, 66), (80, 36), (80, 76)], fill="#e2e8f0")

    elif kind == "camera":
        # Ekran görüntüsü kamera ikonu
        _rounded_rect(d, [14, 34, 114, 104], radius=12, fill="#38bdf8", outline="#ffffff", width=5)
        d.polygon([(42, 34), (52, 18), (76, 18), (86, 34)], fill="#38bdf8", outline="#ffffff")
        d.ellipse([44, 48, 84, 88], fill="#0f172a", outline="#ffffff", width=6)

    elif kind == "trash":
        # Çöp kutusu / temizle ikonu
        d.rectangle([26, 26, 102, 38], fill="#fca5a5")
        d.rectangle([48, 16, 80, 26], fill="#fca5a5")
        d.polygon([(32, 42), (96, 42), (88, 110), (40, 110)], fill="#ef4444", outline="#fecaca")
        d.line([(52, 54), (54, 96)], fill="#ffffff", width=6)
        d.line([(76, 54), (74, 96)], fill="#ffffff", width=6)

    resample_filter = getattr(getattr(Image, "Resampling", Image), "LANCZOS", getattr(Image, "ANTIALIAS", 1))
    resized = img.resize((size, size), resample_filter)
    return ctk.CTkImage(light_image=resized, dark_image=resized, size=(size, size))


class ScreenPenHUD(ThemedMixin, ctk.CTkToplevel):
    """
    Novaboard - Kompakt Dikey Akıllı Tahta Kalemi (Fatih Kalem) Araç Çubuğu.

    Özellikler:
      * Ekranın sol kenarında çok az yer kaplayan (56 px genişliğinde) dikey ikon çubuğu
      * Kalem, Fosforlu Kalem, Silgi, Fare, Şekiller, Renk/Kalınlık ve Tahta için
        özel çizilmiş görsel ikonlar
      * Silgi, Renk/Boyut, Şekiller ve Tahta Modu için yan tarafta açılan ve çizime
        başlandığında otomatik kapanan açılır pencereler (popover)
      * Gerçek bölgesel silgi (yalnızca değdiği 4px'lik parçaları siler) ve ayarlanabilir silgi çapı
    """

    def __init__(self, master, data_manager, sound_player, theme_manager, on_raise_peers=None, on_return_to_main=None):
        super().__init__(master)
        self.master_win = master
        self.dm = data_manager
        self.sound = sound_player
        self.tm = theme_manager
        self.on_raise_peers = on_raise_peers
        self.on_return_to_main = on_return_to_main

        self.overrideredirect(True)
        set_window_icon(self, default=False)

        # Kompakt dikey çubuk boyutları
        self.bar_width = 56
        self.expanded_height = 468
        self.collapsed_height = 54
        self.margin_left = 8

        self._is_collapsed = False
        self._is_animating_slide = False
        self._active_popover_name = None

        # Çizim ve silgi durumu
        self.current_tool = "hand"
        self.current_color = PALETTE[0][0]
        self.thickness_label = "Orta"
        self.current_width = THICKNESS_MAP["Orta"]
        self.eraser_radius = int(self.dm.get_setting("pen_eraser_radius", 24) or 24)
        self.board_mode = "Şeffaf Ekran"
        self.curtain_active = False
        self.curtain_y = 260

        self.item_specs = {}
        self.undo_stack = []
        self.redo_stack = []

        self.current_stroke_ids = []
        self._current_erased_specs = []
        self._shape_preview_ids = []
        self._eraser_cursor_id = None
        self._start_x = None
        self._start_y = None
        self._last_x = None
        self._last_y = None
        self._active_text_entry = None

        # Sürükleme durumu
        self._is_dragging = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._win_orig_x = 0
        self._win_orig_y = 0
        self._custom_pos_set = False
        self.pos_x = self.margin_left
        self.pos_y = 60
        self._load_or_compute_position()

        # 1. Çizim Katmanı & 2. Giriş Yakalayıcı Katman
        self._setup_canvas_layers()

        # 3. Açılır yan pencere (Popover) ve Ipucu (Tooltip)
        self._setup_popover_window()
        self._setup_tooltip_window()

        # 4. Kompakt Dikey Araç Çubuğu
        self.attributes("-topmost", True)
        self.geometry(f"{self.bar_width}x{self.expanded_height}+{self.pos_x}+{self.pos_y}")
        self._build_icons()
        self._setup_ui()
        self._bind_events()
        self.apply_theme()
        self.tm.register_callback(self.apply_theme)

        self.select_tool("hand", play_sound=False)
        self.after(60, self._ensure_topmost_lock)

    # =========================================================================
    # İKONLAR, POPOVER (AÇILIR PENCERE) VE İPUCU (TOOLTIP)
    # =========================================================================
    def _build_icons(self):
        self.icons = {
            "hand": _make_icon("hand", 26),
            "pen": _make_icon("pen", 26, self.current_color),
            "highlighter": _make_icon("highlighter", 26),
            "marker": _make_icon("marker", 22, self.current_color),
            "eraser": _make_icon("eraser", 26),
            "shapes": _make_icon("shapes", 26),
            "line": _make_icon("line", 22),
            "arrow": _make_icon("arrow", 22),
            "rect": _make_icon("rect", 22),
            "oval": _make_icon("oval", 22),
            "triangle": _make_icon("triangle", 22),
            "laser": _make_icon("laser", 22),
            "text": _make_icon("text", 24),
            "palette": _make_icon("palette", 26, self.current_color),
            "board": _make_icon("board", 26),
            "curtain": _make_icon("curtain", 22),
            "undo": _make_icon("undo", 22),
            "redo": _make_icon("redo", 22),
            "camera": _make_icon("camera", 22),
            "trash": _make_icon("trash", 22),
        }

    def _refresh_color_dependent_icons(self):
        self.icons["pen"] = _make_icon("pen", 26, self.current_color)
        self.icons["palette"] = _make_icon("palette", 26, self.current_color)
        self.icons["marker"] = _make_icon("marker", 22, self.current_color)
        if hasattr(self, "tool_buttons") and "pen" in self.tool_buttons:
            self.tool_buttons["pen"].configure(image=self.icons["pen"])
        if hasattr(self, "palette_btn"):
            self.palette_btn.configure(image=self.icons["palette"])

    def _setup_popover_window(self):
        self.popover = ctk.CTkToplevel(self)
        self.popover.overrideredirect(True)
        self.popover.attributes("-topmost", True)
        self.popover.withdraw()
        self.popover_frame = self.styled(
            ctk.CTkFrame(self.popover, corner_radius=10, border_width=1.5),
            fg_color="bg_main", border_color="border",
        )
        self.popover_frame.pack(fill="both", expand=True)

    def _get_scaling(self):
        try:
            return ctk.ScalingTracker.get_window_scaling(self)
        except Exception:
            return 1.0

    def _setup_tooltip_window(self):
        self.tooltip_win = tk.Toplevel(self)
        self.tooltip_win.overrideredirect(True)
        self.tooltip_win.attributes("-topmost", True)
        self.tooltip_win.configure(bg="#0f172a")
        px_font = max(11, int(round(12 * self._get_scaling() * getattr(ctk.ScalingTracker, "font_size_correction", 1.0))))
        self.tooltip_lbl = tk.Label(
            self.tooltip_win, text="", bg="#0f172a", fg="#f8fafc",
            font=("Segoe UI", -px_font, "bold"), padx=8, pady=3, relief="solid", bd=1
        )
        self.tooltip_lbl.pack()
        self.tooltip_win.withdraw()

    def _attach_tooltip(self, widget, text_fn):
        def _enter(_e):
            if self._active_popover_name:
                return
            txt = text_fn() if callable(text_fn) else str(text_fn)
            self.tooltip_lbl.configure(text=txt)
            self.tooltip_win.update_idletasks()
            actual_bar_w = max(self.winfo_width(), int(round(self.bar_width * self._get_scaling())))
            rx = self.winfo_rootx() + actual_bar_w + 6
            ry = widget.winfo_rooty() + 4
            self.tooltip_win.geometry(f"+{rx}+{ry}")
            self.tooltip_win.deiconify()
            self.tooltip_win.lift()

        def _leave(_e):
            self.tooltip_win.withdraw()

        widget.bind("<Enter>", _enter, add="+")
        widget.bind("<Leave>", _leave, add="+")

    def close_popover(self):
        self._active_popover_name = None
        if hasattr(self, "popover") and self.popover.winfo_exists():
            self.popover.withdraw()
        self._refresh_button_Highlights()

    def toggle_popover(self, name: str, anchor_widget):
        self.tooltip_win.withdraw()
        if self._active_popover_name == name:
            self.close_popover()
            return

        for child in self.popover_frame.winfo_children():
            child.destroy()

        self._active_popover_name = name
        if name == "eraser":
            self._build_eraser_popover(self.popover_frame)
            w, h = 230, 118
        elif name == "palette":
            self._build_palette_popover(self.popover_frame)
            w, h = 248, 172
        elif name == "shapes":
            self._build_shapes_popover(self.popover_frame)
            w, h = 216, 186
        elif name == "board":
            self._build_board_popover(self.popover_frame)
            w, h = 210, 244
        else:
            return

        self.apply_theme()
        scale = self._get_scaling()
        actual_bar_w = max(self.winfo_width(), int(round(self.bar_width * scale)))
        actual_pop_w = int(round(w * scale))
        actual_pop_h = int(round(h * scale))
        gap = max(6, int(round(6 * scale)))
        px = self.winfo_rootx() + actual_bar_w + gap
        if px + actual_pop_w > self._get_screen_width() - 10:
            px = max(10, self.winfo_rootx() - actual_pop_w - gap)
        py = max(10, min(self.winfo_screenheight() - actual_pop_h - 10, anchor_widget.winfo_rooty() - 6))
        self.popover.geometry(f"{w}x{h}+{px}+{py}")
        self.popover.deiconify()
        self.popover.lift()
        self._refresh_button_Highlights()

    def _build_eraser_popover(self, parent):
        head = ctk.CTkFrame(parent, fg_color="transparent")
        head.pack(fill="x", padx=10, pady=(8, 2))
        self.styled(ctk.CTkLabel(head, text="Silgi Boyutu", font=font(11, bold=True)), TEXT_PRIMARY).pack(side="left")
        self.eraser_size_label = self.styled(
            ctk.CTkLabel(head, text=f"{self.eraser_radius} px", font=font(11, bold=True)), TEXT_ACCENT
        )
        self.eraser_size_label.pack(side="right")

        self.eraser_slider = ctk.CTkSlider(
            parent, from_=8, to=90, number_of_steps=82, height=16, command=self._on_eraser_slider_change
        )
        self.eraser_slider.set(self.eraser_radius)
        self.eraser_slider.pack(fill="x", padx=10, pady=(4, 6))

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        for lbl, val in [("Küçük", 12), ("Orta", 26), ("Büyük", 48), ("Dev", 75)]:
            b = self.styled(
                ctk.CTkButton(
                    btn_row, text=lbl, height=26, width=46, corner_radius=5, font=font(10, bold=True),
                    border_width=1, command=lambda v=val: self.set_eraser_radius(v),
                ),
                BTN_INNER,
            )
            b.pack(side="left", expand=True, fill="x", padx=2)

    def _build_palette_popover(self, parent):
        self.styled(
            ctk.CTkLabel(parent, text="Renk Seçimi", font=font(11, bold=True)), TEXT_PRIMARY
        ).pack(anchor="w", padx=10, pady=(8, 4))

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", padx=8, pady=2)
        self.color_buttons = {}
        for idx, (hex_col, _name) in enumerate(PALETTE):
            b = ctk.CTkButton(
                grid, text="", width=28, height=26, corner_radius=6,
                fg_color=hex_col, hover_color=hex_col,
                border_width=2.5 if hex_col.lower() == self.current_color.lower() else 1,
                border_color="#38bdf8" if hex_col.lower() == self.current_color.lower() else "#64748b",
                command=lambda c=hex_col: (self.select_color(c), self.close_popover()),
            )
            b.grid(row=0, column=idx, padx=2, pady=2)
            self.color_buttons[hex_col] = b

        custom_b = self.styled(
            ctk.CTkButton(
                parent, text="Özel Renk Seç...", height=26, corner_radius=5, font=font(10, bold=True),
                border_width=1, command=lambda: (self.close_popover(), self.pick_custom_color()),
            ),
            BTN_INNER,
        )
        custom_b.pack(fill="x", padx=10, pady=(4, 6))

        self.styled(
            ctk.CTkLabel(parent, text="Kalem Kalınlığı", font=font(11, bold=True)), TEXT_PRIMARY
        ).pack(anchor="w", padx=10, pady=(2, 4))

        w_row = ctk.CTkFrame(parent, fg_color="transparent")
        w_row.pack(fill="x", padx=8, pady=(0, 8))
        self.width_buttons = {}
        for lbl in THICKNESS_MAP:
            wb = ctk.CTkButton(
                w_row, text=lbl, height=26, width=48, corner_radius=5, font=font(10, bold=True),
                border_width=1, command=lambda l=lbl: (self.select_thickness(l), self.close_popover()),
            )
            wb.pack(side="left", expand=True, fill="x", padx=2)
            self.width_buttons[lbl] = wb

    def _build_shapes_popover(self, parent):
        self.styled(
            ctk.CTkLabel(parent, text="Şekiller ve Kalemler", font=font(11, bold=True)), TEXT_PRIMARY
        ).pack(anchor="w", padx=10, pady=(8, 4))

        items = [
            ("line", "Düz Çizgi"),
            ("arrow", "Ok Çizimi"),
            ("rect", "Dikdörtgen"),
            ("oval", "Çember / Elips"),
            ("triangle", "Üçgen"),
            ("marker", "Kesik Uçlu Kalem"),
            ("laser", "Lazer İşaretçi"),
        ]
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        grid.grid_columnconfigure((0, 1), weight=1)

        for idx, (tid, title) in enumerate(items):
            r, c = divmod(idx, 2)
            b = ctk.CTkButton(
                grid,
                text=title,
                image=self.icons.get(tid),
                compound="left",
                anchor="w",
                height=30,
                corner_radius=6,
                font=font(10, bold=True),
                border_width=1,
                command=lambda t=tid: (self.close_popover(), self.select_tool(t)),
            )
            if idx == len(items) - 1:
                b.grid(row=r, column=0, columnspan=2, padx=2, pady=2, sticky="ew")
            else:
                b.grid(row=r, column=c, padx=2, pady=2, sticky="ew")

    def _build_board_popover(self, parent):
        self.styled(
            ctk.CTkLabel(parent, text="Tahta Arka Planı", font=font(11, bold=True)), TEXT_PRIMARY
        ).pack(anchor="w", padx=10, pady=(8, 4))

        for mode in BOARD_MODES:
            is_cur = mode == self.board_mode
            b = self.styled(
                ctk.CTkButton(
                    parent,
                    text=f"✓ {mode}" if is_cur else mode,
                    height=26,
                    corner_radius=5,
                    font=font(10, bold=True),
                    border_width=1,
                    command=lambda m=mode: (self.close_popover(), self.set_board_mode(m)),
                ),
                BTN_ACCENT if is_cur else BTN_INNER,
            )
            b.pack(fill="x", padx=10, pady=1.5)

        curtain_txt = "Ekran Perdesini Kapat" if self.curtain_active else "Ekran Perdesini Aç"
        cb = self.styled(
            ctk.CTkButton(
                parent,
                text=curtain_txt,
                image=self.icons["curtain"],
                compound="left",
                height=28,
                corner_radius=5,
                font=font(10, bold=True),
                border_width=1,
                command=lambda: (self.close_popover(), self.toggle_curtain()),
            ),
            BTN_ACCENT if self.curtain_active else BTN_INNER,
        )
        cb.pack(fill="x", padx=10, pady=(6, 8))

    # =========================================================================
    # ÇİZİM VE GİRİŞ KATMANLARI (Çift Katmanlı Mimari)
    # =========================================================================
    def _setup_canvas_layers(self):
        sw = self._get_screen_width()
        sh = self.winfo_screenheight()

        self.draw_win = tk.Toplevel(self.master_win)
        self.draw_win.title("Novaboard Kalem Çizim Katmanı")
        self.draw_win.overrideredirect(True)
        self.draw_win.geometry(f"{sw}x{sh}+0+0")
        self.draw_win.attributes("-topmost", True)
        if sys.platform == "win32":
            try:
                self.draw_win.attributes("-transparentcolor", TRANSPARENT_KEY)
            except Exception:
                pass
        self.draw_win.configure(bg=TRANSPARENT_KEY)

        self.canvas = tk.Canvas(
            self.draw_win, width=sw, height=sh, bg=TRANSPARENT_KEY, highlightthickness=0, bd=0
        )
        self.canvas.pack(fill="both", expand=True)
        self._make_draw_win_clickthrough()

        if sys.platform != "win32":
            self.canvas.bind("<Button-1>", self._on_input_down)
            self.canvas.bind("<B1-Motion>", self._on_input_drag)
            self.canvas.bind("<ButtonRelease-1>", self._on_input_up)
            self.canvas.bind("<Motion>", self._on_input_hover)
            self.canvas.bind("<Button-3>", lambda _e: self.select_tool("hand"))
            self.draw_win.bind("<Escape>", lambda _e: self.select_tool("hand"))

        self.input_win = tk.Toplevel(self.master_win)
        self.input_win.title("Novaboard Kalem Giriş Katmanı")
        self.input_win.overrideredirect(True)
        self.input_win.geometry(f"{sw}x{sh}+0+0")
        self.input_win.attributes("-topmost", True)
        try:
            self.input_win.attributes("-alpha", 0.01)
        except Exception:
            pass
        self.input_win.configure(bg="black")

        self.input_win.bind("<Button-1>", self._on_input_down)
        self.input_win.bind("<B1-Motion>", self._on_input_drag)
        self.input_win.bind("<ButtonRelease-1>", self._on_input_up)
        self.input_win.bind("<Motion>", self._on_input_hover)
        self.input_win.bind("<Button-3>", lambda _e: self.select_tool("hand"))
        self.input_win.bind("<Escape>", lambda _e: self.select_tool("hand"))

        self.draw_win.withdraw()
        self.input_win.withdraw()

    def _make_draw_win_clickthrough(self):
        if sys.platform == "win32" and user32:
            try:
                self.draw_win.update_idletasks()
                hwnd = user32.GetAncestor(self.draw_win.winfo_id(), 2)
                style = user32.GetWindowLongW(hwnd, -20)
                user32.SetWindowLongW(hwnd, -20, style | 0x80000 | 0x20)
            except Exception:
                pass

    def _ensure_topmost_lock(self):
        try:
            if self.draw_win.winfo_exists() and self.draw_win.state() != "withdrawn":
                self.draw_win.attributes("-topmost", True)
                self.draw_win.lift()
            if self.input_win.winfo_exists() and self.input_win.state() != "withdrawn":
                self.input_win.attributes("-topmost", True)
                self.input_win.lift()
            if self.winfo_exists() and self.state() != "withdrawn":
                self.attributes("-topmost", True)
                self.lift()
            if hasattr(self, "popover") and self.popover.winfo_exists() and self.popover.state() != "withdrawn":
                self.popover.attributes("-topmost", True)
                self.popover.lift()
            if self.on_raise_peers:
                self.on_raise_peers()
        except Exception:
            pass

    def _sync_layer_visibility(self):
        has_board = self.board_mode != "Şeffaf Ekran"
        has_content = bool(self.item_specs) or has_board or self.curtain_active
        needs_input = (not self._is_collapsed) and (self.current_tool != "hand" or self.curtain_active)

        if sys.platform != "win32":
            # Linux/Pardus X11'de -transparentcolor desteklenmediği için yalnızca çizim/tahta aktifken göster
            if needs_input or has_board or self.curtain_active:
                sw = self._get_screen_width()
                sh = self.winfo_screenheight()
                if has_board:
                    self.canvas.delete("linux_screen_bg")
                    self._linux_bg_photo = None
                elif getattr(self, "_linux_bg_photo", None) is None:
                    self._prepare_linux_transparent_bg()
                self.draw_win.geometry(f"{sw}x{sh}+0+0")
                self.draw_win.deiconify()
                self.draw_win.lift()
            else:
                self.draw_win.withdraw()
            self.input_win.withdraw()
            self._ensure_topmost_lock()
            return

        if has_content or needs_input:
            self.draw_win.deiconify()
        else:
            self.draw_win.withdraw()

        if needs_input and self.state() != "withdrawn":
            self.input_win.deiconify()
        else:
            self.input_win.withdraw()
            self._clear_eraser_cursor()

        self._ensure_topmost_lock()

    def _prepare_linux_transparent_bg(self):
        """Linux/Pardus X11 üzerinde şeffaf ekran modunda masaüstü görüntüsünü hızlıca arka plan olarak yakalar."""
        try:
            from PIL import ImageGrab, ImageTk
            self.draw_win.withdraw()
            self.update_idletasks()
            grabbed = ImageGrab.grab()
            self._linux_bg_photo = ImageTk.PhotoImage(grabbed)
            self.canvas.delete("linux_screen_bg")
            self.canvas.create_image(0, 0, image=self._linux_bg_photo, anchor="nw", tags=("linux_screen_bg",))
            self.canvas.tag_lower("linux_screen_bg")
        except Exception:
            self.canvas.configure(bg="#f8fafc")

    # =========================================================================
    # DİKEY KOMPAKT İKON ÇUBUĞU ARAYÜZÜ
    # =========================================================================
    def _setup_ui(self):
        self.main_container = self.styled(
            ctk.CTkFrame(self, corner_radius=12, border_width=1.5), fg_color="bg_main", border_color="border"
        )
        self.main_container.pack(fill="both", expand=True)

        # 1. Üst Sürükleme ve Daraltma Başlığı (Her zaman görünür)
        self.top_bar = self.styled(
            ctk.CTkFrame(self.main_container, height=48, corner_radius=10), fg_color="bg_sidebar"
        )
        self.top_bar.pack(side="top", fill="x", padx=3, pady=3)
        self.top_bar.pack_propagate(False)

        self.drag_grip = self.styled(
            ctk.CTkLabel(self.top_bar, text="::::", height=14, font=font(10, bold=True), cursor="fleur"),
            TEXT_ACCENT,
        )
        self.drag_grip.pack(side="top", pady=(2, 0))
        self._attach_tooltip(self.drag_grip, "Kalem Çubuğunu Taşı")

        self.toggle_btn = self.styled(
            ctk.CTkButton(
                self.top_bar, text="▲", width=44, height=24, corner_radius=6,
                font=font(11, bold=True), command=self.toggle_collapse,
            ),
            BTN_ACCENT,
        )
        self.toggle_btn.pack(side="top", padx=3, pady=(1, 2))
        self._attach_tooltip(self.toggle_btn, lambda: "Kalem Çubuğunu Aç" if self._is_collapsed else "Kalem Çubuğunu Küçült")

        # 2. Dikey İkon Listesi (Küçültüldüğünde gizlenir)
        self.content_panel = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_panel.pack(side="top", fill="both", expand=True, padx=4, pady=(0, 4))

        self.tool_buttons = {}

        # Ana çizim araçları (Dikey)
        primary_tools = [
            ("hand", "hand", "Fare / Gezinme Modu", lambda: self._on_primary_tool_click("hand")),
            ("pen", "pen", "Kalem (Tekrar tıkla: Renk & Boyut)", lambda: self._on_pen_button_click("pen")),
            ("highlighter", "highlighter", "Fosforlu Kalem", lambda: self._on_pen_button_click("highlighter")),
            ("eraser", "eraser", lambda: f"Bölgesel Silgi ({self.eraser_radius} px) - Tıkla: Boyut Ayarla", self._on_eraser_button_click),
            ("shapes", "shapes", "Şekiller, Ok, Tahta Kalemi ve Lazer", self._on_shapes_button_click),
            ("text", "text", "Metin Yazma Aracı", lambda: self._on_primary_tool_click("text")),
        ]

        for tid, icon_key, tip, cmd in primary_tools:
            btn = ctk.CTkButton(
                self.content_panel,
                text="",
                image=self.icons[icon_key],
                width=44,
                height=38,
                corner_radius=8,
                border_width=1.5,
                command=cmd,
            )
            btn.pack(side="top", pady=2)
            self._attach_tooltip(btn, tip)
            self.tool_buttons[tid] = btn

        # Ayırıcı çizgi
        sep1 = self.styled(ctk.CTkFrame(self.content_panel, height=2), fg_color="border")
        sep1.pack(fill="x", padx=4, pady=3)

        # Açılır Pencere Butonları: Renk/Boyut & Tahta/Perde
        self.palette_btn = self.styled(
            ctk.CTkButton(
                self.content_panel,
                text="",
                image=self.icons["palette"],
                width=44,
                height=36,
                corner_radius=8,
                border_width=1.5,
                command=lambda: self.toggle_popover("palette", self.palette_btn),
            ),
            BTN_INNER,
        )
        self.palette_btn.pack(side="top", pady=2)
        self._attach_tooltip(self.palette_btn, lambda: f"Renk ve Kalem Kalınlığı ({self.thickness_label})")

        self.board_btn = self.styled(
            ctk.CTkButton(
                self.content_panel,
                text="",
                image=self.icons["board"],
                width=44,
                height=36,
                corner_radius=8,
                border_width=1.5,
                command=lambda: self.toggle_popover("board", self.board_btn),
            ),
            BTN_INNER,
        )
        self.board_btn.pack(side="top", pady=2)
        self._attach_tooltip(self.board_btn, lambda: f"Tahta Modu ({self.board_mode}) ve Ekran Perdesi")

        # Ayırıcı çizgi
        sep2 = self.styled(ctk.CTkFrame(self.content_panel, height=2), fg_color="border")
        sep2.pack(fill="x", padx=4, pady=3)

        # Alt Hızlı Eylemler: Geri Al & İleri Al yan yana (2 küçük ikon), Kamera ve Tümünü Sil
        ur_row = ctk.CTkFrame(self.content_panel, fg_color="transparent")
        ur_row.pack(fill="x", pady=1)

        self.undo_btn = self.styled(
            ctk.CTkButton(
                ur_row, text="", image=self.icons["undo"], width=21, height=28,
                corner_radius=6, border_width=1, command=self.undo_last,
            ),
            BTN_INNER,
        )
        self.undo_btn.pack(side="left", expand=True, padx=(0, 1))
        self._attach_tooltip(self.undo_btn, "Geri Al")

        self.redo_btn = self.styled(
            ctk.CTkButton(
                ur_row, text="", image=self.icons["redo"], width=21, height=28,
                corner_radius=6, border_width=1, command=self.redo_last,
            ),
            BTN_INNER,
        )
        self.redo_btn.pack(side="right", expand=True, padx=(1, 0))
        self._attach_tooltip(self.redo_btn, "İleri Al")

        act_row = ctk.CTkFrame(self.content_panel, fg_color="transparent")
        act_row.pack(fill="x", pady=2)

        self.shot_btn = self.styled(
            ctk.CTkButton(
                act_row, text="", image=self.icons["camera"], width=21, height=28,
                corner_radius=6, border_width=1, command=self.save_screenshot,
            ),
            BTN_INNER,
        )
        self.shot_btn.pack(side="left", expand=True, padx=(0, 1))
        self._attach_tooltip(self.shot_btn, "Ekran Görüntüsü Kaydet")

        self.clear_btn = self.styled(
            ctk.CTkButton(
                act_row, text="", image=self.icons["trash"], width=21, height=28,
                corner_radius=6, command=self.clear_all,
            ),
            BTN_DANGER_SOFT,
        )
        self.clear_btn.pack(side="right", expand=True, padx=(1, 0))
        self._attach_tooltip(self.clear_btn, "Tüm Çizimleri Temizle")

    def _on_primary_tool_click(self, tool_id: str):
        self.close_popover()
        self.select_tool(tool_id)

    def _on_pen_button_click(self, tool_id: str):
        if self.current_tool == tool_id:
            self.toggle_popover("palette", self.tool_buttons[tool_id])
        else:
            self.close_popover()
            self.select_tool(tool_id)

    def _on_eraser_button_click(self):
        if self.current_tool != "eraser":
            self.select_tool("eraser")
            self.toggle_popover("eraser", self.tool_buttons["eraser"])
        else:
            self.toggle_popover("eraser", self.tool_buttons["eraser"])

    def _on_shapes_button_click(self):
        self.toggle_popover("shapes", self.tool_buttons["shapes"])

    def _bind_events(self):
        self.bind("<FocusOut>", lambda _e: self._ensure_topmost_lock())
        self.bind("<FocusIn>", lambda _e: self._ensure_topmost_lock())

        for w in (self.drag_grip, self.top_bar, self.main_container):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)
            w.bind("<ButtonRelease-1>", self._end_drag)

    # =========================================================================
    # SERBEST TAŞIMA VE EKRAN KONUMU (SOL KENAR DİKEY VARSAYILAN)
    # =========================================================================
    def _load_or_compute_position(self):
        scale = self._get_scaling()
        sw = self._get_screen_width()
        sh = self.winfo_screenheight()
        actual_w = int(round(self.bar_width * scale))
        actual_h = int(round(self.expanded_height * scale))
        saved_x = self.dm.get_setting("pen_pos_x", None)
        saved_y = self.dm.get_setting("pen_pos_y", None)
        if saved_x is not None and saved_y is not None:
            sx, sy = int(saved_x), int(saved_y)
            if 0 <= sx <= max(0, sw - actual_w) and 0 <= sy <= max(0, sh - actual_h):
                self.pos_x = sx
                self.pos_y = sy
                self._custom_pos_set = True
                return
        self.pos_x = int(round(self.margin_left * scale))
        self.pos_y = int(round(60 * scale))
        self._custom_pos_set = False

    def _get_screen_width(self):
        try:
            if sys.platform == "win32" and user32:
                sw = user32.GetSystemMetrics(0)
                if sw > 0:
                    return sw
        except Exception:
            pass
        return self.winfo_screenwidth()

    def _start_drag(self, event):
        self.close_popover()
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._win_orig_x = self.winfo_x()
        self._win_orig_y = self.winfo_y()
        self._is_dragging = True

    def _on_drag(self, event):
        if not self._is_dragging:
            return
        scale = self._get_scaling()
        cur_h = self.collapsed_height if self._is_collapsed else self.expanded_height
        actual_w = int(round(self.bar_width * scale))
        actual_h = int(round(cur_h * scale))
        new_x = max(0, min(self._get_screen_width() - actual_w, self._win_orig_x + event.x_root - self._drag_start_x))
        new_y = max(0, min(self.winfo_screenheight() - actual_h, self._win_orig_y + event.y_root - self._drag_start_y))

        self.pos_x = new_x
        self.pos_y = new_y
        self._custom_pos_set = True
        self.geometry(f"{self.bar_width}x{cur_h}+{new_x}+{new_y}")

    def _end_drag(self, _event):
        self._is_dragging = False
        try:
            self.dm.set_setting("pen_pos_x", self.pos_x)
            self.dm.set_setting("pen_pos_y", self.pos_y)
        except Exception:
            pass

    # =========================================================================
    # DİKEY AÇILMA / KÜÇÜLME ANİMASYONU
    # =========================================================================
    def toggle_collapse(self):
        if self._is_animating_slide:
            return

        self.close_popover()
        self._is_animating_slide = True
        self._is_collapsed = not self._is_collapsed
        self.sound.play_tick()

        start_h = self.expanded_height if self._is_collapsed else self.collapsed_height
        target_h = self.collapsed_height if self._is_collapsed else self.expanded_height
        steps = 8
        cur_step = 0

        if self._is_collapsed:
            self.content_panel.pack_forget()
            self._sync_layer_visibility()

        def _place_at_height(h):
            self.geometry(f"{self.bar_width}x{h}+{self.pos_x}+{self.pos_y}")

        def _step_anim():
            nonlocal cur_step
            cur_step += 1
            eased = 1.0 - (1.0 - cur_step / steps) ** 2
            _place_at_height(int(start_h + (target_h - start_h) * eased))

            if cur_step < steps:
                self.after(16, _step_anim)
            else:
                _place_at_height(target_h)
                self._is_animating_slide = False
                if self._is_collapsed:
                    self.toggle_btn.configure(text="▼")
                else:
                    self.content_panel.pack(side="top", fill="both", expand=True, padx=4, pady=(0, 4))
                    self.toggle_btn.configure(text="▲")
                self._sync_layer_visibility()

        _step_anim()

    def show_pen_hud(self, expand=False):
        self.deiconify()
        if expand and self._is_collapsed:
            self.toggle_collapse()
        else:
            cur_h = self.collapsed_height if self._is_collapsed else self.expanded_height
            self.geometry(f"{self.bar_width}x{cur_h}+{self.pos_x}+{self.pos_y}")
            self._sync_layer_visibility()

    def reset_and_clear(self):
        """Ekrandaki tüm kalem çizimlerini, metinleri, tahta arka planını ve perdeyi tamamen temizler."""
        self._cancel_active_text()
        self.close_popover()
        if hasattr(self, "tooltip_win") and self.tooltip_win.winfo_exists():
            self.tooltip_win.withdraw()
        self._clear_eraser_cursor()
        if hasattr(self, "canvas") and self.canvas.winfo_exists():
            self.canvas.delete("all")
        self.item_specs.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current_stroke_ids.clear()
        self._current_erased_specs.clear()
        self._shape_preview_ids.clear()
        self.board_mode = "Şeffaf Ekran"
        self.curtain_active = False
        self.current_tool = "hand"
        self._linux_bg_photo = None
        if hasattr(self, "input_win") and self.input_win.winfo_exists():
            self.input_win.withdraw()
        if hasattr(self, "draw_win") and self.draw_win.winfo_exists():
            self.draw_win.withdraw()
        self._refresh_button_Highlights()

    def hide_pen_hud(self):
        self.reset_and_clear()
        self.withdraw()

    # =========================================================================
    # ARAÇ, RENK, KALINLIK, SİLGİ BOYUTU VE TAHTA SEÇİMLERİ
    # =========================================================================
    def select_tool(self, tool_id, play_sound=True):
        self._commit_active_text()
        self.current_tool = tool_id

        if tool_id in (*SHAPE_TOOLS, "marker") and hasattr(self, "tool_buttons") and "shapes" in self.tool_buttons:
            self.tool_buttons["shapes"].configure(image=self.icons.get(tool_id, self.icons["shapes"]))
        elif hasattr(self, "tool_buttons") and "shapes" in self.tool_buttons:
            self.tool_buttons["shapes"].configure(image=self.icons["shapes"])

        cur_spec = "arrow"
        if tool_id == "eraser":
            cur_spec = "none" if sys.platform == "win32" else "circle"
        elif tool_id == "text":
            cur_spec = "xterm"
        elif tool_id != "hand":
            cur_spec = "tcross"

        for target in (self.input_win, self.canvas):
            try:
                target.configure(cursor=cur_spec)
            except Exception:
                try:
                    target.configure(cursor="tcross")
                except Exception:
                    pass

        if tool_id != "eraser":
            self._clear_eraser_cursor()

        self._refresh_button_Highlights()
        self._sync_layer_visibility()
        if play_sound:
            self.sound.play_tick()

    def select_color(self, hex_color):
        self.current_color = hex_color
        self._refresh_color_dependent_icons()
        if self.current_tool in ("hand", "eraser"):
            self.current_tool = "pen"
            self._clear_eraser_cursor()
        self._refresh_button_Highlights()
        self._sync_layer_visibility()
        self.sound.play_tick()

    def pick_custom_color(self):
        was_input = self.input_win.state() != "withdrawn"
        if was_input:
            self.input_win.withdraw()
        color = colorchooser.askcolor(initialcolor=self.current_color, title="Akıllı Tahta Kalemi - Özel Renk Seç")[1]
        if color:
            self.select_color(color)
        else:
            self._sync_layer_visibility()

    def select_thickness(self, label):
        if label in THICKNESS_MAP:
            self.thickness_label = label
            self.current_width = THICKNESS_MAP[label]
            self._refresh_button_Highlights()
            self.sound.play_tick()

    def _on_eraser_slider_change(self, val):
        self.eraser_radius = max(8, min(90, int(round(float(val)))))
        if hasattr(self, "eraser_size_label") and self.eraser_size_label.winfo_exists():
            self.eraser_size_label.configure(text=f"{self.eraser_radius} px")
        try:
            self.dm.set_setting("pen_eraser_radius", self.eraser_radius)
        except Exception:
            pass

    def set_eraser_radius(self, radius_px: int):
        self.eraser_radius = max(8, min(90, int(radius_px)))
        if hasattr(self, "eraser_slider") and self.eraser_slider.winfo_exists():
            self.eraser_slider.set(self.eraser_radius)
        if hasattr(self, "eraser_size_label") and self.eraser_size_label.winfo_exists():
            self.eraser_size_label.configure(text=f"{self.eraser_radius} px")
        try:
            self.dm.set_setting("pen_eraser_radius", self.eraser_radius)
        except Exception:
            pass
        self.sound.play_tick()
        self.close_popover()

    def set_board_mode(self, mode):
        self.board_mode = mode
        self._redraw_board_background()
        if mode != "Şeffaf Ekran" and self.current_tool == "hand":
            self.select_tool("pen", play_sound=False)
            if mode in ("Yeşil Tahta", "Siyah Tahta"):
                self.select_color("#ffffff")
            elif mode in ("Beyaz Tahta", "Kareli Tahta", "Çizgili Tahta") and self.current_color == "#ffffff":
                self.select_color("#0f172a")
        self._sync_layer_visibility()
        self.sound.play_tick()

    def _redraw_board_background(self):
        self.canvas.delete("board_bg")
        if self.board_mode == "Şeffaf Ekran":
            self.canvas.configure(bg=TRANSPARENT_KEY)
            return

        # Tahta arka planı aktifken Linux ekran görüntüsü katmanını temizle ki tahtanın üstünü örtmesin
        self.canvas.delete("linux_screen_bg")
        self._linux_bg_photo = None

        sw = self._get_screen_width()
        sh = self.winfo_screenheight()
        scale = self._get_scaling()

        bg_map = {
            "Beyaz Tahta": "#f8fafc",
            "Yeşil Tahta": "#0f3822",
            "Siyah Tahta": "#0f172a",
            "Kareli Tahta": "#f8fafc",
            "Çizgili Tahta": "#fefce8",
        }
        bg_col = bg_map.get(self.board_mode, "#f8fafc")
        self.canvas.configure(bg=bg_col)
        self.canvas.create_rectangle(0, 0, sw, sh, fill=bg_col, outline=bg_col, tags=("board_bg",))

        if self.board_mode == "Kareli Tahta":
            step = max(20, int(round(32 * scale)))
            for x in range(0, sw, step):
                self.canvas.create_line(x, 0, x, sh, fill="#cbd5e1", width=1, tags=("board_bg",))
            for y in range(0, sh, step):
                self.canvas.create_line(0, y, sw, y, fill="#cbd5e1", width=1, tags=("board_bg",))
        elif self.board_mode == "Çizgili Tahta":
            step = max(24, int(round(36 * scale)))
            margin_x = int(round(90 * scale))
            self.canvas.create_line(margin_x, 0, margin_x, sh, fill="#fca5a5", width=2, tags=("board_bg",))
            for y in range(int(round(60 * scale)), sh, step):
                self.canvas.create_line(0, y, sw, y, fill="#93c5fd", width=1, tags=("board_bg",))

        if self.canvas.find_withtag("stroke"):
            self.canvas.tag_lower("board_bg", "stroke")
        if self.canvas.find_withtag("curtain_layer"):
            self.canvas.tag_raise("curtain_layer")

    def toggle_curtain(self):
        self.curtain_active = not self.curtain_active
        self._redraw_curtain()
        self._refresh_button_Highlights()
        self._sync_layer_visibility()
        self.sound.play_tick()

    def _redraw_curtain(self):
        self.canvas.delete("curtain_layer")
        if not self.curtain_active:
            return
        sw = self._get_screen_width()
        sh = self.winfo_screenheight()
        scale = self._get_scaling()
        cy = max(int(60 * scale), min(sh - int(40 * scale), self.curtain_y))
        self.canvas.create_rectangle(0, cy, sw, sh, fill="#0f172a", outline="#38bdf8", width=3, tags=("curtain_layer",))
        hw = int(round(48 * scale))
        hh = int(round(16 * scale))
        self.canvas.create_oval(
            sw // 2 - hw, cy - hh, sw // 2 + hw, cy + hh,
            fill="#0284c7", outline="#ffffff", width=2, tags=("curtain_layer",)
        )
        px_f = max(10, int(round(11 * scale * getattr(ctk.ScalingTracker, "font_size_correction", 1.0))))
        self.canvas.create_text(
            sw // 2, cy, text="PERDEYİ SÜRÜKLE", fill="#ffffff", font=("Segoe UI", -px_f, "bold"), tags=("curtain_layer",)
        )

    # =========================================================================
    # ÇİZİM, ŞEKİL, METİN, LAZER VE GERÇEK BÖLGESEL SİLGİ İŞLEMLERİ
    # =========================================================================
    def _is_point_on_hud(self, x_root, y_root):
        try:
            for win in (self, getattr(self, "popover", None)):
                if win and win.winfo_exists() and win.state() != "withdrawn":
                    wx, wy = win.winfo_rootx(), win.winfo_rooty()
                    ww, wh = win.winfo_width(), win.winfo_height()
                    if wx <= x_root <= wx + ww and wy <= y_root <= wy + wh:
                        return True
        except Exception:
            pass
        return False

    def _on_input_hover(self, event):
        if self.current_tool == "eraser":
            self._update_eraser_cursor(event.x, event.y)
        else:
            self._clear_eraser_cursor()

    def _update_eraser_cursor(self, x, y):
        r = self.eraser_radius
        if self._eraser_cursor_id is None:
            self._eraser_cursor_id = self.canvas.create_oval(
                x - r, y - r, x + r, y + r,
                outline="#ef4444", width=2, fill="", tags=("ui_helper",)
            )
        else:
            self.canvas.coords(self._eraser_cursor_id, x - r, y - r, x + r, y + r)
            self.canvas.tag_raise(self._eraser_cursor_id)

    def _clear_eraser_cursor(self):
        if self._eraser_cursor_id is not None:
            self.canvas.delete(self._eraser_cursor_id)
            self._eraser_cursor_id = None

    def _register_canvas_item(self, itype: str, coords: list, opts: dict) -> int:
        creators = {
            "line": self.canvas.create_line,
            "oval": self.canvas.create_oval,
            "rectangle": self.canvas.create_rectangle,
            "polygon": self.canvas.create_polygon,
            "text": self.canvas.create_text,
        }
        fn = creators[itype]
        clean_opts = {k: v for k, v in opts.items() if v != "" and v is not None}
        item_id = fn(*coords, tags=("stroke",), **clean_opts)
        self.item_specs[item_id] = (itype, list(coords), dict(clean_opts))
        return item_id

    def _add_subdivided_line(self, x1, y1, x2, y2, opts: dict, step_px: float = 9.0) -> list:
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        if dist <= step_px:
            return [self._register_canvas_item("line", [x1, y1, x2, y2], opts)]

        steps = max(1, int(math.ceil(dist / step_px)))
        created = []
        px, py = x1, y1
        for i in range(1, steps + 1):
            t = i / steps
            nx = x1 + dx * t
            ny = y1 + dy * t
            created.append(self._register_canvas_item("line", [px, py, nx, ny], opts))
            px, py = nx, ny
        return created

    def _on_input_down(self, event):
        if self._is_point_on_hud(event.x_root, event.y_root):
            self._ensure_topmost_lock()
            return

        # Ekrana dokunulduğu anda açık olan yan pencereyi otomatik kapat
        if self._active_popover_name:
            self.close_popover()

        if self.curtain_active and abs(event.y - self.curtain_y) <= 28:
            self._dragging_curtain = True
            return
        self._dragging_curtain = False

        if self.current_tool == "hand":
            return

        if self.current_tool == "text":
            self._spawn_text_input(event.x, event.y)
            return

        self._commit_active_text()
        self._start_x = event.x
        self._start_y = event.y
        self._last_x = event.x
        self._last_y = event.y
        self.current_stroke_ids = []
        self._current_erased_specs = []

        if self.current_tool == "eraser":
            self._update_eraser_cursor(event.x, event.y)
            self._erase_along(event.x, event.y, event.x, event.y)
            return

        if self.current_tool in ("pen", "highlighter", "marker"):
            w = self._effective_stroke_width()
            r = max(1.5, w / 2.0)
            opts = {"fill": self.current_color, "outline": self.current_color}
            if self.current_tool == "highlighter":
                opts["stipple"] = "gray50"
            dot_id = self._register_canvas_item("oval", [event.x - r, event.y - r, event.x + r, event.y + r], opts)
            self.current_stroke_ids.append(dot_id)

    def _on_input_drag(self, event):
        if getattr(self, "_dragging_curtain", False):
            self.curtain_y = event.y
            self._redraw_curtain()
            return

        if self.current_tool == "hand":
            return

        if self.current_tool == "eraser":
            self._update_eraser_cursor(event.x, event.y)
            lx = self._last_x if self._last_x is not None else event.x
            ly = self._last_y if self._last_y is not None else event.y
            self._erase_along(lx, ly, event.x, event.y)
            self._last_x, self._last_y = event.x, event.y
            return

        if self.current_tool == "laser":
            if self._last_x is not None and self._last_y is not None:
                glow = self.canvas.create_line(
                    self._last_x, self._last_y, event.x, event.y,
                    fill="#ef4444", width=6, capstyle="round", smooth=True, tags=("laser",)
                )
                core = self.canvas.create_line(
                    self._last_x, self._last_y, event.x, event.y,
                    fill="#fef08a", width=2, capstyle="round", smooth=True, tags=("laser",)
                )
                self.after(900, lambda g=glow, c=core: (self.canvas.delete(g), self.canvas.delete(c)))
            self._last_x, self._last_y = event.x, event.y
            return

        if self.current_tool in ("pen", "highlighter", "marker"):
            if self._last_x is not None and self._last_y is not None:
                if math.hypot(event.x - self._last_x, event.y - self._last_y) < 2.5:
                    return
                w = self._effective_stroke_width()
                cap = "projecting" if self.current_tool == "marker" else "round"
                opts = {
                    "fill": self.current_color,
                    "width": w,
                    "capstyle": cap,
                    "joinstyle": "round",
                }
                if self.current_tool == "highlighter":
                    opts["stipple"] = "gray50"
                new_ids = self._add_subdivided_line(self._last_x, self._last_y, event.x, event.y, opts, step_px=9.0)
                self.current_stroke_ids.extend(new_ids)
            self._last_x, self._last_y = event.x, event.y
            return

        if self.current_tool in ("line", "arrow", "rect", "oval", "triangle"):
            for pid in self._shape_preview_ids:
                self.canvas.delete(pid)
            self._shape_preview_ids = self._create_preview_shape(self._start_x, self._start_y, event.x, event.y)

    def _on_input_up(self, event):
        if getattr(self, "_dragging_curtain", False):
            self._dragging_curtain = False
            return

        if self.current_tool in ("line", "arrow", "rect", "oval", "triangle") and self._start_x is not None:
            for pid in self._shape_preview_ids:
                self.canvas.delete(pid)
            self._shape_preview_ids = []
            if math.hypot(event.x - self._start_x, event.y - self._start_y) >= 3:
                created_ids = self._commit_segmented_shape(self._start_x, self._start_y, event.x, event.y)
                self.current_stroke_ids.extend(created_ids)

        if self.current_stroke_ids:
            specs = [self.item_specs[iid] for iid in self.current_stroke_ids if iid in self.item_specs]
            if specs:
                self.undo_stack.append(("draw", specs))
                self.redo_stack.clear()
            self.current_stroke_ids = []
            if self.curtain_active:
                self.canvas.tag_raise("curtain_layer")

        if self._current_erased_specs:
            self.undo_stack.append(("erase", list(self._current_erased_specs)))
            self.redo_stack.clear()
            self._current_erased_specs = []
            self._sync_layer_visibility()

        self._start_x = None
        self._start_y = None
        self._last_x = None
        self._last_y = None
        self._ensure_topmost_lock()

    def _effective_stroke_width(self):
        if self.current_tool == "highlighter":
            return self.current_width * 3.2
        if self.current_tool == "marker":
            return self.current_width * 1.8
        return self.current_width

    def _create_preview_shape(self, x1, y1, x2, y2) -> list:
        w = self.current_width
        col = self.current_color
        if self.current_tool == "line":
            return [self.canvas.create_line(x1, y1, x2, y2, fill=col, width=w, capstyle="round", tags=("preview",))]
        if self.current_tool == "arrow":
            return [self.canvas.create_line(
                x1, y1, x2, y2, fill=col, width=w, capstyle="round",
                arrow=tk.LAST, arrowshape=(14, 16, 6), tags=("preview",),
            )]
        if self.current_tool == "rect":
            return [self.canvas.create_rectangle(x1, y1, x2, y2, outline=col, width=w, tags=("preview",))]
        if self.current_tool == "oval":
            return [self.canvas.create_oval(x1, y1, x2, y2, outline=col, width=w, tags=("preview",))]
        if self.current_tool == "triangle":
            mx = (x1 + x2) / 2.0
            return [self.canvas.create_polygon(
                mx, y1, x1, y2, x2, y2, fill="", outline=col, width=w, joinstyle="round", tags=("preview",),
            )]
        return []

    def _commit_segmented_shape(self, x1, y1, x2, y2) -> list:
        w = self.current_width
        col = self.current_color
        opts = {"fill": col, "width": w, "capstyle": "round", "joinstyle": "round"}
        ids = []

        if self.current_tool == "line":
            ids.extend(self._add_subdivided_line(x1, y1, x2, y2, opts))
        elif self.current_tool == "arrow":
            ids.extend(self._add_subdivided_line(x1, y1, x2, y2, opts))
            angle = math.atan2(y2 - y1, x2 - x1)
            head_len = max(14.0, w * 2.6)
            for delta in (2.6, -2.6):
                hx = x2 + head_len * math.cos(angle + delta)
                hy = y2 + head_len * math.sin(angle + delta)
                ids.extend(self._add_subdivided_line(x2, y2, hx, hy, opts))
        elif self.current_tool == "rect":
            ids.extend(self._add_subdivided_line(x1, y1, x2, y1, opts))
            ids.extend(self._add_subdivided_line(x2, y1, x2, y2, opts))
            ids.extend(self._add_subdivided_line(x2, y2, x1, y2, opts))
            ids.extend(self._add_subdivided_line(x1, y2, x1, y1, opts))
        elif self.current_tool == "triangle":
            mx = (x1 + x2) / 2.0
            ids.extend(self._add_subdivided_line(mx, y1, x1, y2, opts))
            ids.extend(self._add_subdivided_line(x1, y2, x2, y2, opts))
            ids.extend(self._add_subdivided_line(x2, y2, mx, y1, opts))
        elif self.current_tool == "oval":
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            rx = abs(x2 - x1) / 2.0
            ry = abs(y2 - y1) / 2.0
            circum = math.pi * (1.5 * (rx + ry) - math.sqrt(max(0.0, rx * ry)))
            steps = max(36, int(circum / 4.5))
            pts = [
                (cx + rx * math.cos(2.0 * math.pi * i / steps), cy + ry * math.sin(2.0 * math.pi * i / steps))
                for i in range(steps + 1)
            ]
            for i in range(steps):
                ids.append(
                    self._register_canvas_item("line", [pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]], opts)
                )
        return ids

    def _spawn_text_input(self, x, y):
        self._commit_active_text()
        scale = self._get_scaling()
        font_sz = max(16, int(round(self.current_width * 4.2 * scale)))
        target_win = self.draw_win if sys.platform != "win32" else self.input_win
        entry = tk.Entry(
            target_win,
            font=("Segoe UI", -font_sz, "bold"),
            fg=self.current_color if self.current_color != "#ffffff" else "#0f172a",
            bg="#ffffff",
            insertbackground="#0284c7",
            relief="solid",
            bd=2,
            width=24,
        )
        entry.place(x=x, y=y)
        entry.focus_set()
        self._active_text_entry = (entry, x, y, font_sz)
        entry.bind("<Return>", lambda _e: self._commit_active_text())
        entry.bind("<Escape>", lambda _e: self._cancel_active_text())

    def _commit_active_text(self):
        if not self._active_text_entry:
            return
        entry, x, y, font_sz = self._active_text_entry
        self._active_text_entry = None
        try:
            txt = entry.get().strip()
            entry.destroy()
            if txt:
                opts = {
                    "text": txt,
                    "fill": self.current_color,
                    "anchor": "nw",
                    "font": ("Segoe UI", -font_sz, "bold"),
                }
                item_id = self._register_canvas_item("text", [x, y], opts)
                self.undo_stack.append(("draw", [self.item_specs[item_id]]))
                self.redo_stack.clear()
        except Exception:
            pass

    def _cancel_active_text(self):
        if not self._active_text_entry:
            return
        entry, *_ = self._active_text_entry
        self._active_text_entry = None
        try:
            entry.destroy()
        except Exception:
            pass

    @staticmethod
    def _point_to_segment_dist(px, py, x1, y1, x2, y2) -> float:
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1)
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

    def _erase_along(self, x1, y1, x2, y2):
        r = float(self.eraser_radius)
        dist = math.hypot(x2 - x1, y2 - y1)
        steps = max(1, int(math.ceil(dist / max(3.0, r * 0.35))))
        for i in range(steps + 1):
            t = i / steps
            cx = x1 + (x2 - x1) * t
            cy = y1 + (y2 - y1) * t
            self._erase_circle_at(cx, cy, r)

    def _erase_circle_at(self, cx: float, cy: float, r: float):
        candidates = self.canvas.find_overlapping(cx - r, cy - r, cx + r, cy + r)
        for item_id in candidates:
            if item_id not in self.item_specs:
                continue
            itype, coords, opts = self.item_specs[item_id]
            hit = False
            if itype == "line" and len(coords) >= 4:
                d = self._point_to_segment_dist(cx, cy, coords[0], coords[1], coords[2], coords[3])
                stroke_half = float(opts.get("width", 2.0)) * 0.5
                hit = d <= (r + stroke_half)
            elif itype == "oval" and len(coords) >= 4:
                ox = (coords[0] + coords[2]) * 0.5
                oy = (coords[1] + coords[3]) * 0.5
                orad = abs(coords[2] - coords[0]) * 0.5
                hit = math.hypot(cx - ox, cy - oy) <= (r + orad)
            else:
                bbox = self.canvas.bbox(item_id)
                if bbox:
                    bx = max(bbox[0], min(cx, bbox[2]))
                    by = max(bbox[1], min(cy, bbox[3]))
                    hit = math.hypot(cx - bx, cy - by) <= r

            if hit:
                self._current_erased_specs.append((itype, coords, opts))
                del self.item_specs[item_id]
                self.canvas.delete(item_id)

    # =========================================================================
    # GERİ AL / İLERİ AL / TEMİZLE / EKRAN GÖRÜNTÜSÜ
    # =========================================================================
    def _delete_matching_specs(self, target_specs: list):
        target_set = {(itype, tuple(coords)) for itype, coords, _ in target_specs}
        to_remove = [
            iid for iid, (itype, coords, _) in self.item_specs.items()
            if (itype, tuple(coords)) in target_set
        ]
        for iid in to_remove:
            del self.item_specs[iid]
            self.canvas.delete(iid)

    def _restore_specs(self, specs: list):
        for itype, coords, opts in specs:
            self._register_canvas_item(itype, coords, opts)
        if self.curtain_active:
            self.canvas.tag_raise("curtain_layer")

    def undo_last(self):
        self._commit_active_text()
        if not self.undo_stack:
            return
        action, specs = self.undo_stack.pop()
        if action == "draw":
            self._delete_matching_specs(specs)
        elif action == "erase":
            self._restore_specs(specs)
        self.redo_stack.append((action, specs))
        self.sound.play_tick()
        self._sync_layer_visibility()

    def redo_last(self):
        if not self.redo_stack:
            return
        action, specs = self.redo_stack.pop()
        if action == "draw":
            self._restore_specs(specs)
        elif action == "erase":
            self._delete_matching_specs(specs)
        self.undo_stack.append((action, specs))
        self.sound.play_tick()
        self._sync_layer_visibility()

    def clear_all(self):
        self._commit_active_text()
        self.close_popover()
        if self.item_specs:
            all_specs = list(self.item_specs.values())
            self.undo_stack.append(("erase", all_specs))
            self.redo_stack.clear()
        self.canvas.delete("stroke")
        self.canvas.delete("laser")
        self.item_specs.clear()
        self.current_stroke_ids.clear()
        self.sound.play_tick()
        self._sync_layer_visibility()

    def _capture_screen_png_bytes(self) -> bytes:
        try:
            import io
            from PIL import ImageGrab
            img = ImageGrab.grab()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except Exception:
            pass

        if sys.platform.startswith("win"):
            import struct
            import zlib
            from ctypes import wintypes

            u32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
            w = u32.GetSystemMetrics(0)
            h = u32.GetSystemMetrics(1)

            hdc_screen = u32.GetDC(0)
            hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
            hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
            old_obj = gdi32.SelectObject(hdc_mem, hbmp)
            gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, 0, 0, 0x00CC0020)

            class BITMAPINFOHEADER(ctypes.Structure):
                _fields_ = [
                    ("biSize", wintypes.DWORD),
                    ("biWidth", wintypes.LONG),
                    ("biHeight", wintypes.LONG),
                    ("biPlanes", wintypes.WORD),
                    ("biBitCount", wintypes.WORD),
                    ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD),
                    ("biXPelsPerMeter", wintypes.LONG),
                    ("biYPelsPerMeter", wintypes.LONG),
                    ("biClrUsed", wintypes.DWORD),
                    ("biClrImportant", wintypes.DWORD),
                ]

            bmi = BITMAPINFOHEADER()
            bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.biWidth = w
            bmi.biHeight = -h
            bmi.biPlanes = 1
            bmi.biBitCount = 32
            bmi.biCompression = 0

            buf_len = w * h * 4
            raw = ctypes.create_string_buffer(buf_len)
            gdi32.GetDIBits(hdc_mem, hbmp, 0, h, raw, ctypes.byref(bmi), 0)

            gdi32.SelectObject(hdc_mem, old_obj)
            gdi32.DeleteObject(hbmp)
            gdi32.DeleteDC(hdc_mem)
            u32.ReleaseDC(0, hdc_screen)

            bgra = raw.raw
            rows = []
            stride = w * 4
            for y in range(h):
                row_bgra = bgra[y * stride : (y + 1) * stride]
                row_rgb = bytearray(w * 3 + 1)
                row_rgb[0] = 0
                row_rgb[1::3] = row_bgra[2::4]
                row_rgb[2::3] = row_bgra[1::4]
                row_rgb[3::3] = row_bgra[0::4]
                rows.append(bytes(row_rgb))

            def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
                crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
                return struct.pack("!I", len(data)) + chunk_type + data + struct.pack("!I", crc)

            ihdr = struct.pack("!IIBBBBB", w, h, 8, 2, 0, 0, 0)
            idat = zlib.compress(b"".join(rows), 6)
            return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", idat) + png_chunk(b"IEND", b"")

        raise RuntimeError("Ekran yakalama modülü bulunamadı.")

    def save_screenshot(self):
        try:
            self.close_popover()
            self.withdraw()
            self.update_idletasks()
            png_bytes = self._capture_screen_png_bytes()
            self.deiconify()
            self._ensure_topmost_lock()

            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            default_name = f"Novaboard_Tahta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            save_path = filedialog.asksaveasfilename(
                parent=self,
                title="Tahta Ekran Görüntüsünü Kaydet",
                initialdir=desktop if os.path.exists(desktop) else os.path.expanduser("~"),
                initialfile=default_name,
                defaultextension=".png",
                filetypes=[("PNG Görseli", "*.png")],
            )
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(png_bytes)
                messagebox.showinfo("Kaydedildi", f"Ekran görüntüsü kaydedildi:\n{save_path}", parent=self)
        except Exception as e:
            self.deiconify()
            messagebox.showwarning("Uyarı", f"Ekran görüntüsü alınamadı: {e}", parent=self)

    # =========================================================================
    # TEMA VE VURGU GÜNCELLEMESİ
    # =========================================================================
    def _refresh_button_Highlights(self):
        t = self.tm.get_theme()
        shape_selected = self.current_tool in (*SHAPE_TOOLS, "marker")

        for tid, btn in getattr(self, "tool_buttons", {}).items():
            is_sel = (tid == self.current_tool) or (tid == "shapes" and shape_selected)
            btn.configure(
                fg_color=t["accent"] if is_sel else t["bg_card_inner"],
                hover_color=t["accent_hover"] if is_sel else t["bg_hover"],
                border_color=t["accent"] if is_sel else t["border"],
            )

        if hasattr(self, "palette_btn"):
            is_pal = self._active_popover_name == "palette"
            self.palette_btn.configure(
                fg_color=t["accent"] if is_pal else t["bg_card_inner"],
                border_color=t["accent"] if is_pal else t["border"],
            )

        if hasattr(self, "board_btn"):
            is_brd = self._active_popover_name == "board" or self.board_mode != "Şeffaf Ekran" or self.curtain_active
            self.board_btn.configure(
                fg_color=t["accent"] if is_brd else t["bg_card_inner"],
                border_color=t["accent"] if is_brd else t["border"],
            )

        for lbl, btn in getattr(self, "width_buttons", {}).items():
            if btn.winfo_exists():
                is_sel = lbl == self.thickness_label
                btn.configure(
                    fg_color=t["accent"] if is_sel else t["bg_card_inner"],
                    hover_color=t["accent_hover"] if is_sel else t["bg_hover"],
                    text_color=t["accent_text"] if is_sel else t["text_primary"],
                    border_color=t["accent"] if is_sel else t["border"],
                )

    def apply_theme(self):
        try:
            super().apply_theme()
            self._refresh_button_Highlights()
        except Exception:
            pass

    def destroy(self):
        try:
            self.reset_and_clear()
        except Exception:
            pass
        try:
            self.tm.unregister_callback(self.apply_theme)
        except Exception:
            pass
        for win in (
            getattr(self, "draw_win", None),
            getattr(self, "input_win", None),
            getattr(self, "popover", None),
            getattr(self, "tooltip_win", None),
        ):
            try:
                if win and win.winfo_exists():
                    win.destroy()
            except Exception:
                pass
        super().destroy()
