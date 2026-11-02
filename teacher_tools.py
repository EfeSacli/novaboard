from tkinter import messagebox
import customtkinter as ctk
import random

from vocabulary_game import VocabularyGameFrame
from ui_kit import (
    ThemedMixin, font, attach_context_menu,
    BTN_ACCENT, BTN_SUCCESS, BTN_INNER,
    CARD, SEGMENTED, TEXTBOX, OPTION_MENU_INNER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
)


class TeacherToolsFrame(ThemedMixin, ctk.CTkFrame):
    """
    Novaboard - Akıllı Tahta & Öğretmen Yardımcı Araçları Paneli.
    Ders Sayacı / Kronometre, Rastgele Grup Oluşturucu,
    İngilizce B1 Kelime Yarışması ve Hızlı Tahta Notu içerir.
    """

    def __init__(self, master, data_manager, sound_player, theme_manager):
        super().__init__(master, fg_color="transparent")
        self.dm = data_manager
        self.sound = sound_player
        self.tm = theme_manager

        self._timer_seconds_total = 300  # 5 dakika varsayılan
        self._timer_seconds_left = 300
        self._timer_running = False
        self._timer_after_id = None

        self._setup_ui()
        self.tm.register_callback(self.apply_theme)

    def _setup_ui(self):
        self.tab_selector = self.styled(
            ctk.CTkSegmentedButton(
                self,
                values=["Ders Sayacı", "Grup Oluşturucu", "Kelime Yarışması", "Ders Notları"],
                command=self._on_tab_changed,
                height=36,
                font=font(12, bold=True),
            ),
            SEGMENTED,
        )
        self.tab_selector.pack(fill="x", padx=4, pady=(6, 10))
        self.tab_selector.set("Ders Sayacı")

        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        self.timer_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.groups_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.vocab_frame = VocabularyGameFrame(
            self.content_container, data_manager=self.dm, sound_player=self.sound, theme_manager=self.tm
        )
        self.notes_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")

        self._setup_timer_ui()
        self._setup_groups_ui()
        self._setup_notes_ui()

        self.timer_frame.pack(fill="both", expand=True)

    def _on_tab_changed(self, choice):
        for f in (self.timer_frame, self.groups_frame, self.vocab_frame, self.notes_frame):
            f.pack_forget()

        if "Sayaç" in choice or "Sayacı" in choice:
            self.timer_frame.pack(fill="both", expand=True)
        elif "Grup" in choice:
            self.refresh_groups_class_info()
            self.groups_frame.pack(fill="both", expand=True)
        elif "Kelime" in choice:
            self.vocab_frame.refresh_class_and_students()
            self.vocab_frame.pack(fill="both", expand=True)
        elif "Not" in choice:
            self.notes_frame.pack(fill="both", expand=True)

    # =========================================================================
    # 1. DERS & SINAV GERİ SAYIM SAYACI (TIMER)
    # =========================================================================
    def _setup_timer_ui(self):
        self.timer_card = self.styled(ctk.CTkFrame(self.timer_frame, corner_radius=12, border_width=1), CARD)
        self.timer_card.pack(fill="both", expand=True, padx=4, pady=4)

        self.timer_display = self.styled(
            ctk.CTkLabel(self.timer_card, text="05:00", font=font(72, bold=True, family="Consolas")), TEXT_ACCENT
        )
        self.timer_display.pack(pady=(36, 12))

        self.timer_status = self.styled(
            ctk.CTkLabel(self.timer_card, text="Süre ayarlandı • Başlatmaya hazır", font=font(12)), TEXT_SECONDARY
        )
        self.timer_status.pack(pady=(0, 16))

        self.presets_frame = ctk.CTkFrame(self.timer_card, fg_color="transparent")
        self.presets_frame.pack(pady=8)

        self.preset_buttons = []
        for minutes in [1, 2, 3, 5, 10, 15, 20]:
            btn = self.styled(
                ctk.CTkButton(
                    self.presets_frame,
                    text=f"{minutes} dk",
                    width=58,
                    height=32,
                    corner_radius=6,
                    font=font(11, bold=True),
                    border_width=1,
                    command=lambda m=minutes: self._set_timer_minutes(m),
                ),
                BTN_INNER,
            )
            btn.pack(side="left", padx=3)
            self.preset_buttons.append(btn)

        self.timer_ctrl_frame = ctk.CTkFrame(self.timer_card, fg_color="transparent")
        self.timer_ctrl_frame.pack(pady=24)

        self.timer_start_btn = self.styled(
            ctk.CTkButton(
                self.timer_ctrl_frame, text="▶ Başlat", width=130, height=40, corner_radius=8,
                font=font(13, bold=True), command=self._toggle_timer,
            ),
            BTN_SUCCESS,
        )
        self.timer_start_btn.pack(side="left", padx=6)

        self.timer_add_btn = self.styled(
            ctk.CTkButton(
                self.timer_ctrl_frame, text="+1 Dk Ekle", width=96, height=40, corner_radius=8,
                font=font(11, bold=True), border_width=1, command=self._add_timer_minute,
            ),
            BTN_INNER,
        )
        self.timer_add_btn.pack(side="left", padx=6)

        self.timer_reset_btn = self.styled(
            ctk.CTkButton(
                self.timer_ctrl_frame, text="↺ Sıfırla", width=96, height=40, corner_radius=8,
                font=font(11, bold=True), border_width=1, command=self._reset_timer,
            ),
            BTN_INNER,
        )
        self.timer_reset_btn.pack(side="left", padx=6)

    def _cancel_timer(self):
        self._timer_running = False
        if self._timer_after_id:
            self.after_cancel(self._timer_after_id)
            self._timer_after_id = None

    def _set_timer_minutes(self, minutes):
        self._cancel_timer()
        self._timer_seconds_total = minutes * 60
        self._timer_seconds_left = self._timer_seconds_total
        self._update_timer_display()
        self.timer_start_btn.configure(text="▶ Başlat")
        self.timer_status.configure(text=f"{minutes} dakikalık süre hazırlandı")

    def _add_timer_minute(self):
        self._timer_seconds_left += 60
        self._update_timer_display()

    def _toggle_timer(self):
        if self._timer_running:
            self._cancel_timer()
            self.timer_start_btn.configure(text="▶ Devam Et")
            self.timer_status.configure(text="Sayaç duraklatıldı")
        else:
            if self._timer_seconds_left <= 0:
                self._timer_seconds_left = self._timer_seconds_total
            self._timer_running = True
            self.timer_start_btn.configure(text="⏸ Duraklat")
            self.timer_status.configure(text="Süre işliyor...")
            self._timer_tick()

    def _timer_tick(self):
        if not self._timer_running:
            return
        if self._timer_seconds_left > 0:
            self._timer_seconds_left -= 1
            self._update_timer_display()
            self._timer_after_id = self.after(1000, self._timer_tick)
        else:
            self._timer_running = False
            self.timer_start_btn.configure(text="▶ Yeniden Başlat")
            self.timer_status.configure(text="SÜRE TAMAMLANDI!")
            self.sound.play_timer_alarm()

    def _reset_timer(self):
        self._cancel_timer()
        self._timer_seconds_left = self._timer_seconds_total
        self._update_timer_display()
        self.timer_start_btn.configure(text="▶ Başlat")
        self.timer_status.configure(text="Sayaç sıfırlandı")

    def _update_timer_display(self):
        mins, secs = divmod(self._timer_seconds_left, 60)
        self.timer_display.configure(text=f"{mins:02d}:{secs:02d}")

    # =========================================================================
    # 2. RASTGELE GRUP OLUŞTURUCU (GROUP GENERATOR)
    # =========================================================================
    def _setup_groups_ui(self):
        self.groups_ctrl_card = self.styled(
            ctk.CTkFrame(self.groups_frame, corner_radius=10, border_width=1, height=54), CARD
        )
        self.groups_ctrl_card.pack(fill="x", padx=4, pady=(4, 8))
        self.groups_ctrl_card.pack_propagate(False)

        self.groups_class_label = self.styled(
            ctk.CTkLabel(self.groups_ctrl_card, text="Aktif Sınıf: -", font=font(12, bold=True)), TEXT_PRIMARY
        )
        self.groups_class_label.pack(side="left", padx=14)

        self.styled(
            ctk.CTkLabel(self.groups_ctrl_card, text="Grup Sayısı:", font=font(11)), TEXT_SECONDARY
        ).pack(side="left", padx=(10, 4))

        self.group_num_spin = self.styled(
            ctk.CTkOptionMenu(
                self.groups_ctrl_card,
                values=[f"{n} Grup" for n in range(2, 9)],
                width=100,
                height=30,
            ),
            OPTION_MENU_INNER,
        )
        self.group_num_spin.set("4 Grup")
        self.group_num_spin.pack(side="left", padx=4)

        self.make_groups_btn = self.styled(
            ctk.CTkButton(
                self.groups_ctrl_card, text="Grup Oluştur", height=30, font=font(11, bold=True),
                command=self._generate_random_groups,
            ),
            BTN_ACCENT,
        )
        self.make_groups_btn.pack(side="left", padx=10)

        self.copy_groups_btn = self.styled(
            ctk.CTkButton(
                self.groups_ctrl_card, text="Listeyi Kopyala", width=90, height=30, font=font(11), border_width=1,
                command=self._copy_groups_to_clipboard,
            ),
            BTN_INNER,
        )
        self.copy_groups_btn.pack(side="right", padx=14)

        self.groups_scroll = self.styled(
            ctk.CTkScrollableFrame(self.groups_frame, corner_radius=10, border_width=1), CARD
        )
        self.groups_scroll.pack(fill="both", expand=True, padx=4, pady=4)
        self._last_groups_text = ""

    def refresh_groups_class_info(self):
        cname = self.dm.get_active_class()
        active_count = len(self.dm.get_active_students(cname))
        self.groups_class_label.configure(text=f"Aktif Sınıf: {cname or 'Yok'} ({active_count} Katılımcı)")
        self.vocab_frame.refresh_class_and_students()

    def _generate_random_groups(self):
        cname = self.dm.get_active_class()
        if not cname:
            messagebox.showinfo("Bilgi", "Lütfen önce bir sınıf seçiniz.")
            return

        pool = list(self.dm.get_active_students(cname))
        if not pool:
            messagebox.showinfo("Bilgi", "Bu sınıfta aktif öğrenci kaydı bulunmamaktadır.")
            return

        random.shuffle(pool)
        num_groups = max(1, min(len(pool), int(self.group_num_spin.get().split()[0])))

        groups = [[] for _ in range(num_groups)]
        for idx, student in enumerate(pool):
            groups[idx % num_groups].append(student)

        for widget in self.groups_scroll.winfo_children():
            widget.destroy()

        t = self.tm.get_theme()
        copy_text_lines = [f"--- {cname} Grupları ---"]

        for g_idx, members in enumerate(groups, start=1):
            card = ctk.CTkFrame(
                self.groups_scroll, fg_color=t["bg_card_inner"], corner_radius=8, border_width=1, border_color=t["border"]
            )
            card.pack(fill="x", padx=6, pady=4)

            ctk.CTkLabel(
                card, text=f"{g_idx}. Grup ({len(members)} Öğrenci)", font=font(12, bold=True), text_color=t["accent"]
            ).pack(anchor="w", padx=12, pady=(8, 4))

            names_text = ", ".join(members)
            ctk.CTkLabel(
                card, text=names_text, font=font(11), text_color=t["text_primary"], wraplength=520, justify="left"
            ).pack(anchor="w", padx=12, pady=(0, 8))

            copy_text_lines.append(f"\n{g_idx}. Grup: {names_text}")

        self._last_groups_text = "\n".join(copy_text_lines)
        self.sound.play_reveal()

    def _copy_groups_to_clipboard(self):
        if not self._last_groups_text:
            messagebox.showinfo("Bilgi", "Kopyalanacak grup listesi bulunmamaktadır. Önce grup oluşturunuz.")
            return
        self.clipboard_clear()
        self.clipboard_append(self._last_groups_text)
        messagebox.showinfo("Başarılı", "Grup listesi panoya kopyalandı.")

    # =========================================================================
    # 3. HIZLI TAHTA NOTU (QUICK NOTES)
    # =========================================================================
    def _setup_notes_ui(self):
        self.notes_card = self.styled(ctk.CTkFrame(self.notes_frame, corner_radius=10, border_width=1), CARD)
        self.notes_card.pack(fill="both", expand=True, padx=4, pady=4)

        header_frame = ctk.CTkFrame(self.notes_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=12, pady=(10, 6))

        self.notes_title_lbl = self.styled(
            ctk.CTkLabel(header_frame, text="Akıllı Tahta Not Defteri ve Duyurular", font=font(13, bold=True)),
            TEXT_PRIMARY,
        )
        self.notes_title_lbl.pack(side="left")

        self.save_note_btn = self.styled(
            ctk.CTkButton(header_frame, text="Kaydet", width=70, height=28, font=font(10, bold=True),
                          command=self._save_notes),
            BTN_SUCCESS,
        )
        self.save_note_btn.pack(side="right", padx=4)

        self.clear_note_btn = self.styled(
            ctk.CTkButton(header_frame, text="Temizle", width=70, height=28, font=font(10), border_width=1,
                          command=self._clear_notes),
            BTN_INNER,
        )
        self.clear_note_btn.pack(side="right", padx=4)

        self.notes_textbox = self.styled(
            ctk.CTkTextbox(self.notes_card, font=font(12), corner_radius=8, border_width=1), TEXTBOX
        )
        self.notes_textbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        attach_context_menu(self.notes_textbox, self.tm)

        saved = self.dm.get_setting("quick_notes", "")
        if saved:
            self.notes_textbox.insert("1.0", saved)

    def _save_notes(self):
        self.dm.set_setting("quick_notes", self.notes_textbox.get("1.0", "end-1c"))
        messagebox.showinfo("Bilgi", "Tahta notu başarıyla kaydedildi.")

    def _clear_notes(self):
        self.notes_textbox.delete("1.0", "end")
        self.dm.set_setting("quick_notes", "")

    # =========================================================================
    # TEMA GÜNCELLEMESİ
    # =========================================================================
    def apply_theme(self):
        t = self.tm.get_theme()
        try:
            super().apply_theme()

            for child in self.groups_scroll.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    child.configure(fg_color=t["bg_card_inner"], border_color=t["border"])
                    for sub in child.winfo_children():
                        if isinstance(sub, ctk.CTkLabel):
                            sub.configure(text_color=t["text_primary"])

            self.vocab_frame.apply_theme()
        except Exception:
            pass
