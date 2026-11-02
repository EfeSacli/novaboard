import sys
import ctypes
import random
from tkinter import messagebox
import customtkinter as ctk

from notebook_overlay import NotebookRevealOverlay
from ui_kit import (
    ThemedMixin, font, set_window_icon,
    BTN_ACCENT, BTN_SUCCESS, BTN_INNER,
    CARD, OPTION_MENU_INNER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
)


class DrawerHUD(ThemedMixin, ctk.CTkToplevel):
    """
    Novaboard - Akıllı Tahta Kayan Çekmece HUD (Slide-out Drawer).
    Ekranın sağ üst köşesine sabitlenir. Solundaki açma/kapatma kulbuna
    (sağ ok ▶) tıklandığında ekranın sağ kenarına doğru yumuşak animasyonla
    içeri kayar ve yalnızca minik kulp (sol ok ◀) kalır.
    Tekrar tıklandığında yumuşak animasyonla sola doğru geri açılarak kura paneli sunulur.
    Öğrenci seçildiğinde tam ekran kareli defter animasyonunu başlatır.
    """

    def __init__(self, master, data_manager, sound_player, theme_manager, on_return_to_main, on_toggle_pen=None):
        super().__init__(master)
        self.dm = data_manager
        self.sound = sound_player
        self.tm = theme_manager
        self.on_return_to_main = on_return_to_main
        self.on_toggle_pen = on_toggle_pen

        self.overrideredirect(True)
        set_window_icon(self, default=False)

        self.full_width = 344
        self.collapsed_width = 44
        self.panel_height = 146
        self.margin_right = 10

        self._is_collapsed = False
        self._is_animating_slide = False
        self._is_picking = False
        self._last_shown_student = None
        self._is_cycle_completed = False

        self._is_dragging = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._win_orig_x = 0
        self._win_orig_y = 0
        self._custom_pos_set = False
        self.pos_x = 0
        self.pos_y = 20
        self._load_or_compute_position(self.full_width)

        self.attributes("-topmost", True)
        self.lift()
        self.geometry(f"{self.full_width}x{self.panel_height}+{self.pos_x}+{self.pos_y}")

        self._setup_ui()
        self._bind_events()
        self.refresh_display()
        self.apply_theme()
        self.tm.register_callback(self.apply_theme)
        self.after(50, self._ensure_topmost_lock)

    def _ensure_topmost_lock(self):
        try:
            self.attributes("-topmost", True)
            self.lift()
        except Exception:
            pass

    # =========================================================================
    # ARAYÜZ KURULUMU
    # =========================================================================
    def _setup_ui(self):
        self.main_container = self.styled(
            ctk.CTkFrame(self, corner_radius=10, border_width=1.5), fg_color="bg_main", border_color="border"
        )
        self.main_container.pack(fill="both", expand=True)

        # 1. Sol kenar çekmece açma/kapama kulbu
        self.handle_frame = self.styled(
            ctk.CTkFrame(self.main_container, width=self.collapsed_width - 4, corner_radius=8), fg_color="bg_sidebar"
        )
        self.handle_frame.pack(side="left", fill="y", padx=2, pady=2)
        self.handle_frame.pack_propagate(False)

        self.collapsed_drag = self.styled(
            ctk.CTkLabel(
                self.handle_frame, text="✥", width=self.collapsed_width - 8, height=16,
                font=font(12, bold=True), cursor="fleur",
            ),
            TEXT_ACCENT,
        )
        self.collapsed_drag.pack(side="top", pady=(2, 1))

        self.toggle_btn = self.styled(
            ctk.CTkButton(
                self.handle_frame, text="▶\n\nN\nO\nV\nA", width=self.collapsed_width - 8, corner_radius=6,
                font=font(10, bold=True), command=self.toggle_collapse,
            ),
            BTN_ACCENT,
        )
        self.toggle_btn.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        # 2. Sağ gövde paneli (kura kontrolleri)
        self.content_panel = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_panel.pack(side="left", fill="both", expand=True, padx=(2, 4), pady=2)

        self.header_frame = self.styled(
            ctk.CTkFrame(self.content_panel, corner_radius=6, border_width=1, height=28), CARD
        )
        self.header_frame.pack(fill="x", pady=(2, 3))
        self.header_frame.pack_propagate(False)

        self.drag_grip = self.styled(
            ctk.CTkLabel(self.header_frame, text="✥ Taşı", height=22, font=font(10, bold=True), cursor="fleur"),
            TEXT_ACCENT,
        )
        self.drag_grip.pack(side="left", padx=(3, 2), pady=3)

        self.class_var = ctk.StringVar(value=self.dm.get_active_class())
        class_names = self.dm.get_class_names() or ["Sınıf Yok"]
        self.class_dropdown = self.styled(
            ctk.CTkOptionMenu(
                self.header_frame,
                values=class_names,
                variable=self.class_var,
                command=self._on_class_changed,
                width=82,
                height=22,
                font=font(10, bold=True),
                dropdown_font=font(10),
            ),
            OPTION_MENU_INNER,
            dropdown_fg_color="bg_card",
            dropdown_text_color="text_primary",
            dropdown_hover_color="bg_hover",
        )
        self.class_dropdown.pack(side="left", padx=(3, 2), pady=3)

        self.stats_label = self.styled(
            ctk.CTkLabel(self.header_frame, text="0 / 0", font=font(10, bold=True)), TEXT_ACCENT
        )
        self.stats_label.pack(side="left", padx=3)

        self.close_btn = self.styled(
            ctk.CTkButton(
                self.header_frame, text="X", width=24, height=22, font=font(10, bold=True), fg_color="transparent",
                command=self._go_to_main,
            ),
            hover_color="danger_bg", text_color="text_secondary",
        )
        self.close_btn.pack(side="right", padx=(1, 3), pady=3)

        self.settings_btn = self.styled(
            ctk.CTkButton(
                self.header_frame, text="Panel", width=42, height=22, corner_radius=4, font=font(9, bold=True),
                border_width=1, command=self._go_to_main,
            ),
            BTN_INNER,
        )
        self.settings_btn.pack(side="right", padx=2, pady=3)

        self.pen_btn = self.styled(
            ctk.CTkButton(
                self.header_frame, text="Kalem", width=44, height=22, corner_radius=4, font=font(9, bold=True),
                border_width=1, command=self._toggle_pen,
            ),
            BTN_INNER,
        )
        self.pen_btn.pack(side="right", padx=2, pady=3)

        # İsim gösterim kartı
        self.card_frame = self.styled(
            ctk.CTkFrame(self.content_panel, corner_radius=6, border_width=1, height=54), CARD
        )
        self.card_frame.pack(fill="x", pady=2)
        self.card_frame.pack_propagate(False)

        self.name_label = self.styled(
            ctk.CTkLabel(self.card_frame, text="Öğrenci Seçimi", font=font(13, bold=True)), TEXT_PRIMARY
        )
        self.name_label.pack(expand=True, pady=(2, 0))

        self.sub_label = self.styled(ctk.CTkLabel(self.card_frame, text="", font=font(9)), TEXT_SECONDARY)
        self.sub_label.pack(pady=(0, 2))

        # Eylem butonları
        self.actions_frame = ctk.CTkFrame(self.content_panel, fg_color="transparent")
        self.actions_frame.pack(fill="x", pady=(2, 2))

        self.pick_button = self.styled(
            ctk.CTkButton(
                self.actions_frame, text="Öğrenci Seç", height=28, corner_radius=4, font=font(11, bold=True),
                command=self.start_pick,
            ),
            BTN_ACCENT,
        )
        self.pick_button.pack(side="left", expand=True, fill="x", padx=(0, 3))

        self.undo_btn = self.styled(
            ctk.CTkButton(
                self.actions_frame, text="Geri Al", width=56, height=28, corner_radius=4, font=font(10, bold=True),
                border_width=1, command=self._undo_last,
            ),
            BTN_INNER,
        )
        self.undo_btn.pack(side="left", padx=2)

        self.reset_btn = self.styled(
            ctk.CTkButton(
                self.actions_frame, text="Sıfırla", width=56, height=28, corner_radius=4, font=font(10, bold=True),
                border_width=1, command=self._confirm_manual_reset,
            ),
            BTN_INNER,
        )
        self.reset_btn.pack(side="left", padx=(2, 0))

    def _bind_events(self):
        self.bind("<FocusOut>", lambda e: self._ensure_topmost_lock())
        self.bind("<FocusIn>", lambda e: self._ensure_topmost_lock())
        self.bind("<space>", lambda e: self.start_pick())
        self.bind("<Return>", lambda e: self.start_pick())
        self.bind("<Escape>", lambda e: self._go_to_main())
        self.bind("<Control-z>", lambda e: self._undo_last())

        for w in (self.drag_grip, self.collapsed_drag, self.header_frame, self.card_frame, self.name_label, self.main_container):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)
            w.bind("<ButtonRelease-1>", self._end_drag)

    # =========================================================================
    # SERBEST TAŞIMA VE EKRAN KONUMU
    # =========================================================================
    def _load_or_compute_position(self, width_dp):
        saved_x = self.dm.get_setting("drawer_pos_x", None)
        saved_y = self.dm.get_setting("drawer_pos_y", None)
        if saved_x is not None and saved_y is not None:
            self.pos_x = int(saved_x)
            self.pos_y = int(saved_y)
            self._custom_pos_set = True
        else:
            self.pos_y = 20
            self.pos_x = self._get_x_for_width(width_dp)
            self._custom_pos_set = False

    def _start_drag(self, event):
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._win_orig_x = self.winfo_x()
        self._win_orig_y = self.winfo_y()
        self._is_dragging = True

    def _on_drag(self, event):
        if not self._is_dragging:
            return
        cur_w = self.collapsed_width if self._is_collapsed else self.full_width
        new_x = max(0, min(self._get_screen_width() - cur_w, self._win_orig_x + event.x_root - self._drag_start_x))
        new_y = max(0, min(self.winfo_screenheight() - self.panel_height, self._win_orig_y + event.y_root - self._drag_start_y))

        self.pos_x = new_x
        self.pos_y = new_y
        self._custom_pos_set = True
        self.geometry(f"{cur_w}x{self.panel_height}+{new_x}+{new_y}")

    def _end_drag(self, _event):
        self._is_dragging = False
        try:
            self.dm.set_setting("drawer_pos_x", self.pos_x)
            self.dm.set_setting("drawer_pos_y", self.pos_y)
        except Exception:
            pass

    def _get_screen_width(self):
        try:
            if sys.platform == "win32":
                sw = ctypes.windll.user32.GetSystemMetrics(0)
                if sw > 0:
                    return sw
        except Exception:
            pass
        return self.winfo_screenwidth()

    def _get_scaling(self):
        try:
            return ctk.ScalingTracker.get_window_scaling(self)
        except Exception:
            return 1.0

    def _get_x_for_width(self, width_dp):
        actual_px = int(round(width_dp * self._get_scaling()))
        return max(0, self._get_screen_width() - actual_px - self.margin_right)

    def deiconify(self):
        super().deiconify()
        cur_w = self.collapsed_width if self._is_collapsed else self.full_width
        if not self._custom_pos_set:
            self._load_or_compute_position(cur_w)
        self.geometry(f"{cur_w}x{self.panel_height}+{self.pos_x}+{self.pos_y}")
        self._ensure_topmost_lock()

    # =========================================================================
    # KAYAN ÇEKMECE ANİMASYONU (GİZLENME / GERİ ÇIKMA)
    # =========================================================================
    def toggle_collapse(self):
        if self._is_animating_slide:
            return

        self._is_animating_slide = True
        self._is_collapsed = not self._is_collapsed
        self.sound.play_tick()

        start_w = self.full_width if self._is_collapsed else self.collapsed_width
        target_w = self.collapsed_width if self._is_collapsed else self.full_width
        steps = 8
        cur_step = 0

        if self._is_collapsed:
            self.content_panel.pack_forget()

        anchor_right = self.pos_x + start_w

        def _place_at_width(w):
            if not self._custom_pos_set:
                self.pos_x = self._get_x_for_width(w)
            else:
                self.pos_x = max(0, anchor_right - w)
            self.geometry(f"{w}x{self.panel_height}+{self.pos_x}+{self.pos_y}")

        def _step_anim():
            nonlocal cur_step
            cur_step += 1
            eased = 1.0 - (1.0 - cur_step / steps) ** 2
            _place_at_width(int(start_w + (target_w - start_w) * eased))

            if cur_step < steps:
                self.after(16, _step_anim)
            else:
                _place_at_width(target_w)
                self._is_animating_slide = False
                if self._is_collapsed:
                    self.toggle_btn.configure(text="◀\n\nN\nO\nV\nA")
                else:
                    self.content_panel.pack(side="left", fill="both", expand=True, padx=(2, 4), pady=2)
                    self.toggle_btn.configure(text="▶\n\nN\nO\nV\nA")
                self._ensure_topmost_lock()

        _step_anim()

    # =========================================================================
    # ÖĞRENCİ SEÇİMİ VE TAM EKRAN DEFTER ANİMASYONU
    # =========================================================================
    def start_pick(self):
        if self._is_picking or self._is_collapsed:
            return

        active_class = self.dm.get_active_class()
        if not active_class:
            messagebox.showinfo("Bilgilendirme", "Lütfen önce yönetim panelinden bir sınıf tanımlayınız.")
            return

        all_students = self.dm.get_all_students(active_class)
        remaining = self.dm.get_remaining_students(active_class)
        if not all_students:
            messagebox.showinfo("Bilgilendirme", "Seçili sınıfta kayıtlı öğrenci bulunmamaktadır.")
            return

        if self._is_cycle_completed or not remaining:
            self._reset_and_start_new_cycle()
            return

        self._is_picking = True
        self.pick_button.configure(state="disabled", text="Seçiliyor...")
        self.sub_label.configure(text="")

        winner, is_exhausted = self.dm.pick_random(active_class)
        pool = all_students if len(all_students) > 1 else [winner]
        shuffles = 8
        base_delay = 45
        t = self.tm.get_theme()

        def _shuffle_step(step_idx):
            if step_idx < shuffles:
                self.name_label.configure(text=random.choice(pool), text_color=t["accent"])
                self.sound.play_tick()
                next_delay = base_delay + int((step_idx / shuffles) ** 2 * 50)
                self.after(next_delay, lambda: _shuffle_step(step_idx + 1))
            else:
                self._trigger_reveal(winner, is_exhausted)

        _shuffle_step(0)

    def _trigger_reveal(self, winner, is_exhausted):
        self._is_picking = False
        self._last_shown_student = winner
        self.sound.play_reveal()

        def _on_overlay_done():
            self._update_display_after_reveal(winner, is_exhausted)
            self.lift()
            self._ensure_topmost_lock()

        if self.dm.get_setting("paper_animation_enabled", True):
            NotebookRevealOverlay(
                master=self,
                student_name=winner,
                class_name=self.dm.get_active_class(),
                sound_player=self.sound,
                on_finish=_on_overlay_done,
            )
        else:
            _on_overlay_done()

    def _update_display_after_reveal(self, winner, is_exhausted):
        t = self.tm.get_theme()
        font_size = 12 if len(winner) > 22 else 13
        self.name_label.configure(text=winner, font=font(font_size, bold=True), text_color=t["text_primary"])

        active_class = self.dm.get_active_class()
        remaining = self.dm.get_remaining_students(active_class)
        active_total = len(self.dm.get_active_students(active_class))
        self.stats_label.configure(text=f"Kalan: {len(remaining)}/{active_total}", text_color=t["accent"])

        if is_exhausted:
            self._is_cycle_completed = True
            self.sub_label.configure(text="Liste Tamamlandı", text_color=t["success"])
            self._style_pick_button(t)
        else:
            self._is_cycle_completed = False
            self.sub_label.configure(text=f"Kalan: {len(remaining)} öğrenci", text_color=t["text_secondary"])
            self._style_pick_button(t)
        self._ensure_topmost_lock()

    def _style_pick_button(self, t):
        if self._is_cycle_completed:
            self.pick_button.configure(
                state="normal", text="Yeni Tur Başlat",
                fg_color=t["success"], hover_color=t["success_hover"], text_color="#ffffff",
            )
        else:
            self.pick_button.configure(
                state="normal", text="Öğrenci Seç",
                fg_color=t["accent"], hover_color=t["accent_hover"], text_color=t["accent_text"],
            )

    def _reset_and_start_new_cycle(self):
        self.dm.reset_picked(self.dm.get_active_class())
        self._last_shown_student = None
        self._is_cycle_completed = False
        self.refresh_display()
        t = self.tm.get_theme()
        self.name_label.configure(text="Yeni Tur Başlatıldı", text_color=t["success"], font=font(13, bold=True))
        self.sub_label.configure(text="Soru yöneltmek için butona basınız", text_color=t["text_secondary"])
        self._ensure_topmost_lock()

    def _undo_last(self):
        undone = self.dm.undo_pick(self.dm.get_active_class())
        t = self.tm.get_theme()
        if undone:
            self._last_shown_student = None
            self.refresh_display()
            self.name_label.configure(text=undone, text_color=t["text_primary"], font=font(13, bold=True))
            self.sub_label.configure(text="Seçim geri alındı (Listeye iade edildi)", text_color=t["text_secondary"])
        else:
            messagebox.showinfo("Bilgilendirme", "Geri alınabilecek aktif bir seçim bulunmamaktadır.")
        self._ensure_topmost_lock()

    def _confirm_manual_reset(self):
        active_class = self.dm.get_active_class()
        if messagebox.askyesno(
            "Tur Sıfırlama Onayı",
            f"'{active_class}' sınıfına ait soru sırasını baştan başlatmak istediğinizi onaylıyor musunuz?",
        ):
            self._reset_and_start_new_cycle()
        self._ensure_topmost_lock()

    def _on_class_changed(self, choice):
        self.dm.set_active_class(choice)
        self._last_shown_student = None
        self._is_cycle_completed = False
        t = self.tm.get_theme()
        self.name_label.configure(text="Öğrenci Seçimi Bekleniyor", text_color=t["text_primary"], font=font(13, bold=True))
        self.sub_label.configure(text="", text_color=t["text_secondary"])
        self.refresh_display()
        self._ensure_topmost_lock()

    def _go_to_main(self):
        self.withdraw()
        if self.on_return_to_main:
            self.on_return_to_main()

    def _toggle_pen(self):
        if self.on_toggle_pen:
            self.on_toggle_pen()

    def refresh_classes_dropdown(self):
        classes = self.dm.get_class_names() or ["Sınıf Yok"]
        self.class_dropdown.configure(values=classes)
        active = self.dm.get_active_class()
        if active in classes:
            self.class_var.set(active)
        elif classes and classes[0] != "Sınıf Yok":
            self.class_var.set(classes[0])
            self.dm.set_active_class(classes[0])
        else:
            self.class_var.set("Sınıf Yok")
        self._ensure_topmost_lock()

    def refresh_display(self):
        active_class = self.dm.get_active_class()
        self.class_var.set(active_class or "Sınıf Yok")
        t = self.tm.get_theme()

        if not active_class:
            self.stats_label.configure(text="0/0", text_color=t["text_secondary"])
            self.name_label.configure(text="Sınıf Tanımlayınız", text_color=t["danger"], font=font(12))
            self.sub_label.configure(text="Yönetim panelinden sınıf ekleyiniz", text_color=t["text_secondary"])
            self.pick_button.configure(state="disabled", text="Sınıf Yok", fg_color=t["bg_card_inner"], text_color=t["text_secondary"])
            self._is_cycle_completed = False
            self._ensure_topmost_lock()
            return

        all_students = self.dm.get_all_students(active_class)
        remaining = self.dm.get_remaining_students(active_class)
        active_total = len(self.dm.get_active_students(active_class))

        self.stats_label.configure(text=f"Kalan: {len(remaining)}/{active_total}", text_color=t["accent"])

        if not all_students:
            self.name_label.configure(text="Öğrenci Kaydı Yok", text_color=t["danger"], font=font(12))
            self.sub_label.configure(text="Yönetim panelinden öğrenci ekleyiniz", text_color=t["text_secondary"])
            self.pick_button.configure(state="disabled", text="Öğrenci Yok", fg_color=t["bg_card_inner"], text_color=t["text_secondary"])
            self._is_cycle_completed = False
        elif not remaining and active_total > 0:
            self._is_cycle_completed = True
            if not self._last_shown_student:
                self.name_label.configure(text="Sınıf Listesi Tamamlandı", text_color=t["success"], font=font(13, bold=True))
                self.sub_label.configure(text="Tüm öğrencilere soru yöneltilmiştir", text_color=t["text_secondary"])
            self._style_pick_button(t)
        else:
            self._is_cycle_completed = False
            self._style_pick_button(t)
        self._ensure_topmost_lock()

    def apply_theme(self):
        t = self.tm.get_theme()
        try:
            super().apply_theme()
            if self._is_cycle_completed:
                self.pick_button.configure(fg_color=t["success"], hover_color=t["success_hover"], text_color="#ffffff")
        except Exception:
            pass

    def destroy(self):
        try:
            self.tm.unregister_callback(self.apply_theme)
        except Exception:
            pass
        super().destroy()
