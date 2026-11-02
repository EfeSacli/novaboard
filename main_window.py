import os
import sys
import subprocess
from tkinter import messagebox, colorchooser
import customtkinter as ctk

from teacher_tools import TeacherToolsFrame
from theme_manager import THEMES
from ui_kit import (
    ThemedMixin, font, set_window_icon, center_window,
    attach_context_menu, paste_into_widget,
    BTN_ACCENT, BTN_SUCCESS, BTN_DANGER_SOFT, BTN_CARD, BTN_INNER,
    CARD, CARD_INNER, ENTRY, TEXTBOX, OPTION_MENU, SEGMENTED,
    TEXT_PRIMARY, TEXT_SECONDARY,
)

# Öğrenci durum rozeti (Sırada / Seçildi / Muaf) renk ve etiket tablosu
STATUS_BADGE = {
    "picked": ("Soru Yöneltildi", "badge_picked_bg", "badge_picked_text"),
    "exempt": ("Muaf (Devamsız)", "badge_exempt_bg", "badge_exempt_text"),
    "remaining": ("Sırada", "badge_remaining_bg", "badge_remaining_text"),
}


class MainWindow(ThemedMixin, ctk.CTk):
    """
    Novaboard - Merkezi Akıllı Tahta & Öğretmen Yönetim Paneli.
    Sol kenar çubuğunda sınıf listesi, sağda üç sekmeli çalışma alanı:
      1. Sınıf Listesi     (öğrenci ekleme, arama, durum değiştirme, geçmiş)
      2. Öğretmen Araçları (ders sayacı, grup oluşturucu, kelime yarışması, notlar)
      3. Ayarlar           (hazır temalar, özel renkler, yazı tipi/ölçek, ses ve animasyon)
    """

    def __init__(self, data_manager, sound_player, theme_manager, on_launch_corner_mode, on_launch_screen_pen=None):
        super().__init__()
        self.dm = data_manager
        self.sound = sound_player
        self.tm = theme_manager
        self.on_launch_corner_mode = on_launch_corner_mode
        self.on_launch_screen_pen = on_launch_screen_pen

        self.title("Novaboard - Akıllı Tahta Eğitim Yönetim Sistemi")
        set_window_icon(self, default=True)

        screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        win_w = min(1000, max(780, int(screen_w * 0.80)))
        win_h = min(680, max(520, int(screen_h * 0.80)))
        self.geometry(f"{win_w}x{win_h}+{max(10, (screen_w - win_w) // 2)}+{max(10, (screen_h - win_h) // 2)}")
        self.minsize(760, 500)

        self.search_filter = ""
        self._setup_layout()
        self.refresh_all()
        self.apply_theme()
        self.tm.register_callback(self.apply_theme)

        self.deiconify()
        self.lift()

    # =========================================================================
    # ANA YERLEŞİM (Sol Kenar Çubuğu + Sağ Sekmeli Alan)
    # =========================================================================
    def _setup_layout(self):
        self.styled(self, fg_color="bg_main")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._setup_sidebar()
        self._setup_main_area()

    def _setup_sidebar(self):
        self.sidebar_frame = self.styled(ctk.CTkFrame(self, width=260, corner_radius=0), fg_color="bg_sidebar")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        self.logo_label = self.styled(
            ctk.CTkLabel(self.sidebar_frame, text="Novaboard", font=font(22, bold=True)), TEXT_PRIMARY
        )
        self.logo_label.grid(row=0, column=0, padx=16, pady=(16, 2), sticky="w")

        self.subtitle_label = self.styled(
            ctk.CTkLabel(self.sidebar_frame, text="Sınıf Yönetimi", font=font(11)), TEXT_SECONDARY
        )
        self.subtitle_label.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

        self.class_scroll = self.styled(
            ctk.CTkScrollableFrame(
                self.sidebar_frame, label_text="Sınıflar", label_font=font(11, bold=True)
            ),
            fg_color="bg_sidebar",
            label_fg_color="bg_card_inner",
            label_text_color="text_secondary",
        )
        self.class_scroll.grid(row=2, column=0, padx=10, pady=4, sticky="nsew")

        self.class_btns_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.class_btns_frame.grid(row=3, column=0, padx=12, pady=6, sticky="ew")

        self.add_class_btn = self.styled(
            ctk.CTkButton(self.class_btns_frame, text="Yeni Sınıf Ekle", height=30, font=font(11, bold=True),
                          command=self._prompt_add_class),
            BTN_ACCENT,
        )
        self.add_class_btn.pack(fill="x", pady=2)

        self.rename_class_btn = self.styled(
            ctk.CTkButton(self.class_btns_frame, text="Sınıf Adını Değiştir", height=28, font=font(11), border_width=1,
                          command=self._prompt_rename_class),
            BTN_CARD,
        )
        self.rename_class_btn.pack(fill="x", pady=2)

        self.del_class_btn = self.styled(
            ctk.CTkButton(self.class_btns_frame, text="Sınıfı Sil", height=28, font=font(11),
                          command=self._confirm_delete_class),
            BTN_DANGER_SOFT,
        )
        self.del_class_btn.pack(fill="x", pady=2)

        self.bottom_sidebar = self.styled(
            ctk.CTkFrame(self.sidebar_frame, corner_radius=8, border_width=1), CARD
        )
        self.bottom_sidebar.grid(row=4, column=0, padx=10, pady=(6, 12), sticky="ew")

        self.launch_corner_btn = self.styled(
            ctk.CTkButton(self.bottom_sidebar, text="Ders Modunu Başlat", height=36, corner_radius=6,
                          font=font(11, bold=True), command=self.launch_corner_mode),
            BTN_SUCCESS,
        )
        self.launch_corner_btn.pack(fill="x", padx=8, pady=(8, 4))

        self.launch_hint = self.styled(
            ctk.CTkLabel(self.bottom_sidebar, text="Masaüstü öğrenci seçici ve kalemi açar", font=font(9)), TEXT_SECONDARY
        )
        self.launch_hint.pack(pady=(0, 6))

    def _setup_main_area(self):
        self.main_frame = self.styled(ctk.CTkFrame(self, corner_radius=0), fg_color="bg_main")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.top_tabs_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=44)
        self.top_tabs_frame.grid(row=0, column=0, padx=20, pady=(12, 4), sticky="ew")
        self.top_tabs_frame.pack_propagate(False)

        self.main_tab_selector = self.styled(
            ctk.CTkSegmentedButton(
                self.top_tabs_frame,
                values=["Sınıf Listesi", "Öğretmen Araçları", "Ayarlar"],
                command=self._on_main_tab_changed,
                height=34,
                font=font(11, bold=True),
            ),
            SEGMENTED,
        )
        self.main_tab_selector.pack(side="left")
        self.main_tab_selector.set("Sınıf Listesi")

        self.tab_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tab_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(4, 12))
        self.tab_container.grid_rowconfigure(0, weight=1)
        self.tab_container.grid_columnconfigure(0, weight=1)

        self.tab_roster = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self.tab_roster.grid(row=0, column=0, sticky="nsew")
        self._setup_roster_tab()

        self.tab_tools = TeacherToolsFrame(
            self.tab_container, data_manager=self.dm, sound_player=self.sound, theme_manager=self.tm
        )

        self.tab_theme = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self._setup_theme_tab()

    def _on_main_tab_changed(self, choice):
        for tab in (self.tab_roster, self.tab_tools, self.tab_theme):
            tab.grid_remove()

        if "Sınıf" in choice or "Öğrenci" in choice:
            self.tab_roster.grid(row=0, column=0, sticky="nsew")
            self.refresh_roster()
        elif "Araç" in choice:
            self.tab_tools.refresh_groups_class_info()
            self.tab_tools.grid(row=0, column=0, sticky="nsew")
        elif "Ayar" in choice or "Görünüm" in choice:
            self.tab_theme.grid(row=0, column=0, sticky="nsew")

    # =========================================================================
    # SEKME 1: ÖĞRENCİ VE SINIF YÖNETİMİ
    # =========================================================================
    def _setup_roster_tab(self):
        self.tab_roster.grid_rowconfigure(3, weight=1)
        self.tab_roster.grid_columnconfigure(0, weight=1)

        # Başlık + Seçim Geçmişi Butonu
        self.header_frame = ctk.CTkFrame(self.tab_roster, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, pady=(4, 8), sticky="ew")

        self.current_class_title = self.styled(
            ctk.CTkLabel(self.header_frame, text="Sınıf Seçimi Yapınız", font=font(18, bold=True)), TEXT_PRIMARY
        )
        self.current_class_title.pack(side="left")

        self.history_btn = self.styled(
            ctk.CTkButton(self.header_frame, text="Seçim Geçmişi", height=28, font=font(11), border_width=1,
                          command=self._open_history_dialog),
            BTN_CARD,
        )
        self.history_btn.pack(side="right")

        # İstatistik Kartları
        self.stats_cards_frame = ctk.CTkFrame(self.tab_roster, fg_color="transparent")
        self.stats_cards_frame.grid(row=1, column=0, pady=(0, 10), sticky="ew")

        self.card_total = self._create_stat_card(self.stats_cards_frame, "Toplam Öğrenci", "text_primary")
        self.card_total.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.card_picked = self._create_stat_card(self.stats_cards_frame, "Seçilen Öğrenci", "text_secondary")
        self.card_picked.pack(side="left", expand=True, fill="x", padx=6)

        self.card_remaining = self._create_stat_card(self.stats_cards_frame, "Kalan Öğrenci", "success")
        self.card_remaining.pack(side="left", expand=True, fill="x", padx=(6, 0))

        # Araç Çubuğu
        self.toolbar_frame = self.styled(
            ctk.CTkFrame(self.tab_roster, corner_radius=8, border_width=1), CARD
        )
        self.toolbar_frame.grid(row=2, column=0, pady=(0, 10), sticky="ew")

        self.bulk_paste_btn = self.styled(
            ctk.CTkButton(self.toolbar_frame, text="Toplu Öğrenci Ekle", height=32, font=font(11, bold=True),
                          command=self._open_bulk_paste_dialog),
            BTN_ACCENT,
        )
        self.bulk_paste_btn.pack(side="left", padx=(8, 6), pady=6)

        self.single_entry = self.styled(
            ctk.CTkEntry(self.toolbar_frame, placeholder_text="Öğrenci adı soyadı...", width=180, height=32,
                         font=font(11)),
            ENTRY,
        )
        self.single_entry.pack(side="left", padx=4, pady=6)
        self.single_entry.bind("<Return>", lambda e: self._add_single_student())
        attach_context_menu(self.single_entry, self.tm)

        self.add_single_btn = self.styled(
            ctk.CTkButton(self.toolbar_frame, text="Ekle", width=60, height=32, font=font(11), border_width=1,
                          command=self._add_single_student),
            BTN_INNER,
        )
        self.add_single_btn.pack(side="left", padx=(2, 8), pady=6)

        self.clear_roster_btn = self.styled(
            ctk.CTkButton(self.toolbar_frame, text="Listeyi Temizle", height=32, width=100, font=font(11),
                          command=self._confirm_clear_roster),
            BTN_DANGER_SOFT,
        )
        self.clear_roster_btn.pack(side="right", padx=(4, 8), pady=6)

        self.reset_cycle_btn = self.styled(
            ctk.CTkButton(self.toolbar_frame, text="Seçimleri Sıfırla", height=32, width=120, font=font(11),
                          border_width=1, command=self._confirm_reset_cycle),
            BTN_INNER,
        )
        self.reset_cycle_btn.pack(side="right", padx=4, pady=6)

        # Arama + Öğrenci Tablosu
        self.roster_container = ctk.CTkFrame(self.tab_roster, fg_color="transparent")
        self.roster_container.grid(row=3, column=0, pady=(0, 6), sticky="nsew")
        self.roster_container.grid_rowconfigure(1, weight=1)
        self.roster_container.grid_columnconfigure(0, weight=1)

        self.search_entry = self.styled(
            ctk.CTkEntry(self.roster_container, placeholder_text="Listede ara...", height=30, font=font(11)), ENTRY
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.search_entry.bind("<KeyRelease>", self._on_search_typed)
        attach_context_menu(self.search_entry, self.tm)

        self.roster_scroll = self.styled(
            ctk.CTkScrollableFrame(self.roster_container, corner_radius=8, border_width=1), CARD
        )
        self.roster_scroll.grid(row=1, column=0, sticky="nsew")

    def _create_stat_card(self, parent, title, color_key):
        frame = self.styled(ctk.CTkFrame(parent, corner_radius=8, border_width=1, height=64), CARD)
        frame.pack_propagate(False)

        val_label = self.styled(ctk.CTkLabel(frame, text="0", font=font(20, bold=True)), text_color=color_key)
        val_label.pack(pady=(6, 0))

        title_label = self.styled(ctk.CTkLabel(frame, text=title, font=font(10)), TEXT_SECONDARY)
        title_label.pack(pady=(0, 4))

        frame._val_label = val_label
        frame._title_label = title_label
        return frame

    # =========================================================================
    # SEKME 3: AYARLAR (Tema, Özel Renkler, Yazı Tipi/Ölçek, Animasyon & Ses)
    # =========================================================================
    def _setup_theme_tab(self):
        self.theme_card = self.styled(
            ctk.CTkScrollableFrame(self.tab_theme, corner_radius=10, border_width=1), CARD
        )
        self.theme_card.pack(fill="both", expand=True, padx=4, pady=4)

        self.theme_main_title = self.styled(
            ctk.CTkLabel(self.theme_card, text="Arayüz Teması", font=font(15, bold=True)), TEXT_PRIMARY
        )
        self.theme_main_title.pack(anchor="w", padx=16, pady=(16, 4))

        self.theme_desc = self.styled(
            ctk.CTkLabel(self.theme_card, text="Kullanmak istediğiniz renk temasını seçebilirsiniz.", font=font(11)),
            TEXT_SECONDARY,
        )
        self.theme_desc.pack(anchor="w", padx=16, pady=(0, 16))

        # Hazır Tema Kartları
        self.theme_swatches_frame = ctk.CTkFrame(self.theme_card, fg_color="transparent")
        self.theme_swatches_frame.pack(fill="x", padx=16, pady=4)

        self.theme_cards_list = []
        for theme_id, th in THEMES.items():
            card = ctk.CTkFrame(
                self.theme_swatches_frame,
                fg_color=th["bg_card_inner"],
                corner_radius=8,
                border_width=1,
                border_color=th["border"],
                height=64,
                cursor="hand2",
            )
            card.pack(fill="x", pady=4)
            card.pack_propagate(False)

            dot = ctk.CTkLabel(
                card, text="●", font=ctk.CTkFont(size=20), text_color=th["accent"], cursor="hand2"
            )
            dot.pack(side="left", padx=14)

            text_frame = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
            text_frame.pack(side="left", fill="y", pady=8)

            t_name = ctk.CTkLabel(
                text_frame, text=th["name"], font=font(12, bold=True), text_color=th["text_primary"], cursor="hand2"
            )
            t_name.pack(anchor="w")

            t_sub = ctk.CTkLabel(
                text_frame,
                text=f"Vurgu: {th['accent']} • Mod: {th['appearance_mode']}",
                font=font(10),
                text_color=th["text_secondary"],
                cursor="hand2",
            )
            t_sub.pack(anchor="w")

            for clickable in (card, dot, text_frame, t_name, t_sub):
                clickable.bind("<Button-1>", lambda _e, tid=theme_id: self._apply_theme(tid))

            apply_btn = ctk.CTkButton(
                card,
                text="Uygula",
                width=90,
                height=30,
                font=font(11, bold=True),
                fg_color=th["accent"],
                hover_color=th["accent_hover"],
                text_color=th["accent_text"],
                command=lambda tid=theme_id: self._apply_theme(tid),
            )
            apply_btn.pack(side="right", padx=14)
            self.theme_cards_list.append((theme_id, card, t_name, t_sub, apply_btn))

        # Özel Renkler
        self.custom_color_title, self.custom_bar = self._add_settings_section("Özel Renkler")

        self.pick_bg_btn = self.styled(
            ctk.CTkButton(self.custom_bar, text="Arka Plan Rengi", height=32, font=font(11), border_width=1,
                          command=self._pick_custom_bg_color),
            BTN_CARD,
        )
        self.pick_bg_btn.pack(side="left", padx=12, pady=10)

        self.pick_accent_btn = self.styled(
            ctk.CTkButton(self.custom_bar, text="Vurgu Rengi", height=32, font=font(11), border_width=1,
                          command=self._pick_custom_accent_color),
            BTN_CARD,
        )
        self.pick_accent_btn.pack(side="left", padx=6, pady=10)

        self.reset_colors_btn = self.styled(
            ctk.CTkButton(self.custom_bar, text="Varsayılan Renkler", height=32, command=self._reset_colors),
            BTN_DANGER_SOFT,
        )
        self.reset_colors_btn.pack(side="right", padx=12, pady=10)

        # Yazı Tipi ve Boyut
        self.font_section_title, self.font_bar = self._add_settings_section("Yazı Tipi ve Boyut")

        self.font_family_lbl = self.styled(
            ctk.CTkLabel(self.font_bar, text="Yazı Tipi:", font=font(11, bold=True)), TEXT_PRIMARY
        )
        self.font_family_lbl.pack(side="left", padx=(14, 6), pady=10)

        self.font_family_menu = self.styled(
            ctk.CTkOptionMenu(
                self.font_bar,
                values=["Segoe UI", "Arial", "Roboto", "Tahoma", "Trebuchet MS", "Consolas"],
                command=self._on_font_family_changed,
                width=140,
                height=30,
            ),
            OPTION_MENU,
        )
        self.font_family_menu.set(self.dm.get_setting("font_family", "Segoe UI"))
        self.font_family_menu.pack(side="left", padx=6, pady=10)

        self.font_scale_lbl = self.styled(
            ctk.CTkLabel(self.font_bar, text="Arayüz Ölçeği:", font=font(11, bold=True)), TEXT_PRIMARY
        )
        self.font_scale_lbl.pack(side="left", padx=(14, 6), pady=10)

        self.font_scale_menu = self.styled(
            ctk.CTkOptionMenu(
                self.font_bar,
                values=["Standart", "Büyük (Akıllı Tahta)", "Çok Büyük"],
                command=self._on_font_scale_changed,
                width=160,
                height=30,
            ),
            OPTION_MENU,
        )
        self.font_scale_menu.set(self.dm.get_setting("font_size_scale", "Standart"))
        self.font_scale_menu.pack(side="left", padx=6, pady=10)

        # Animasyon ve Ses
        self.anim_section_title, self.anim_bar = self._add_settings_section("Animasyon ve Ses", bottom_pad=20)

        self.paper_anim_switch = self.styled(
            ctk.CTkSwitch(self.anim_bar, text="Geçiş Animasyonları", font=font(11), command=self._toggle_paper_anim),
            TEXT_PRIMARY,
        )
        if self.dm.get_setting("paper_animation_enabled", True):
            self.paper_anim_switch.select()
        self.paper_anim_switch.pack(padx=14, pady=(12, 6), anchor="w")

        self.sound_switch = self.styled(
            ctk.CTkSwitch(self.anim_bar, text="Ses Efektleri", font=font(11), command=self._toggle_sound_switch),
            TEXT_PRIMARY,
        )
        if self.dm.get_setting("sound_enabled", True):
            self.sound_switch.select()
        self.sound_switch.pack(padx=14, pady=(6, 12), anchor="w")

        # Yeniden Başlat
        self.restart_section_title, self.restart_bar = self._add_settings_section("Yeniden Başlat", bottom_pad=24)

        self.restart_hint_lbl = self.styled(
            ctk.CTkLabel(
                self.restart_bar,
                text="Tüm tema, özel renk, yazı tipi ve boyut ayarlarını tazelemek için programı yeniden başlatabilirsiniz.",
                font=font(11),
            ),
            TEXT_SECONDARY,
        )
        self.restart_hint_lbl.pack(side="left", padx=14, pady=12)

        self.restart_btn = self.styled(
            ctk.CTkButton(self.restart_bar, text="🔄 Yeniden Başlat", height=34, width=140, font=font(11, bold=True),
                          command=self._restart_app),
            BTN_ACCENT,
        )
        self.restart_btn.pack(side="right", padx=14, pady=12)

    def _add_settings_section(self, title_text, bottom_pad=4):
        """Ayarlar sekmesine başlık ve çerçeveli kart satırı ekler."""
        title = self.styled(ctk.CTkLabel(self.theme_card, text=title_text, font=font(13, bold=True)), TEXT_PRIMARY)
        title.pack(anchor="w", padx=16, pady=(24, 8))

        bar = self.styled(ctk.CTkFrame(self.theme_card, corner_radius=8, border_width=1), CARD_INNER)
        bar.pack(fill="x", padx=16, pady=(4, bottom_pad))
        return title, bar

    # =========================================================================
    # AYAR EYLEMLERİ
    # =========================================================================
    def _apply_theme(self, theme_id):
        self.tm.set_theme(theme_id)

    def _reset_colors(self):
        self.tm.reset_custom_colors()

    def _pick_custom_bg_color(self):
        color = colorchooser.askcolor(title="Novaboard - Arka Plan Rengi")[1]
        if color:
            self.tm.set_custom_colors(bg_hex=color)

    def _pick_custom_accent_color(self):
        color = colorchooser.askcolor(title="Novaboard - Vurgu Rengi")[1]
        if color:
            self.tm.set_custom_colors(accent_hex=color)

    def _toggle_paper_anim(self):
        self.dm.set_setting("paper_animation_enabled", bool(self.paper_anim_switch.get()))

    def _toggle_sound_switch(self):
        self.dm.set_setting("sound_enabled", bool(self.sound_switch.get()))

    def _on_font_family_changed(self, choice):
        if choice != self.dm.get_setting("font_family", "Segoe UI"):
            self.dm.set_setting("font_family", choice)
            self._restart_app()

    def _on_font_scale_changed(self, choice):
        if choice != self.dm.get_setting("font_size_scale", "Standart"):
            self.dm.set_setting("font_size_scale", choice)
            self._restart_app()

    def _restart_app(self):
        """Programı yeni tema, ölçek ve yazı tipi ayarlarıyla temiz bir şekilde yeniden başlatır."""
        try:
            clean_env = os.environ.copy()
            for key in ("_MEIPASS2", "_MEIPASS", "PYTHONPATH", "PYTHONHOME"):
                clean_env.pop(key, None)

            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = (
                    getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
                    | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
                )

            if getattr(sys, "frozen", False):
                target = os.path.abspath(sys.executable)
                app_dir = os.path.dirname(target)
                cmd = [target]
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
                app_py = os.path.join(app_dir, "app.py")
                target = app_py if os.path.exists(app_py) else os.path.abspath(sys.argv[0])
                cmd = [sys.executable, target]

            subprocess.Popen(cmd, env=clean_env, cwd=app_dir, creationflags=creation_flags, close_fds=True)
        except Exception as e:
            print(f"Yeniden başlatma hatası: {e}")
            self.apply_theme()
            return

        try:
            self.destroy()
        except Exception:
            pass
        os._exit(0)

    # =========================================================================
    # LİSTE YENİLEME (Sol Kenar Çubuğu & Öğrenci Tablosu)
    # =========================================================================
    def _on_search_typed(self, _event):
        self.search_filter = self.search_entry.get().strip().lower()
        self.refresh_roster()

    def launch_corner_mode(self):
        active = self.dm.get_active_class()
        if not active:
            messagebox.showwarning(
                "Sınıf Tanımlanmadı",
                "Ders ekranını başlatabilmek için sol menüden 'Yeni Sınıf Tanımla' butonuna basarak bir sınıf oluşturunuz.",
            )
            return

        if not self.dm.get_all_students(active):
            messagebox.showwarning(
                "Öğrenci Kaydı Yok",
                f"'{active}' sınıfında henüz kayıtlı öğrenci bulunmuyor.\n"
                "Lütfen 'Toplu Liste Aktarımı' butonunu kullanarak liste ekleyiniz.",
            )
            return

        self.withdraw()
        self.on_launch_corner_mode()

    def refresh_all(self):
        self.refresh_classes_sidebar()
        self.refresh_roster()

    def refresh_classes_sidebar(self):
        t = self.tm.get_theme()
        for widget in self.class_scroll.winfo_children():
            widget.destroy()

        class_names = self.dm.get_class_names()
        active = self.dm.get_active_class()

        if not class_names:
            ctk.CTkLabel(
                self.class_scroll,
                text="Henüz sınıf tanımlanmadı.\nAşağıdaki butondan ekleyiniz.",
                font=font(11),
                text_color=t["text_secondary"],
                justify="center",
            ).pack(pady=20)
            return

        for cname in class_names:
            count = len(self.dm.get_all_students(cname))
            is_active = cname == active
            ctk.CTkButton(
                self.class_scroll,
                text=f"  {cname}  ({count})",
                anchor="w",
                height=32,
                corner_radius=6,
                font=font(11, bold=is_active),
                fg_color=t["accent"] if is_active else t["bg_card_inner"],
                hover_color=t["accent_hover"] if is_active else t["bg_hover"],
                text_color=t["accent_text"] if is_active else t["text_primary"],
                border_width=0 if is_active else 1,
                border_color=t["border"],
                command=lambda cn=cname: self._select_class(cn),
            ).pack(fill="x", pady=2)

    def _select_class(self, class_name):
        self.dm.set_active_class(class_name)
        self.refresh_all()
        if hasattr(self, "tab_tools"):
            self.tab_tools.refresh_groups_class_info()

    def refresh_roster(self):
        active = self.dm.get_active_class()
        classes = self.dm.get_class_names()
        t = self.tm.get_theme()

        for widget in self.roster_scroll.winfo_children():
            widget.destroy()

        if not classes or not active:
            self.current_class_title.configure(text="Novaboard Eğitim Paneli", text_color=t["text_primary"])
            self.card_total._val_label.configure(text="0", text_color=t["text_primary"])
            self.card_picked._val_label.configure(text="0", text_color=t["text_secondary"])
            self.card_remaining._val_label.configure(text="0", text_color=t["success"])
            self._render_empty_welcome(t)
            return

        self.current_class_title.configure(text=f"{active} Sınıf Listesi", text_color=t["text_primary"])

        all_students = self.dm.get_all_students(active)
        picked_set = set(self.dm.get_picked_students(active))
        remaining = self.dm.get_remaining_students(active)

        self.card_total._val_label.configure(text=str(len(all_students)), text_color=t["text_primary"])
        self.card_picked._val_label.configure(text=str(len(picked_set)), text_color=t["text_secondary"])
        self.card_remaining._val_label.configure(text=str(len(remaining)), text_color=t["success"])

        filtered = [
            (idx + 1, s)
            for idx, s in enumerate(all_students)
            if not self.search_filter or self.search_filter in s.lower()
        ]

        if not filtered:
            msg = (
                "Sınıfta henüz öğrenci kaydı yok. 'Toplu Liste Aktarımı' butonunu kullanabilirsiniz."
                if not all_students
                else "Arama kriterine uygun öğrenci bulunamadı."
            )
            ctk.CTkLabel(
                self.roster_scroll, text=msg, font=font(12), text_color=t["text_secondary"], justify="center"
            ).pack(pady=35)
            return

        for original_num, name in filtered:
            self._render_student_row(original_num, name, active, t)

        ctk.CTkFrame(self.roster_scroll, height=30, fg_color="transparent").pack(fill="x", pady=(0, 15))

    def _render_empty_welcome(self, t):
        welcome_frame = ctk.CTkFrame(self.roster_scroll, fg_color="transparent")
        welcome_frame.pack(expand=True, fill="both", pady=40)

        ctk.CTkLabel(
            welcome_frame, text="Yeni Sınıf Tanımlayarak Başlayınız", font=font(15, bold=True),
            text_color=t["text_primary"],
        ).pack(pady=(10, 6))

        ctk.CTkLabel(
            welcome_frame,
            text=(
                "Sol paneldeki 'Yeni Sınıf Tanımla' butonuna basarak ilk sınıfınızı oluşturabilir,\n"
                "ardından e-Okul veya Excel üzerinden öğrenci listenizi aktarabilirsiniz."
            ),
            font=font(12),
            text_color=t["text_secondary"],
            justify="center",
        ).pack(pady=(0, 16))

        ctk.CTkButton(
            welcome_frame,
            text="İlk Sınıfınızı Tanımlayın",
            height=36,
            font=font(11, bold=True),
            fg_color=t["accent"],
            hover_color=t["accent_hover"],
            text_color=t["accent_text"],
            command=self._prompt_add_class,
        ).pack()

    def _render_student_row(self, original_num, name, active_class, t):
        status = self.dm.get_student_status(name, active_class)
        is_remaining = status == "remaining"
        badge_text, bg_key, tc_key = STATUS_BADGE.get(status, STATUS_BADGE["remaining"])

        row = ctk.CTkFrame(
            self.roster_scroll, fg_color=t["bg_card_inner"], corner_radius=6, border_width=1, border_color=t["border"]
        )
        row.pack(fill="x", padx=4, pady=2)

        ctk.CTkLabel(row, text=f"{original_num:02d}", width=32, font=font(10), text_color=t["text_muted"]).pack(
            side="left", padx=(6, 2), pady=4
        )
        ctk.CTkLabel(
            row,
            text=name,
            font=font(12, bold=is_remaining),
            text_color=t["text_primary"] if is_remaining else t["text_secondary"],
        ).pack(side="left", padx=6, pady=4)

        ctk.CTkButton(
            row,
            text=badge_text,
            font=font(10, bold=is_remaining),
            text_color=t[tc_key],
            fg_color=t[bg_key],
            hover_color=t[bg_key],
            corner_radius=4,
            height=24,
            width=110,
            command=lambda s=name: self._cycle_student_status(s),
        ).pack(side="right", padx=(4, 6), pady=4)

        ctk.CTkButton(
            row,
            text="✕",
            width=22,
            height=22,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=t["danger_bg"],
            text_color=t["text_muted"],
            command=lambda s=name: self._delete_student(s),
        ).pack(side="right", padx=2, pady=4)

    # =========================================================================
    # SINIF VE ÖĞRENCİ İŞLEMLERİ
    # =========================================================================
    def _prompt_add_class(self):
        dialog = ctk.CTkInputDialog(text="Tanımlanacak sınıf adı (Örn: 9-A, 10-B, 11-F):", title="Yeni Sınıf Tanımlama")
        name = dialog.get_input()
        if name:
            success, msg = self.dm.add_class(name)
            if success:
                self.refresh_all()
            else:
                messagebox.showerror("Hata", msg)

    def _prompt_rename_class(self):
        active = self.dm.get_active_class()
        if not active:
            messagebox.showinfo("Bilgilendirme", "Lütfen önce bir sınıf seçiniz.")
            return
        dialog = ctk.CTkInputDialog(text=f"'{active}' için güncel sınıf adı:", title="Sınıf Adını Güncelle")
        new_name = dialog.get_input()
        if new_name:
            success, msg = self.dm.rename_class(active, new_name)
            if success:
                self.refresh_all()
            else:
                messagebox.showerror("Hata", msg)

    def _confirm_delete_class(self):
        active = self.dm.get_active_class()
        if active and messagebox.askyesno(
            "Silme Onayı", f"'{active}' sınıfını ve kayıtlı öğrencilerini silmek istediğinizi onaylıyor musunuz?"
        ):
            self.dm.delete_class(active)
            self.refresh_all()

    def _add_single_student(self):
        if not self.dm.get_active_class():
            messagebox.showinfo("Bilgilendirme", "Lütfen önce bir sınıf tanımlayınız.")
            return

        name = self.single_entry.get().strip()
        if not name:
            return
        success, msg = self.dm.add_student(name)
        if success:
            self.single_entry.delete(0, "end")
            self.refresh_all()
        else:
            messagebox.showwarning("Uyarı", msg)

    def _delete_student(self, student_name):
        self.dm.remove_student(student_name)
        self.refresh_all()

    def _cycle_student_status(self, student_name):
        self.dm.cycle_student_status(student_name)
        self.refresh_all()

    def _confirm_clear_roster(self):
        active = self.dm.get_active_class()
        if active and messagebox.askyesno(
            "Listeyi Temizleme Onayı",
            f"'{active}' sınıfındaki tüm öğrenci kayıtlarını silmek istediğinizi onaylıyor musunuz?",
        ):
            self.dm.set_students_list([])
            self.refresh_all()

    def _confirm_reset_cycle(self):
        active = self.dm.get_active_class()
        if active and messagebox.askyesno(
            "Soru Turunu Sıfırlama Onayı",
            f"'{active}' sınıfı için soru sırasını baştan başlatmak istediğinizi onaylıyor musunuz?",
        ):
            self.dm.reset_picked()
            self.refresh_all()

    # =========================================================================
    # MODAL PENCERELER (Seçim Geçmişi & Toplu Liste Aktarımı)
    # =========================================================================
    def _create_modal(self, title, width, height):
        t = self.tm.get_theme()
        modal = ctk.CTkToplevel(self)
        modal.title(title)
        modal.resizable(False, False)
        modal.configure(fg_color=t["bg_main"])
        modal.grab_set()
        center_window(modal, width, height)
        return modal, t

    def _open_history_dialog(self):
        active = self.dm.get_active_class()
        if not active:
            messagebox.showinfo("Bilgilendirme", "Lütfen önce bir sınıf seçiniz.")
            return

        history = self.dm.get_history(active)
        modal, t = self._create_modal(f"Seçim Geçmişi - {active}", 440, 480)

        ctk.CTkLabel(
            modal, text=f"{active} Sınıfı Soru Sırası Kayıtları", font=font(13, bold=True),
            text_color=t["text_primary"],
        ).pack(padx=16, pady=(16, 8), anchor="w")

        scroll = ctk.CTkScrollableFrame(modal, fg_color=t["bg_card"], corner_radius=6, border_width=1, border_color=t["border"])
        scroll.pack(fill="both", expand=True, padx=16, pady=8)

        if not history:
            ctk.CTkLabel(
                scroll, text="Bu oturumda henüz soru yöneltilen öğrenci bulunmuyor.", text_color=t["text_secondary"]
            ).pack(pady=40)
        else:
            for idx, item in enumerate(history, 1):
                row = ctk.CTkFrame(scroll, fg_color=t["bg_card_inner"], height=32, corner_radius=4)
                row.pack(fill="x", pady=2)
                row.pack_propagate(False)

                ctk.CTkLabel(row, text=f"{idx:02d}.", width=30, font=ctk.CTkFont(size=10), text_color=t["text_muted"]).pack(side="left", padx=4)
                ctk.CTkLabel(row, text=item.get("student", ""), font=font(11, bold=True), text_color=t["text_primary"]).pack(side="left", padx=6)
                ctk.CTkLabel(row, text=item.get("timestamp", ""), font=ctk.CTkFont(size=10), text_color=t["text_secondary"]).pack(side="right", padx=8)

        btn_bar = ctk.CTkFrame(modal, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=(4, 12))

        def _clear_h():
            self.dm.clear_history(active)
            modal.destroy()
            messagebox.showinfo("Bilgilendirme", "Seçim geçmişi temizlenmiştir.")

        ctk.CTkButton(
            btn_bar, text="Geçmişi Temizle", height=30, fg_color=t["danger_bg"], hover_color=t["danger_hover"],
            text_color=t["danger_text"], command=_clear_h,
        ).pack(side="left")

        ctk.CTkButton(
            btn_bar, text="Kapat", height=30, width=70, fg_color=t["bg_card"], hover_color=t["bg_hover"],
            text_color=t["text_primary"], command=modal.destroy,
        ).pack(side="right")

    def _open_bulk_paste_dialog(self):
        active = self.dm.get_active_class()
        if not active:
            messagebox.showinfo("Bilgilendirme", "Lütfen önce bir sınıf tanımlayınız.")
            return

        modal, t = self._create_modal(f"Toplu Liste Aktarımı - {active}", 520, 460)

        ctk.CTkLabel(
            modal,
            text=(
                "e-Okul veya Excel üzerinden kopyalanan listeyi bu alana yapıştırabilirsiniz.\n"
                "Sıra numaraları ve gereksiz karakterler sistem tarafından otomatik temizlenir."
            ),
            font=font(11),
            text_color=t["text_secondary"],
            justify="left",
        ).pack(padx=16, pady=(12, 6), anchor="w")

        textbox = ctk.CTkTextbox(
            modal,
            height=280,
            font=font(11, family="Consolas"),
            fg_color=t["input_bg"],
            text_color=t["input_text"],
            corner_radius=6,
            border_width=1,
            border_color=t["input_border"],
        )
        textbox.pack(fill="both", expand=True, padx=16, pady=6)
        attach_context_menu(textbox, self.tm)

        current_students = self.dm.get_all_students(active)
        if current_students:
            textbox.insert("1.0", "\n".join(current_students))

        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(6, 12))

        ctk.CTkButton(
            btn_frame, text="📋 Panodan Yapıştır", height=34, font=font(11, bold=True),
            fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["accent_text"],
            command=lambda: paste_into_widget(textbox),
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_frame, text="🗑️ Temizle", height=34, width=80, font=font(11),
            fg_color=t["danger_bg"], hover_color=t["danger_hover"], text_color=t["danger_text"],
            command=lambda: textbox.delete("1.0", "end"),
        ).pack(side="left")

        def _save():
            parsed = self.dm.parse_bulk_text(textbox.get("1.0", "end"))
            if not parsed:
                messagebox.showwarning("Uyarı", "Geçerli bir öğrenci kaydı tespit edilemedi.", parent=modal)
                return
            self.dm.set_students_list(parsed, active)
            modal.destroy()
            self.refresh_all()
            messagebox.showinfo("İşlem Başarılı", f"{len(parsed)} adet öğrenci kaydı sisteme aktarılmıştır.")

        ctk.CTkButton(
            btn_frame, text="Kaydet ve Aktar", height=34, font=font(11, bold=True),
            fg_color=t["success"], hover_color=t["success_hover"], text_color="#ffffff", command=_save,
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            btn_frame, text="İptal", height=34, width=70, fg_color=t["bg_card"], hover_color=t["bg_hover"],
            text_color=t["text_primary"], command=modal.destroy,
        ).pack(side="right")

    # =========================================================================
    # TEMA UYGULAMA
    # =========================================================================
    def apply_theme(self):
        t = self.tm.get_theme()
        try:
            super().apply_theme()

            active_tid = self.tm.get_current_theme_id()
            for tid, card, t_name, t_sub, apply_btn in getattr(self, "theme_cards_list", []):
                card_th = THEMES[tid]
                is_active = tid == active_tid
                card.configure(
                    fg_color=t["bg_card_inner"],
                    border_width=2 if is_active else 1,
                    border_color=t["accent"] if is_active else t["border"],
                )
                t_name.configure(text_color=t["accent"] if is_active else t["text_primary"])
                t_sub.configure(text_color=t["text_secondary"])
                if is_active:
                    apply_btn.configure(
                        text="✓ Aktif", fg_color=t["success"], hover_color=t["success_hover"],
                        text_color="#ffffff", state="disabled",
                    )
                else:
                    apply_btn.configure(
                        text="Uygula", fg_color=card_th["accent"], hover_color=card_th["accent_hover"],
                        text_color=card_th["accent_text"], state="normal",
                    )

            if hasattr(self, "tab_tools"):
                self.tab_tools.apply_theme()

            self.refresh_classes_sidebar()
            self.refresh_roster()
            self.update_idletasks()
        except Exception:
            pass
