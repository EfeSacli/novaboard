import sys
import ctypes
import customtkinter as ctk

APP_ID = "novaboard.smartboard.assistant.v1.0"

# Windows görev çubuğu kimliği ve yüksek DPI ölçekleme
if sys.platform == "win32":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from data_manager import DataManager
from sound_effects import SoundPlayer
from theme_manager import ThemeManager
from main_window import MainWindow
from drawer_hud import DrawerHUD
from screen_pen import ScreenPenHUD

SCALE_MAP = {
    "Standart": 1.0,
    "Büyük (Akıllı Tahta)": 1.10,
    "Çok Büyük": 1.20,
}


class NovaboardApp:
    """
    Novaboard - Akıllı Tahta & Öğretmen Asistanı
    Ana Uygulama Denetleyicisi: MainWindow, DrawerHUD (Kayan Çekmece),
    SoundPlayer ve ThemeManager koordinasyonu.
    """

    def __init__(self):
        self.dm = DataManager()
        self.sound = SoundPlayer(self.dm)
        self.theme_mgr = ThemeManager(self.dm)

        # 1. Yazı tipi ailesini global olarak uygula (Linux/Pardus'ta Segoe UI yerine sistem/Roboto kullan)
        font_family = self.dm.get_setting("font_family", "Segoe UI")
        if sys.platform != "win32" and font_family == "Segoe UI":
            font_family = None
        if font_family:
            orig_font_init = ctk.CTkFont.__init__

            def _custom_font_init(font_self, family=None, *args, **kwargs):
                if family is None or family == "Segoe UI":
                    family = font_family
                return orig_font_init(font_self, family=family, *args, **kwargs)

            ctk.CTkFont.__init__ = _custom_font_init

        # 2. Arayüz ölçeğini ve temayı uygula (pencere ve bileşen ölçeği senkronize)
        scale_choice = self.dm.get_setting("font_size_scale", "Standart")
        user_scale = SCALE_MAP.get(scale_choice, 1.0)
        ctk.set_widget_scaling(user_scale)
        ctk.set_window_scaling(user_scale)
        ctk.set_appearance_mode(self.theme_mgr.get_theme()["appearance_mode"])
        ctk.set_default_color_theme("blue")

        self.drawer_hud = None
        self.screen_pen = None
        self.main_window = MainWindow(
            data_manager=self.dm,
            sound_player=self.sound,
            theme_manager=self.theme_mgr,
            on_launch_corner_mode=self.show_drawer_mode,
            on_launch_screen_pen=self.toggle_screen_pen,
        )
        self.main_window.protocol("WM_DELETE_WINDOW", self.on_main_close)
        self.main_window.bind("<FocusIn>", self._on_main_window_focus)

    def _on_main_window_focus(self, event):
        if event.widget is self.main_window:
            if self.screen_pen and self.screen_pen.winfo_exists():
                if self.drawer_hud is None or not self.drawer_hud.winfo_exists() or self.drawer_hud.state() == "withdrawn":
                    self.screen_pen.hide_pen_hud()
                else:
                    self.screen_pen.reset_and_clear()

    def _raise_hud_peers(self):
        if self.drawer_hud and self.drawer_hud.winfo_exists() and self.drawer_hud.state() != "withdrawn":
            try:
                self.drawer_hud.attributes("-topmost", True)
                self.drawer_hud.lift()
            except Exception:
                pass

    def ensure_screen_pen(self, expand=False):
        if self.screen_pen is None or not self.screen_pen.winfo_exists():
            self.screen_pen = ScreenPenHUD(
                master=self.main_window,
                data_manager=self.dm,
                sound_player=self.sound,
                theme_manager=self.theme_mgr,
                on_raise_peers=self._raise_hud_peers,
                on_return_to_main=self.show_main_mode,
            )
            if expand and self.screen_pen._is_collapsed:
                self.screen_pen.toggle_collapse()
        else:
            self.screen_pen.show_pen_hud(expand=expand)

    def toggle_screen_pen(self):
        if self.main_window.state() != "withdrawn":
            self.main_window.withdraw()
            self.show_drawer_mode()
        if self.screen_pen is None or not self.screen_pen.winfo_exists():
            self.ensure_screen_pen(expand=True)
            self.screen_pen.select_tool("pen")
        elif self.screen_pen.state() == "withdrawn":
            self.screen_pen.show_pen_hud(expand=True)
            self.screen_pen.select_tool("pen")
        else:
            if self.screen_pen._is_collapsed:
                self.screen_pen.toggle_collapse()
            self.screen_pen.select_tool("pen")

    def show_drawer_mode(self):
        if self.drawer_hud is None or not self.drawer_hud.winfo_exists():
            self.drawer_hud = DrawerHUD(
                master=self.main_window,
                data_manager=self.dm,
                sound_player=self.sound,
                theme_manager=self.theme_mgr,
                on_return_to_main=self.show_main_mode,
                on_toggle_pen=self.toggle_screen_pen,
            )
        else:
            self.drawer_hud.deiconify()
            self.drawer_hud.refresh_classes_dropdown()
            self.drawer_hud.refresh_display()
            self.drawer_hud.lift()

        self.ensure_screen_pen(expand=False)

    def show_main_mode(self):
        if self.drawer_hud and self.drawer_hud.winfo_exists():
            self.drawer_hud.withdraw()
        if self.screen_pen and self.screen_pen.winfo_exists():
            self.screen_pen.hide_pen_hud()
        self.main_window.deiconify()
        self.main_window.refresh_all()
        self.main_window.lift()

    def on_main_close(self):
        if self.screen_pen and self.screen_pen.winfo_exists():
            try:
                self.screen_pen.destroy()
            except Exception:
                pass
        if self.drawer_hud and self.drawer_hud.winfo_exists():
            try:
                self.drawer_hud.destroy()
            except Exception:
                pass
        self.main_window.destroy()
        sys.exit(0)

    def run(self):
        self.main_window.mainloop()


if __name__ == "__main__":
    NovaboardApp().run()
