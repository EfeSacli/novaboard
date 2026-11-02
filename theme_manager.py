import customtkinter as ctk

# Novaboard - Merkezi Renk ve Tema Yönetim Sistemi
# Akıllı tahta, projeksiyon ve masaüstü sistemleri için yüksek kontrastlı ve kurumsal temalar

THEMES = {
    "dark": {
        "id": "dark",
        "name": "Koyu Tema (Klasik)",
        "appearance_mode": "Dark",
        "bg_main": "#111827",          # Slate 900
        "bg_sidebar": "#1f2937",       # Slate 800
        "bg_card": "#1f2937",          # Slate 800
        "bg_card_inner": "#111827",    # Slate 900
        "bg_hover": "#374151",         # Slate 700
        "border": "#374151",           # Slate 700
        "text_primary": "#f9fafb",     # Slate 50
        "text_secondary": "#9ca3af",   # Slate 400
        "text_muted": "#6b7280",       # Slate 500
        "accent": "#0284c7",           # Sky 600
        "accent_hover": "#0369a1",     # Sky 700
        "accent_text": "#ffffff",
        "input_bg": "#111827",
        "input_border": "#374151",
        "input_text": "#f9fafb",
        "success": "#16a34a",          # Green 600
        "success_hover": "#15803d",
        "success_bg": "#14532d",
        "success_text": "#86efac",
        "danger": "#dc2626",           # Red 600
        "danger_hover": "#b91c1c",
        "danger_bg": "#450a0a",
        "danger_text": "#fca5a5",
        "badge_remaining_bg": "#14532d",
        "badge_remaining_text": "#86efac",
        "badge_picked_bg": "#374151",
        "badge_picked_text": "#9ca3af",
        "badge_exempt_bg": "#451a03",
        "badge_exempt_text": "#fde68a",
    },
    "light": {
        "id": "light",
        "name": "Açık Tema (Kurumsal Beyaz)",
        "appearance_mode": "Light",
        "bg_main": "#f8fafc",          # Slate 50
        "bg_sidebar": "#ffffff",       # Beyaz
        "bg_card": "#ffffff",          # Beyaz kartlar
        "bg_card_inner": "#f1f5f9",    # Slate 100
        "bg_hover": "#e2e8f0",         # Slate 200
        "border": "#cbd5e1",           # Slate 300
        "text_primary": "#0f172a",     # Slate 900 (Yüksek kontrastlı siyah)
        "text_secondary": "#475569",   # Slate 600
        "text_muted": "#64748b",       # Slate 500
        "accent": "#0284c7",           # Sky 600
        "accent_hover": "#0369a1",     # Sky 700
        "accent_text": "#ffffff",
        "input_bg": "#ffffff",
        "input_border": "#cbd5e1",
        "input_text": "#0f172a",
        "success": "#16a34a",
        "success_hover": "#15803d",
        "success_bg": "#dcfce7",
        "success_text": "#15803d",
        "danger": "#dc2626",
        "danger_hover": "#b91c1c",
        "danger_bg": "#fee2e2",
        "danger_text": "#b91c1c",
        "badge_remaining_bg": "#dcfce7",
        "badge_remaining_text": "#15803d",
        "badge_picked_bg": "#e2e8f0",
        "badge_picked_text": "#475569",
        "badge_exempt_bg": "#fef3c7",
        "badge_exempt_text": "#b45309",
    },
    "chalkboard": {
        "id": "chalkboard",
        "name": "Yeşil Tahta (MEB Akıllı Tahta)",
        "appearance_mode": "Dark",
        "bg_main": "#0a1c14",          # Koyu yeşil zemin
        "bg_sidebar": "#112e21",       # Tahta koyusu
        "bg_card": "#133527",          # Tahta yeşili
        "bg_card_inner": "#0d241a",
        "bg_hover": "#1d4734",
        "border": "#21543e",
        "text_primary": "#f0fdf4",     # Tebeşir beyazı
        "text_secondary": "#86efac",   # Açık tebeşir yeşili
        "text_muted": "#4ade80",
        "accent": "#22c55e",           # Parlak yeşil
        "accent_hover": "#16a34a",
        "accent_text": "#052e16",
        "input_bg": "#0d241a",
        "input_border": "#21543e",
        "input_text": "#f0fdf4",
        "success": "#16a34a",
        "success_hover": "#15803d",
        "success_bg": "#052e16",
        "success_text": "#86efac",
        "danger": "#dc2626",
        "danger_hover": "#b91c1c",
        "danger_bg": "#450a0a",
        "danger_text": "#fca5a5",
        "badge_remaining_bg": "#052e16",
        "badge_remaining_text": "#86efac",
        "badge_picked_bg": "#1d4734",
        "badge_picked_text": "#a7f3d0",
        "badge_exempt_bg": "#3f2c05",
        "badge_exempt_text": "#fde047",
    },
    "midnight": {
        "id": "midnight",
        "name": "Gece Mavisi (Derin Mavi)",
        "appearance_mode": "Dark",
        "bg_main": "#091224",
        "bg_sidebar": "#0f1c36",
        "bg_card": "#142548",
        "bg_card_inner": "#0c172d",
        "bg_hover": "#1d3567",
        "border": "#223c72",
        "text_primary": "#f8fafc",
        "text_secondary": "#93c5fd",
        "text_muted": "#60a5fa",
        "accent": "#38bdf8",
        "accent_hover": "#0284c7",
        "accent_text": "#082f49",
        "input_bg": "#0c172d",
        "input_border": "#223c72",
        "input_text": "#f8fafc",
        "success": "#10b981",
        "success_hover": "#059669",
        "success_bg": "#064e3b",
        "success_text": "#6ee7b7",
        "danger": "#f43f5e",
        "danger_hover": "#e11d48",
        "danger_bg": "#4c0519",
        "danger_text": "#fda4af",
        "badge_remaining_bg": "#064e3b",
        "badge_remaining_text": "#6ee7b7",
        "badge_picked_bg": "#1d3567",
        "badge_picked_text": "#bfdbfe",
        "badge_exempt_bg": "#451a03",
        "badge_exempt_text": "#fed7aa",
    },
}


class ThemeManager:
    """
    Novaboard - Merkezi Tema ve Görünüm Motoru.
    Pencerelerin ve bileşenlerin renklerini tek bir kaynaktan yönetir.
    """

    def __init__(self, data_manager):
        self.dm = data_manager
        self.callbacks = []
        self._current_theme_id = self.dm.get_setting("theme", "dark")
        if self._current_theme_id not in THEMES:
            self._current_theme_id = "dark"
        self._custom_bg = self.dm.get_setting("custom_bg", "")
        self._custom_accent = self.dm.get_setting("custom_accent", "")

    def register_callback(self, callback):
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def unregister_callback(self, callback):
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    @property
    def current_theme_id(self):
        return self._current_theme_id

    def get_current_theme_id(self):
        return self._current_theme_id

    def get_theme(self):
        base = THEMES.get(self._current_theme_id, THEMES["dark"]).copy()

        if self._custom_bg:
            bg = self._custom_bg
            is_light = self._is_light(bg)
            base["appearance_mode"] = "Light" if is_light else "Dark"
            base["bg_main"] = bg
            if is_light:
                base.update({
                    "bg_sidebar": self._adjust_brightness(bg, 0.95),
                    "bg_card": "#ffffff",
                    "bg_card_inner": self._adjust_brightness(bg, 0.92),
                    "border": "#cbd5e1",
                    "bg_hover": "#e2e8f0",
                    "text_primary": "#0f172a",
                    "text_secondary": "#475569",
                    "text_muted": "#64748b",
                    "input_bg": "#ffffff",
                    "input_border": "#cbd5e1",
                    "input_text": "#0f172a",
                })
            else:
                inner = self._adjust_brightness(bg, 0.85)
                border = self._adjust_brightness(bg, 1.40)
                base.update({
                    "bg_sidebar": self._adjust_brightness(bg, 1.15),
                    "bg_card": self._adjust_brightness(bg, 1.25),
                    "bg_card_inner": inner,
                    "border": border,
                    "bg_hover": self._adjust_brightness(bg, 1.35),
                    "text_primary": "#f9fafb",
                    "text_secondary": "#9ca3af",
                    "text_muted": "#6b7280",
                    "input_bg": inner,
                    "input_border": border,
                    "input_text": "#f9fafb",
                })

        if self._custom_accent:
            is_light = self._is_light(self._custom_accent)
            base["accent"] = self._custom_accent
            base["accent_hover"] = self._adjust_brightness(self._custom_accent, 0.85 if is_light else 1.15)
            base["accent_text"] = "#0f172a" if is_light else "#ffffff"

        return base

    def set_theme(self, theme_id):
        if theme_id not in THEMES:
            return
        self._current_theme_id = theme_id
        self.dm.set_setting("theme", theme_id)
        self._clear_custom_colors()
        self._apply_and_notify()

    def set_custom_colors(self, bg_hex=None, accent_hex=None):
        if bg_hex is not None:
            self._custom_bg = bg_hex
            self.dm.set_setting("custom_bg", bg_hex)
        if accent_hex is not None:
            self._custom_accent = accent_hex
            self.dm.set_setting("custom_accent", accent_hex)
        self._apply_and_notify()

    def reset_custom_colors(self):
        self._clear_custom_colors()
        self._apply_and_notify()

    def _clear_custom_colors(self):
        self._custom_bg = ""
        self._custom_accent = ""
        self.dm.set_setting("custom_bg", "")
        self.dm.set_setting("custom_accent", "")

    def _apply_and_notify(self):
        ctk.set_appearance_mode(self.get_theme()["appearance_mode"])
        for cb in list(self.callbacks):
            try:
                cb()
            except Exception:
                pass

    @staticmethod
    def _parse_rgb(hex_color):
        h = hex_color.lstrip("#")
        if len(h) != 6:
            return None
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def _is_light(self, hex_color):
        try:
            rgb = self._parse_rgb(hex_color)
            return bool(rgb and (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000 > 135)
        except Exception:
            return False

    def _adjust_brightness(self, hex_color, factor):
        try:
            rgb = self._parse_rgb(hex_color)
            if rgb:
                r, g, b = (min(255, max(0, int(c * factor))) for c in rgb)
                return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            pass
        return hex_color
