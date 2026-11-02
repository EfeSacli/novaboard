import random
from tkinter import messagebox
import customtkinter as ctk
from datetime import datetime

from vocabulary_data import B1_VOCABULARY
from ui_kit import (
    ThemedMixin, font,
    BTN_ACCENT, BTN_SUCCESS, BTN_DANGER, BTN_CARD, BTN_INNER,
    CARD, CARD_INNER, resolve,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
)

OPTION_LABELS = ("A)", "B)", "C)", "D)")
PLACEHOLDER_STUDENTS = ("Öğrenci Seçiniz", "Öğrenci Kaydı Yok", "Tüm Sınıf Yarıştı (Sıfırla)")


class VocabularyGameFrame(ThemedMixin, ctk.CTkFrame):
    """
    Novaboard - İngilizce B1 Süreli Kelime Yarışması & Turnuva Modülü.
    Adil Kura Döngüsü: Bir kez yarışan öğrenci tüm sınıf kalkana veya liste sıfırlanana
    kadar tekrar çıkmaz. Eksi (-) puan destekli, 30/45/60 sn süreli, her cevapta
    anında otomatik soru geçişli ve sağ panel canlı liderlik tablosuna sahip yarışma aracı.
    """

    def __init__(self, master, data_manager, sound_player, theme_manager):
        super().__init__(master, fg_color="transparent")
        self.dm = data_manager
        self.sound = sound_player
        self.tm = theme_manager

        self.selected_duration = 45
        self.time_left = 45
        self.is_running = False
        self.answering_locked = False
        self._timer_id = None
        self._after_next_q = None

        self.active_student = ""
        self.contestant_queue = []
        self.queue_index = 0

        self.correct_count = 0
        self.wrong_count = 0
        self.streak = 0
        self.round_score = 0
        self.leaderboard_records = []

        self.deck = []
        self.current_q = None
        self.shuffled_options = []
        self.current_correct = ""

        self._setup_ui()
        self.refresh_class_and_students()
        self._prepare_idle_screen()
        self.tm.register_callback(self.apply_theme)

    # =========================================================================
    # ARAYÜZ KURULUMU
    # =========================================================================
    def _setup_ui(self):
        self.left_col = ctk.CTkFrame(self, fg_color="transparent")
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, 6), pady=0)

        self.right_col = self.styled(
            ctk.CTkFrame(self, width=290, corner_radius=12, border_width=1), CARD
        )
        self.right_col.pack(side="right", fill="y", padx=(6, 0), pady=0)
        self.right_col.pack_propagate(False)

        self._setup_top_controls()
        self._setup_status_bar()
        self._setup_question_area()
        self._setup_right_leaderboard()

    def _setup_top_controls(self):
        self.top_ctrl_card = self.styled(
            ctk.CTkFrame(self.left_col, corner_radius=10, border_width=1), CARD
        )
        self.top_ctrl_card.pack(fill="x", padx=2, pady=(0, 6))

        # Satır 1: Yarışmacı seçimi ve kura havuzu
        row1 = ctk.CTkFrame(self.top_ctrl_card, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(8, 4))

        self.styled(ctk.CTkLabel(row1, text="Yarışmacı:", font=font(12, bold=True)), TEXT_PRIMARY).pack(
            side="left", padx=(0, 6)
        )

        self.student_menu = self.styled(
            ctk.CTkOptionMenu(
                row1,
                values=["Öğrenci Seçiniz"],
                width=150,
                height=32,
                font=font(11, bold=True),
                command=self._on_student_dropdown_changed,
            ),
            fg_color="bg_card_inner", button_color="accent", button_hover_color="accent_hover", text_color="text_primary",
        )
        self.student_menu.pack(side="left", padx=(0, 6))

        self.btn_kura = self.styled(
            ctk.CTkButton(row1, text="Kura Çek", width=90, height=32, font=font(11, bold=True), border_width=1,
                          command=self._pick_single_kura),
            BTN_INNER,
        )
        self.btn_kura.pack(side="left", padx=(0, 6))

        self.btn_queue_modal = self.styled(
            ctk.CTkButton(row1, text="Çoklu Seçim", width=88, height=32, font=font(11, bold=True), border_width=1,
                          command=self._open_multi_select_modal),
            BTN_INNER,
        )
        self.btn_queue_modal.pack(side="left", padx=(0, 10))

        self.btn_reset_cycle = self.styled(
            ctk.CTkButton(row1, text="Listeyi Sıfırla", width=98, height=28, font=font(10, bold=True), border_width=1,
                          command=lambda: self._reset_competition_cycle(prompt=True)),
            BTN_INNER,
        )
        self.btn_reset_cycle.pack(side="right")

        self.cycle_badge_lbl = self.styled(
            ctk.CTkLabel(row1, text="Kalan: 0 / 0", font=font(11, bold=True)), TEXT_ACCENT
        )
        self.cycle_badge_lbl.pack(side="right", padx=(0, 8))

        # Satır 2: Süre ve Başlat/Bitir
        row2 = ctk.CTkFrame(self.top_ctrl_card, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(4, 8))

        self.styled(ctk.CTkLabel(row2, text="Süre:", font=font(12, bold=True)), TEXT_PRIMARY).pack(
            side="left", padx=(0, 8)
        )

        self.duration_seg = self.styled(
            ctk.CTkSegmentedButton(
                row2,
                values=["30 sn", "45 sn", "60 sn"],
                width=180,
                height=32,
                font=font(11, bold=True),
                command=self._on_duration_selected,
            ),
            fg_color="bg_card_inner", selected_color="accent", selected_hover_color="accent_hover",
            unselected_color="bg_card_inner", unselected_hover_color="bg_hover", text_color="text_primary",
        )
        self.duration_seg.set("45 sn")
        self.duration_seg.pack(side="left", padx=(0, 12))

        self.start_btn = self.styled(
            ctk.CTkButton(row2, text="Yarışmayı Başlat", width=140, height=34, font=font(12, bold=True),
                          command=self._toggle_game_round),
            BTN_SUCCESS,
        )
        self.start_btn.pack(side="right")

    def _setup_status_bar(self):
        self.status_bar_card = self.styled(
            ctk.CTkFrame(self.left_col, corner_radius=10, border_width=1, height=58), CARD
        )
        self.status_bar_card.pack(fill="x", padx=2, pady=(0, 6))
        self.status_bar_card.pack_propagate(False)

        stat_inner = ctk.CTkFrame(self.status_bar_card, fg_color="transparent")
        stat_inner.pack(fill="x", padx=14, pady=6)

        self.active_contestant_lbl = self.styled(
            ctk.CTkLabel(stat_inner, text="Yarışmacı: Belirlenmedi", font=font(13, bold=True)), TEXT_PRIMARY
        )
        self.active_contestant_lbl.pack(side="left")

        self.timer_display_lbl = ctk.CTkLabel(
            stat_inner, text="00:45", font=font(24, bold=True, family="Consolas"),
            text_color=self.tm.get_theme()["accent"],
        )
        self.timer_display_lbl.pack(side="left", expand=True)

        self.live_score_lbl = self.styled(
            ctk.CTkLabel(stat_inner, text="Doğru: 0   Yanlış: 0   Puan: 0", font=font(12, bold=True)), TEXT_PRIMARY
        )
        self.live_score_lbl.pack(side="right")

        self.time_progress = ctk.CTkProgressBar(
            self.status_bar_card, height=5, progress_color=self.tm.get_theme()["accent"]
        )
        self.time_progress.pack(fill="x", padx=6, side="bottom", pady=(0, 4))
        self.time_progress.set(1.0)

    def _setup_question_area(self):
        t = self.tm.get_theme()
        self.question_card = self.styled(
            ctk.CTkFrame(self.left_col, corner_radius=12, border_width=1), CARD
        )
        self.question_card.pack(fill="both", expand=True, padx=2, pady=(0, 6))

        self.curriculum_badge = self.styled(
            ctk.CTkLabel(self.question_card, text="KELİME YARIŞMASI", font=font(11, bold=True)), TEXT_ACCENT
        )
        self.curriculum_badge.pack(pady=(16, 4))

        self.word_label = self.styled(
            ctk.CTkLabel(self.question_card, text="Kelime Yarışması", font=font(36, bold=True)), TEXT_PRIMARY
        )
        self.word_label.pack(pady=(6, 2))

        self.type_label = self.styled(
            ctk.CTkLabel(self.question_card, text="Yarışmayı başlatmak için öğrenci seçiniz.", font=font(12)),
            TEXT_SECONDARY,
        )
        self.type_label.pack(pady=(0, 4))

        self.feedback_label = ctk.CTkLabel(self.question_card, text="", font=font(13, bold=True))
        self.feedback_label.pack(pady=(0, 10))

        self.options_container = ctk.CTkFrame(self.left_col, fg_color="transparent")
        self.options_container.pack(fill="both", expand=False, padx=2, pady=(0, 4))
        self.options_container.grid_columnconfigure((0, 1), weight=1)
        self.options_container.grid_rowconfigure((0, 1), weight=1)

        self.option_buttons = []
        for idx in range(4):
            btn = ctk.CTkButton(
                self.options_container,
                text=f"{OPTION_LABELS[idx]}  Seçenek",
                height=54,
                corner_radius=10,
                font=font(14, bold=True),
                border_width=1,
                command=lambda i=idx: self._on_option_clicked(i),
                **resolve(BTN_CARD, t),
            )
            btn.grid(row=idx // 2, column=idx % 2, padx=5, pady=5, sticky="nsew")
            self.option_buttons.append(btn)

    def _setup_right_leaderboard(self):
        header_frame = ctk.CTkFrame(self.right_col, fg_color="transparent", height=42)
        header_frame.pack(fill="x", padx=10, pady=(10, 4))

        self.styled(ctk.CTkLabel(header_frame, text="Puan Tablosu", font=font(14, bold=True)), TEXT_PRIMARY).pack(
            side="left"
        )

        self.btn_reset_lb = self.styled(
            ctk.CTkButton(header_frame, text="Temizle", width=68, height=26, font=font(10, bold=True), border_width=1,
                          command=self._reset_leaderboard),
            BTN_INNER,
        )
        self.btn_reset_lb.pack(side="right")

        self.lb_subtitle = self.styled(
            ctk.CTkLabel(self.right_col, text="Sınıf: - • 0 Yarışmacı", font=font(11)), TEXT_SECONDARY
        )
        self.lb_subtitle.pack(fill="x", padx=12, pady=(0, 6))

        self.lb_scroll = self.styled(
            ctk.CTkScrollableFrame(self.right_col, corner_radius=8), fg_color="bg_card"
        )
        self.lb_scroll.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.queue_box = self.styled(
            ctk.CTkFrame(self.right_col, corner_radius=8, border_width=1, height=90), CARD_INNER
        )
        self.queue_box.pack(fill="x", padx=8, pady=(0, 8))
        self.queue_box.pack_propagate(False)

        q_head = ctk.CTkFrame(self.queue_box, fg_color="transparent")
        q_head.pack(fill="x", padx=8, pady=(6, 2))

        self.styled(ctk.CTkLabel(q_head, text="Sıradaki Yarışmacılar", font=font(11, bold=True)), TEXT_PRIMARY).pack(
            side="left"
        )
        self.queue_count_lbl = self.styled(ctk.CTkLabel(q_head, text="(0)", font=font(11, bold=True)), TEXT_ACCENT)
        self.queue_count_lbl.pack(side="right")

        self.queue_names_lbl = self.styled(
            ctk.CTkLabel(
                self.queue_box, text="Sırada bekleyen öğrenci bulunmuyor.", font=font(10), justify="left", anchor="w"
            ),
            TEXT_SECONDARY,
        )
        self.queue_names_lbl.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        self._render_leaderboard()

    # =========================================================================
    # ADİL KURA DÖNGÜSÜ & ÖĞRENCİ YÖNETİMİ
    # =========================================================================
    def _get_class_valid_students(self, cname=None):
        return self.dm.get_active_students(cname)

    def _get_competed_students(self, cname=None):
        return self.dm.get_vocab_competed(cname)

    def _get_remaining_uncompeted_students(self, cname=None):
        valid = self._get_class_valid_students(cname)
        competed = set(self._get_competed_students(cname))
        return [s for s in valid if s not in competed]

    def _mark_student_competed(self, student_name, cname=None):
        self.dm.mark_vocab_competed(student_name, cname)
        self._update_cycle_status()

    def _reset_competition_cycle(self, cname=None, prompt=True):
        cname = cname or self.dm.get_active_class()
        if not cname or cname not in self.dm.data.get("classes", {}):
            return
        if prompt and not messagebox.askyesno(
            "Listeyi Sıfırla", f"'{cname}' sınıfı için yarışma listesi sıfırlansın mı?"
        ):
            return
        self.dm.reset_vocab_competed(cname)
        self.refresh_class_and_students()
        self.sound.play_reveal()

    def _update_cycle_status(self):
        cname = self.dm.get_active_class()
        total = len(self._get_class_valid_students(cname))
        rem = len(self._get_remaining_uncompeted_students(cname))
        self.cycle_badge_lbl.configure(text=f"Kalan: {rem} / {total}")

    def _set_single_contestant(self, student_name):
        self.active_student = student_name
        self.student_menu.set(student_name)
        self.active_contestant_lbl.configure(text=f"Yarışmacı: {student_name}")
        self.contestant_queue = [student_name]
        self.queue_index = 0
        self._update_queue_display()

    def refresh_class_and_students(self):
        cname = self.dm.get_active_class()
        valid_students = self._get_class_valid_students(cname)
        remaining = self._get_remaining_uncompeted_students(cname)

        self._update_cycle_status()
        self.lb_subtitle.configure(text=f"Sınıf: {cname or 'Yok'} • {len(self.leaderboard_records)} Kayıt")

        if remaining:
            self.student_menu.configure(values=remaining)
            if not self.active_student or self.active_student not in remaining:
                self.active_student = remaining[0]
                self.student_menu.set(self.active_student)
                self.active_contestant_lbl.configure(text=f"Yarışmacı: {self.active_student}")
        elif valid_students:
            self.student_menu.configure(values=["Tüm Sınıf Yarıştı (Sıfırla)"])
            self.student_menu.set("Tüm Sınıf Yarıştı (Sıfırla)")
            self.active_student = ""
            self.active_contestant_lbl.configure(text="Yarışmacı: Tamamlandı")
        else:
            self.student_menu.configure(values=["Öğrenci Kaydı Yok"])
            self.student_menu.set("Öğrenci Kaydı Yok")
            self.active_student = ""
            self.active_contestant_lbl.configure(text="Yarışmacı: -")

        self._update_queue_display()

    def _on_student_dropdown_changed(self, choice):
        if "Tüm Sınıf Yarıştı" in choice:
            self._reset_competition_cycle(prompt=True)
            return
        if choice and choice not in PLACEHOLDER_STUDENTS:
            self._set_single_contestant(choice)

    def _pick_single_kura(self):
        cname = self.dm.get_active_class()
        valid = self._get_class_valid_students(cname)
        remaining = self._get_remaining_uncompeted_students(cname)

        if not valid:
            messagebox.showinfo("Bilgi", "Aktif sınıfta kayıtlı öğrenci bulunamadı.")
            return

        if not remaining:
            if messagebox.askyesno(
                "Döngü Tamamlandı",
                f"'{cname}' sınıfındaki tüm öğrenciler ({len(valid)} kişi) yarıştı.\nKura listesi sıfırlansın mı?",
            ):
                self._reset_competition_cycle(prompt=False)
                remaining = self._get_remaining_uncompeted_students(cname)
            else:
                return

        self._set_single_contestant(random.choice(remaining))
        self.sound.play_reveal()

    def _open_multi_select_modal(self):
        cname = self.dm.get_active_class()
        valid = self._get_class_valid_students(cname)
        competed_set = set(self._get_competed_students(cname))
        remaining = self._get_remaining_uncompeted_students(cname)

        if not valid:
            messagebox.showinfo("Bilgi", "Seçilebilecek kayıtlı öğrenci bulunamadı.")
            return

        t = self.tm.get_theme()
        modal = ctk.CTkToplevel(self)
        modal.title(f"Yarışmacı Öğrencileri Belirle ({cname})")
        modal.geometry("440x540")
        modal.minsize(400, 460)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        try:
            modal.configure(fg_color=t["bg_main"])
        except Exception:
            pass

        title_box = ctk.CTkFrame(modal, fg_color=t["bg_card"], corner_radius=10)
        title_box.pack(fill="x", padx=12, pady=(12, 6))
        ctk.CTkLabel(
            title_box,
            text=f"👥 {cname} - Turnuva Listesi (Kalan: {len(remaining)}/{len(valid)})",
            font=font(13, bold=True),
            text_color=t["text_primary"],
        ).pack(padx=12, pady=10)

        quick_bar = ctk.CTkFrame(modal, fg_color="transparent")
        quick_bar.pack(fill="x", padx=12, pady=(0, 6))
        check_vars = {}

        def select_remaining():
            for st, var in check_vars.items():
                var.set(st not in competed_set)

        def select_all():
            for v in check_vars.values():
                v.set(True)

        def select_random_remaining(n):
            for v in check_vars.values():
                v.set(False)
            pool = remaining or valid
            for name in random.sample(pool, min(n, len(pool))):
                check_vars[name].set(True)

        ctk.CTkButton(
            quick_bar, text=f"Kalanları Seç ({len(remaining)})", height=28, width=110,
            font=ctk.CTkFont(size=10, weight="bold"), fg_color=t["accent"], hover_color=t["accent_hover"],
            text_color="#ffffff", command=select_remaining,
        ).pack(side="left", padx=2)
        for lbl, w, cmd in [
            ("Tümünü Seç", 75, select_all),
            ("🎲 Kalan 3", 70, lambda: select_random_remaining(3)),
            ("🎲 Kalan 5", 70, lambda: select_random_remaining(5)),
        ]:
            ctk.CTkButton(
                quick_bar, text=lbl, height=28, width=w, font=ctk.CTkFont(size=10),
                fg_color=t["bg_card"], hover_color=t["bg_hover"], text_color=t["text_primary"], command=cmd,
            ).pack(side="left", padx=2)

        scroll = ctk.CTkScrollableFrame(modal, fg_color=t["bg_card"], corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        for st in valid:
            is_competed = st in competed_set
            is_checked = (st in self.contestant_queue) if self.contestant_queue else (not is_competed)
            var = ctk.BooleanVar(value=is_checked)
            check_vars[st] = var

            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=3)
            ctk.CTkCheckBox(
                row,
                text=f"{st}{'  [✓ Yarıştı]' if is_competed else ''}",
                variable=var,
                font=font(12, slant="italic" if is_competed else "roman"),
                text_color=t["text_secondary"] if is_competed else t["text_primary"],
                fg_color=t["accent"],
                hover_color=t["accent_hover"],
            ).pack(side="left")

        def on_confirm():
            chosen_list = [st for st, var in check_vars.items() if var.get()]
            if not chosen_list:
                messagebox.showinfo("Uyarı", "Lütfen en az bir öğrenci seçiniz.", parent=modal)
                return
            self.contestant_queue = chosen_list
            self.queue_index = 0
            self.active_student = chosen_list[0]
            self.student_menu.set(self.active_student)
            self.active_contestant_lbl.configure(text=f"👤 Yarışmacı: {self.active_student} (1/{len(chosen_list)})")
            self._update_queue_display()
            self.sound.play_tick()
            modal.destroy()

        ctk.CTkButton(
            modal, text="✔️ Seçilen Öğrencileri Kuyruğa Ekle", height=38, font=font(12, bold=True),
            **resolve(BTN_ACCENT, t), command=on_confirm,
        ).pack(fill="x", padx=12, pady=(0, 12))

    def _update_queue_display(self):
        remaining_q = self.contestant_queue[self.queue_index:] if self.contestant_queue else []
        self.queue_count_lbl.configure(text=f"({len(remaining_q)})")

        if not remaining_q:
            self.queue_names_lbl.configure(text="Bekleyen öğrenci yok.\n'Çoklu Seçim' ile liste ekleyebilirsiniz.")
        else:
            lines = [f"{'🟢 Şu an:' if i == 0 else f'{i + 1}.'} {name}" for i, name in enumerate(remaining_q[:3])]
            if len(remaining_q) > 3:
                lines.append(f"... ve {len(remaining_q) - 3} kişi daha")
            self.queue_names_lbl.configure(text="\n".join(lines))

    # =========================================================================
    # SÜRE, SORU VE PUAN AKIŞI (- PUAN DESTEKLİ)
    # =========================================================================
    def _on_duration_selected(self, choice):
        if self.is_running:
            return
        self.selected_duration = 30 if "30" in choice else (60 if "60" in choice else 45)
        self.time_left = self.selected_duration
        self.timer_display_lbl.configure(text=f"⏱️ 00:{self.time_left:02d}")
        self.time_progress.set(1.0)

    def _prepare_idle_screen(self):
        t = self.tm.get_theme()
        self.word_label.configure(text="Yarışmaya Hazır mısın?", text_color=t["text_primary"])
        self.type_label.configure(
            text="Öğrenci belirleyip 'Yarışmayı Başlat' butonuna basınız. (Doğru: +10 Puan, Yanlış: -5 Puan)"
        )
        self.feedback_label.configure(text="")
        for idx, btn in enumerate(self.option_buttons):
            btn.configure(
                text=f"{OPTION_LABELS[idx]}  Başlatılınca Aktif Olur",
                fg_color=t["bg_card"],
                hover_color=t["bg_card"],
                text_color=t["text_secondary"],
                border_color=t["border"],
                state="disabled",
            )

    def _set_controls_state(self, state):
        for w in (self.duration_seg, self.student_menu, self.btn_kura, self.btn_queue_modal, self.btn_reset_cycle):
            w.configure(state=state)

    def _toggle_game_round(self):
        if self.is_running:
            self._finish_round()
        else:
            self._start_round()

    def _start_round(self):
        if not self.active_student or self.active_student in PLACEHOLDER_STUDENTS or "Tüm Sınıf Yarıştı" in self.active_student:
            self._pick_single_kura()
            if not self.active_student or self.active_student in PLACEHOLDER_STUDENTS:
                messagebox.showinfo("Uyarı", "Lütfen yarışacak öğrenciyi seçiniz.")
                return

        t = self.tm.get_theme()
        self.correct_count = 0
        self.wrong_count = 0
        self.streak = 0
        self.round_score = 0
        self.time_left = self.selected_duration
        self.is_running = True
        self.answering_locked = False

        self.deck = list(B1_VOCABULARY)
        random.shuffle(self.deck)

        self._set_controls_state("disabled")
        self.start_btn.configure(text="⏹️ Turu Bitir", **resolve(BTN_DANGER, t))

        total_in_queue = len(self.contestant_queue) or 1
        curr_num = (self.queue_index + 1) if self.contestant_queue else 1
        self.active_contestant_lbl.configure(text=f"🟢 Yarışıyor: {self.active_student} ({curr_num}/{total_in_queue})")

        self._update_live_score_display()
        self.timer_display_lbl.configure(text=f"⏱️ 00:{self.time_left:02d}", text_color=t["accent"])
        self.time_progress.configure(progress_color=t["accent"])
        self.time_progress.set(1.0)
        self.sound.play_reveal()

        self.next_question()
        if self._timer_id:
            self.after_cancel(self._timer_id)
        self._timer_id = self.after(1000, self._timer_tick)

    def _timer_tick(self):
        if not self.is_running:
            return

        self.time_left -= 1
        t = self.tm.get_theme()
        self.timer_display_lbl.configure(text=f"⏱️ 00:{self.time_left:02d}")
        self.time_progress.set(max(0.0, self.time_left / float(self.selected_duration)))

        if self.time_left <= 5:
            self.timer_display_lbl.configure(text_color=t["danger"])
            self.time_progress.configure(progress_color=t["danger"])
            self.sound.play_tick()
        elif self.time_left <= 15:
            self.timer_display_lbl.configure(text_color="#f59e0b")
            self.time_progress.configure(progress_color="#f59e0b")

        if self.time_left <= 0:
            self._finish_round()
        else:
            self._timer_id = self.after(1000, self._timer_tick)

    def next_question(self):
        if not self.is_running:
            return

        self.answering_locked = False
        t = self.tm.get_theme()

        if not self.deck:
            self.deck = list(B1_VOCABULARY)
            random.shuffle(self.deck)

        self.current_q = self.deck.pop()
        self.word_label.configure(text=self.current_q["word"], text_color=t["text_primary"])
        self.type_label.configure(text=f"[ {self.current_q['type']} ]", text_color=t["text_secondary"])
        self.feedback_label.configure(text="")

        self.current_correct = self.current_q["options"][0]
        opts = list(self.current_q["options"])
        random.shuffle(opts)
        self.shuffled_options = opts

        btn_style = resolve(BTN_CARD, t)
        for idx, btn in enumerate(self.option_buttons):
            btn.configure(text=f"{OPTION_LABELS[idx]}  {opts[idx]}", state="normal", **btn_style)

    def _on_option_clicked(self, chosen_idx):
        if not self.is_running or self.answering_locked:
            return

        self.answering_locked = True
        t = self.tm.get_theme()
        chosen_text = self.shuffled_options[chosen_idx]
        correct_text = self.current_correct

        if chosen_text == correct_text:
            self.correct_count += 1
            self.streak += 1
            streak_bonus = 2 if self.streak >= 3 else 0
            gained = 10 + streak_bonus
            self.round_score += gained

            self.option_buttons[chosen_idx].configure(**resolve(BTN_SUCCESS, t))
            self.feedback_label.configure(text=f"✅ Doğru! (+{gained})", text_color=t["success"])
            self.sound.play_reveal()
        else:
            self.wrong_count += 1
            self.streak = 0
            self.round_score -= 5

            self.option_buttons[chosen_idx].configure(**resolve(BTN_DANGER, t))
            for idx, opt in enumerate(self.shuffled_options):
                if opt == correct_text:
                    self.option_buttons[idx].configure(**resolve(BTN_SUCCESS, t))

            self.feedback_label.configure(
                text=f"❌ Yanlış! (-5 Puan)  Doğru Cevap: {correct_text}", text_color=t["danger"]
            )
            self.sound.play_tick()

        self._update_live_score_display()

        if self._after_next_q:
            self.after_cancel(self._after_next_q)
        self._after_next_q = self.after(350, self.next_question)

    def _update_live_score_display(self):
        t = self.tm.get_theme()
        streak_str = f" 🔥 {self.streak}" if self.streak > 1 else ""
        score_color = (
            t["danger"] if self.round_score < 0 else (t["success"] if self.round_score > 0 else t["text_primary"])
        )
        self.live_score_lbl.configure(
            text=f"✅ {self.correct_count}   ❌ {self.wrong_count}{streak_str}   ⭐ {self.round_score} P",
            text_color=score_color,
        )

    # =========================================================================
    # TUR BİTİMİ & KURA DÖNGÜSÜNE İŞLEME
    # =========================================================================
    def _finish_round(self, early_stop=False):
        if not self.is_running:
            return

        self.is_running = False
        for attr in ("_timer_id", "_after_next_q"):
            tid = getattr(self, attr)
            if tid:
                self.after_cancel(tid)
                setattr(self, attr, None)

        t = self.tm.get_theme()
        finished_student = self.active_student
        cname = self.dm.get_active_class()

        for btn in self.option_buttons:
            btn.configure(state="disabled")
        self._set_controls_state("normal")
        self.sound.play_timer_alarm()

        self._mark_student_competed(finished_student, cname)

        self.leaderboard_records.append({
            "student": finished_student,
            "score": self.round_score,
            "correct": self.correct_count,
            "wrong": self.wrong_count,
            "duration": self.selected_duration,
            "time_str": datetime.now().strftime("%H:%M"),
        })
        self.leaderboard_records.sort(key=lambda r: (r["score"], r["correct"], -r["wrong"]), reverse=True)
        self._render_leaderboard()

        has_next = bool(self.contestant_queue and self.queue_index + 1 < len(self.contestant_queue))
        if has_next:
            self.queue_index += 1
            self.active_student = self.contestant_queue[self.queue_index]
            self.student_menu.set(self.active_student)

        self._update_queue_display()
        remaining_in_class = self._get_remaining_uncompeted_students(cname)
        score_sign = "+" if self.round_score > 0 else ""

        if has_next:
            next_student = self.active_student
            self.word_label.configure(
                text=f"Süre Doldu • Skor: {score_sign}{self.round_score}",
                text_color=t["danger"] if self.round_score < 0 else t["accent"],
            )
            self.type_label.configure(
                text=f"{finished_student} tamamladı. (Doğru: {self.correct_count}, Yanlış: {self.wrong_count})\n"
                f"Sıradaki: {next_student}"
            )
            self.start_btn.configure(text=f"{next_student} İçin Başlat", **resolve(BTN_SUCCESS, t))
            self.active_contestant_lbl.configure(
                text=f"Sıradaki: {next_student} ({self.queue_index + 1}/{len(self.contestant_queue)})"
            )
        else:
            top = self.leaderboard_records[0]
            self.word_label.configure(text="TUR TAMAMLANDI", text_color=t["success"])
            if not remaining_in_class:
                self.type_label.configure(
                    text=f"Tüm öğrenciler tamamladı. Lider: {top['student']} ({top['score']} Puan)\n"
                    f"Yeni tur için 'Listeyi Sıfırla' butonuna tıklayabilirsiniz."
                )
            else:
                self.type_label.configure(
                    text=f"{finished_student}: {score_sign}{self.round_score} Puan "
                    f"(Doğru: {self.correct_count}, Yanlış: {self.wrong_count}) • Kalan: {len(remaining_in_class)} Kişi"
                )

            self.start_btn.configure(text="Yeni Tur Başlat", **resolve(BTN_SUCCESS, t))
            self.active_contestant_lbl.configure(text=f"Tamamlandı: {finished_student}")
            self.sound.play_complete_fanfare()

            if remaining_in_class:
                self.active_student = remaining_in_class[0]
                self.student_menu.set(self.active_student)

    # =========================================================================
    # PUAN TABLOSU (LEADERBOARD)
    # =========================================================================
    def _render_leaderboard(self):
        for child in self.lb_scroll.winfo_children():
            child.destroy()

        t = self.tm.get_theme()
        cname = self.dm.get_active_class()
        self.lb_subtitle.configure(text=f"Sınıf: {cname or 'Yok'} • {len(self.leaderboard_records)} Kayıt")

        if not self.leaderboard_records:
            ctk.CTkLabel(
                self.lb_scroll, text="Henüz yarışma kaydı bulunmuyor.", font=font(11),
                text_color=t["text_muted"], justify="center",
            ).pack(pady=28)
            return

        for idx, rec in enumerate(self.leaderboard_records):
            is_top = idx == 0
            row_card = ctk.CTkFrame(
                self.lb_scroll,
                fg_color=t["bg_card_inner"],
                corner_radius=8,
                border_width=1,
                border_color=t["accent"] if is_top else t["border"],
            )
            row_card.pack(fill="x", pady=3)

            inner = ctk.CTkFrame(row_card, fg_color="transparent")
            inner.pack(fill="x", padx=8, pady=6)

            ctk.CTkLabel(
                inner,
                text=f"{idx + 1}. {rec['student']}",
                font=font(12, bold=(idx < 3)),
                text_color=t["accent"] if is_top else t["text_primary"],
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

            score_val = rec["score"]
            score_color = t["danger"] if score_val < 0 else (t["success"] if is_top else t["text_primary"])
            ctk.CTkLabel(
                inner, text=f"{'+' if score_val > 0 else ''}{score_val} P", font=font(12, bold=True),
                text_color=score_color,
            ).pack(side="right")

            ctk.CTkLabel(
                row_card,
                text=f"Doğru: {rec['correct']}   Yanlış: {rec['wrong']}   Süre: {rec['duration']} sn",
                font=font(10),
                text_color=t["text_secondary"],
                anchor="w",
            ).pack(fill="x", padx=10, pady=(0, 4))

    def _reset_leaderboard(self):
        if self.leaderboard_records and messagebox.askyesno("Onay", "Puan tablosundaki tüm dereceler sıfırlansın mı?"):
            self.leaderboard_records.clear()
            self._render_leaderboard()
            self.sound.play_tick()

    # =========================================================================
    # TEMA UYGULAMA
    # =========================================================================
    def apply_theme(self):
        t = self.tm.get_theme()
        try:
            super().apply_theme()

            if self.is_running:
                self.start_btn.configure(**resolve(BTN_DANGER, t))
            if self.time_left > 15:
                self.timer_display_lbl.configure(text_color=t["accent"])
                self.time_progress.configure(progress_color=t["accent"])

            if not self.answering_locked and self.is_running:
                btn_style = resolve(BTN_CARD, t)
                for btn in self.option_buttons:
                    btn.configure(**btn_style)
            elif not self.is_running:
                for btn in self.option_buttons:
                    btn.configure(
                        fg_color=t["bg_card"],
                        hover_color=t["bg_card"],
                        text_color=t["text_secondary"],
                        border_color=t["border"],
                    )

            self._render_leaderboard()
        except Exception:
            pass
