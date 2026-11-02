"""
Novaboard - Ortak arayüz yardımcıları.

Tüm pencerelerde tekrar eden üç şeyi tek yerde toplar:
  * font()       : "Segoe UI" tabanlı CTkFont kısayolu (app.py yazı tipi seçimini buna uygular)
  * Stil şablonları (BTN_*, CARD, ...) : widget özelliği -> tema anahtarı eşlemesi
  * ThemedMixin  : Widget'ları bir stil şablonuyla kaydeder; tema değişince hepsini yeniden boyar

Stil şablonu örneği:  {"fg_color": "accent", "text_color": "#ffffff"}
  - Değer bir tema anahtarıysa (theme_manager.THEMES içindeki) o temanın rengi kullanılır.
  - Değer "#" ile başlıyorsa veya "transparent" ise olduğu gibi kullanılır.
"""
import os
import sys
import tkinter as tk

import customtkinter as ctk


def get_resource_path(relative_path):
    """Kaynak dosyanın (simge vb.) yolunu bulur; hem kaynak koddan hem PyInstaller paketinden çalışır."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    for candidate in (os.path.join(base_path, relative_path), os.path.join(os.getcwd(), relative_path)):
        if os.path.exists(candidate):
            return candidate
    return relative_path


def font(size, bold=False, family="Segoe UI", **kwargs):
    return ctk.CTkFont(family=family, size=size, weight="bold" if bold else "normal", **kwargs)


# --- Stil şablonları ---------------------------------------------------------
BTN_ACCENT = {"fg_color": "accent", "hover_color": "accent_hover", "text_color": "accent_text"}
BTN_SUCCESS = {"fg_color": "success", "hover_color": "success_hover", "text_color": "#ffffff"}
BTN_DANGER = {"fg_color": "danger", "hover_color": "danger_hover", "text_color": "#ffffff"}
BTN_DANGER_SOFT = {"fg_color": "danger_bg", "hover_color": "danger_hover", "text_color": "danger_text"}
BTN_CARD = {"fg_color": "bg_card", "hover_color": "bg_hover", "text_color": "text_primary", "border_color": "border"}
BTN_INNER = {"fg_color": "bg_card_inner", "hover_color": "bg_hover", "text_color": "text_primary", "border_color": "border"}

CARD = {"fg_color": "bg_card", "border_color": "border"}
CARD_INNER = {"fg_color": "bg_card_inner", "border_color": "border"}

ENTRY = {"fg_color": "input_bg", "border_color": "input_border", "text_color": "input_text",
         "placeholder_text_color": "text_muted"}
TEXTBOX = {"fg_color": "input_bg", "border_color": "input_border", "text_color": "input_text"}

OPTION_MENU = {"fg_color": "bg_card", "text_color": "text_primary", "button_color": "bg_hover",
               "dropdown_fg_color": "bg_card", "dropdown_text_color": "text_primary",
               "dropdown_hover_color": "bg_hover"}
OPTION_MENU_INNER = {"fg_color": "bg_card_inner", "button_color": "bg_hover", "button_hover_color": "accent",
                     "text_color": "text_primary"}

SEGMENTED = {"fg_color": "bg_card", "selected_color": "accent", "selected_hover_color": "accent_hover",
             "unselected_color": "bg_card_inner", "unselected_hover_color": "bg_hover", "text_color": "text_primary"}

TEXT_PRIMARY = {"text_color": "text_primary"}
TEXT_SECONDARY = {"text_color": "text_secondary"}
TEXT_ACCENT = {"text_color": "accent"}


def resolve(style, theme):
    """Stil şablonunu, verilen temaya göre gerçek configure() argümanlarına çevirir."""
    return {prop: theme.get(value, value) for prop, value in style.items()}


class ThemedMixin:
    """
    Tema değişimini otomatik yöneten karışım sınıfı.
    Kullanım: __init__ içinde self.tm atandıktan sonra widget'ları self.styled(widget, STİL) ile kaydedin
    ve self.tm.register_callback(self.apply_theme) çağırın. Duruma bağlı renkler için apply_theme'i
    genişletip super().apply_theme() çağırın.
    """

    def styled(self, widget, *styles, **extra):
        style = {}
        for s in styles:
            style.update(s)
        style.update(extra)
        if not hasattr(self, "_styled_widgets"):
            self._styled_widgets = []
        self._styled_widgets.append((widget, style))
        widget.configure(**resolve(style, self.tm.get_theme()))
        return widget

    def apply_theme(self):
        t = self.tm.get_theme()
        alive = []
        for widget, style in getattr(self, "_styled_widgets", []):
            if widget.winfo_exists():
                widget.configure(**resolve(style, t))
                alive.append((widget, style))
        self._styled_widgets = alive


def set_window_icon(window, default=False):
    """Pencereye Novaboard simgesini uygular (Windows: .ico, tüm sistemler: .png)."""
    try:
        icon_ico = get_resource_path("icon.ico")
        icon_png = get_resource_path("icon.png")
        if sys.platform == "win32" and os.path.exists(icon_ico):
            try:
                if default:
                    window.iconbitmap(default=icon_ico)
                else:
                    window.iconbitmap(icon_ico)
            except Exception:
                pass
        if os.path.exists(icon_png):
            try:
                window._icon_img = tk.PhotoImage(file=icon_png)
                window.iconphoto(default, window._icon_img)
            except Exception:
                from PIL import ImageTk, Image
                window._icon_img = ImageTk.PhotoImage(Image.open(icon_png))
                window.iconphoto(default, window._icon_img)
    except Exception:
        pass


def center_window(window, width, height):
    sw, sh = window.winfo_screenwidth(), window.winfo_screenheight()
    window.geometry(f"{width}x{height}+{(sw - width) // 2}+{(sh - height) // 2}")


def paste_into_widget(widget):
    """Panodaki metni CTkTextbox veya CTkEntry içine imleç konumundan yapıştırır."""
    inner = getattr(widget, "_textbox", getattr(widget, "_entry", widget))
    is_text = isinstance(inner, tk.Text)
    try:
        clip = inner.clipboard_get()
    except Exception:
        return "break"
    if not clip:
        return "break"

    inner.focus_set()
    if hasattr(widget, "_entry_focus_in"):
        try:
            widget._entry_focus_in()
        except Exception:
            pass
    try:
        if is_text:
            if inner.tag_ranges("sel"):
                inner.delete("sel.first", "sel.last")
            inner.insert("insert", clip)
            inner.see("insert")
        else:
            if inner.selection_present():
                inner.delete("sel.first", "sel.last")
            inner.insert("insert", clip)
    except Exception:
        pass
    return "break"


def attach_context_menu(widget, theme_manager=None):
    """CTkTextbox ve CTkEntry bileşenlerine sağ tık (Yapıştır / Kopyala / Kes / Tümünü Seç / Temizle) menüsü ekler."""
    inner = getattr(widget, "_textbox", getattr(widget, "_entry", widget))
    is_text = isinstance(inner, tk.Text)

    def _copy():
        try:
            sel = inner.get("sel.first", "sel.last") if (is_text and inner.tag_ranges("sel")) or (not is_text and inner.selection_present()) else ""
            if sel:
                inner.clipboard_clear()
                inner.clipboard_append(sel)
        except Exception:
            pass

    def _cut():
        _copy()
        try:
            if (is_text and inner.tag_ranges("sel")) or (not is_text and inner.selection_present()):
                inner.delete("sel.first", "sel.last")
        except Exception:
            pass

    def _select_all():
        inner.focus_set()
        if is_text:
            inner.tag_add("sel", "1.0", "end-1c")
        else:
            inner.select_range(0, "end")

    def _clear_all():
        inner.focus_set()
        if is_text:
            inner.delete("1.0", "end")
        else:
            inner.delete(0, "end")

    def _show_menu(event):
        inner.focus_set()
        if hasattr(widget, "_entry_focus_in"):
            try:
                widget._entry_focus_in()
            except Exception:
                pass
        t = theme_manager.get_theme() if theme_manager else {}
        bg = t.get("bg_card", "#1f2937")
        fg = t.get("text_primary", "#f9fafb")
        abg = t.get("accent", "#0284c7")
        afg = t.get("accent_text", "#ffffff")

        menu = tk.Menu(
            inner, tearoff=0, bg=bg, fg=fg, activebackground=abg, activeforeground=afg,
            font=("Segoe UI", 10), relief="flat", bd=1,
        )
        menu.add_command(label="📋  Yapıştır", command=lambda: paste_into_widget(widget))
        menu.add_command(label="📄  Kopyala", command=_copy)
        menu.add_command(label="✂️  Kes", command=_cut)
        menu.add_separator()
        menu.add_command(label="☑️  Tümünü Seç", command=_select_all)
        menu.add_command(label="🗑️  Temizle", command=_clear_all)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    for seq in ("<Button-3>", "<Button-2>"):
        inner.bind(seq, _show_menu, add=True)
    for seq in ("<Control-v>", "<Control-V>", "<Shift-Insert>"):
        inner.bind(seq, lambda _e: paste_into_widget(widget))
    for seq in ("<Control-a>", "<Control-A>"):
        inner.bind(seq, lambda _e: (_select_all(), "break")[1])
    return widget
