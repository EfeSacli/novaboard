import sys
import math
import random
from datetime import datetime
import tkinter as tk
import customtkinter as ctk


class NotebookRevealOverlay(ctk.CTkToplevel):
    """
    Novaboard - Kareli Defter Yaprağı ve Çöp Kovası Animasyon Ekranı.
    Öğrenci seçildiğinde tam ekranda dev kareli defter yaprağında öğrencinin adını gösterir.
    Aşamalar: paper_enter -> display -> bin_in -> crumple -> toss -> impact -> bin_out -> kapanış.
    """

    def __init__(self, master, student_name, class_name, sound_player, on_finish=None):
        super().__init__(master)
        self.student_name = student_name
        self.class_name = class_name or "Sınıf"
        self.sound = sound_player
        self.on_finish = on_finish
        self._is_closing = False

        self.overrideredirect(True)
        self.attributes("-topmost", True)

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{screen_w}x{screen_h}+0+0")

        self.transparent_key = "#000001"
        if sys.platform == "win32":
            try:
                self.attributes("-transparentcolor", self.transparent_key)
            except Exception:
                pass
        else:
            self.transparent_key = "#0f172a"
            try:
                self.attributes("-alpha", 0.92)
            except Exception:
                pass
        self.configure(fg_color=self.transparent_key)

        self.canvas = tk.Canvas(self, width=screen_w, height=screen_h, bg=self.transparent_key, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.screen_w = screen_w
        self.screen_h = screen_h
        self.res_scale = max(0.75, min(2.5, min(screen_w / 1920.0, screen_h / 1080.0)))
        self.font_corr = getattr(ctk.ScalingTracker, "font_size_correction", 1.0)

        # Defter boyutları ve hedef konumu (ekran boyutuna göre otomatik oranlanır)
        self.paper_w = int(min(1140 * self.res_scale, max(640 * self.res_scale, screen_w * 0.76)))
        self.paper_h = int(min(680 * self.res_scale, max(420 * self.res_scale, screen_h * 0.68)))
        self.target_paper_x = (screen_w - self.paper_w) // 2
        self.target_paper_y = (screen_h - self.paper_h) // 2
        self.paper_x = self.target_paper_x
        self.paper_y = self.target_paper_y - int(90 * self.res_scale)

        # Çöp kovası boyutları ve hedef konumu
        self.bin_w = int(175 * self.res_scale)
        self.bin_h = int(215 * self.res_scale)
        self.bin_target_x = screen_w - self.bin_w - int(75 * self.res_scale)
        self.bin_target_y = screen_h - self.bin_h - int(40 * self.res_scale)
        self.bin_current_y = screen_h + int(80 * self.res_scale)
        self.bin_bounce = 0

        self.particles = []
        self._init_particles()
        self.splash_particles = []

        self.phase = "paper_enter"
        self.crumple_factor = 0.0
        self.ball_x = self.target_paper_x + self.paper_w // 2
        self.ball_y = self.target_paper_y + self.paper_h // 2
        self.ball_rot = 0
        self.trail_positions = []

        for key in ("<Escape>", "<space>", "<Return>"):
            self.bind(key, lambda e: self.skip_and_close())
        self.canvas.bind("<Button-1>", lambda e: self.skip_and_close())

        self._draw_scene()
        self.after(20, self._step_paper_enter)

    # =========================================================================
    # PARÇACIK SİSTEMLERİ
    # =========================================================================
    def _init_particles(self):
        cx = self.target_paper_x + self.paper_w // 2
        cy = self.target_paper_y + self.paper_h // 2
        colors = ["#0284c7", "#38bdf8", "#10b981", "#60a5fa", "#34d399", "#6366f1", "#f43f5e"]
        symbols = ["✦", "★", "•", "✦", "✦"]
        self.particles = []
        for _ in range(28):
            ang = random.uniform(0, 2 * math.pi)
            dist = random.uniform(50, 280)
            speed = random.uniform(2.5, 6.0)
            self.particles.append({
                "x": cx + dist * 0.25 * math.cos(ang),
                "y": cy + dist * 0.25 * math.sin(ang),
                "vx": math.cos(ang) * speed,
                "vy": math.sin(ang) * speed - 0.5,
                "color": random.choice(colors),
                "char": random.choice(symbols),
                "size": random.randint(9, 16),
                "life": 1.0,
                "decay": random.uniform(0.015, 0.035),
            })

    def _init_splash_particles(self):
        bx = self.bin_target_x + self.bin_w // 2
        by = self.bin_target_y + 18
        colors = ["#38bdf8", "#0284c7", "#4ade80", "#ffffff"]
        self.splash_particles = []
        for _ in range(16):
            ang = random.uniform(math.pi * 1.05, math.pi * 1.95)
            speed = random.uniform(3.5, 7.5)
            self.splash_particles.append({
                "x": bx,
                "y": by,
                "vx": math.cos(ang) * speed,
                "vy": math.sin(ang) * speed,
                "color": random.choice(colors),
                "size": random.randint(10, 15),
                "life": 1.0,
                "char": random.choice(["✦", "★", "•"]),
            })

    def _cfont(self, pt_size: int, bold: bool = True):
        px = max(10, int(round(pt_size * 1.33 * self.res_scale * self.font_corr)))
        return ("Segoe UI", -px, "bold") if bold else ("Segoe UI", -px)

    def _draw_particle_list(self, particle_list):
        for p in particle_list:
            if p["life"] > 0:
                self.canvas.create_text(
                    p["x"], p["y"], text=p["char"], font=self._cfont(p["size"], bold=True), fill=p["color"]
                )

    # =========================================================================
    # SAHNE ÇİZİMİ
    # =========================================================================
    def _draw_scene(self):
        self.canvas.delete("all")
        sw = self.screen_w
        s = self.res_scale

        if self.phase in ("paper_enter", "display", "bin_in"):
            self._draw_notebook_paper(self.paper_x, self.paper_y, self.paper_w, self.paper_h)
        elif self.phase == "crumple":
            self._draw_crumpling_paper()
        elif self.phase in ("toss", "impact", "bin_out"):
            self._draw_paper_ball(self.ball_x, self.ball_y, self.ball_rot)

        if self.phase in ("paper_enter", "display"):
            self._draw_particle_list(self.particles)

        if self.phase in ("bin_in", "crumple", "toss", "impact", "bin_out"):
            self._draw_trash_bin(self.bin_target_x, self.bin_current_y + self.bin_bounce, self.bin_w, self.bin_h)

        if self.phase in ("impact", "bin_out") and self.splash_particles:
            self._draw_particle_list(self.splash_particles)

        # Sağ üst köşe atlama butonu
        btn_w, btn_h = int(190 * s), int(34 * s)
        bx1, by1 = sw - btn_w - int(20 * s), int(16 * s)
        self.canvas.create_rectangle(bx1, by1, bx1 + btn_w, by1 + btn_h, fill="#1e293b", outline="#475569", width=1.5)
        self.canvas.create_text(bx1 + btn_w // 2, by1 + btn_h // 2, text="✕ Geç / Kapat (ESC)", font=self._cfont(10), fill="#f8fafc")

    def _draw_notebook_paper(self, px, py, pw, ph):
        px, py, pw, ph = int(px), int(py), int(pw), int(ph)
        s = self.res_scale

        for off_x, off_y, col in [(16, 16, "#0f172a"), (12, 12, "#1e293b"), (8, 8, "#334155"), (4, 4, "#475569")]:
            ox, oy = int(off_x * s), int(off_y * s)
            self.canvas.create_rectangle(px + ox, py + oy, px + pw + ox, py + ph + oy, fill=col, outline="")

        self.canvas.create_rectangle(px, py, px + pw, py + ph, fill="#fdfcf7", outline="#cbd5e1", width=2)

        for hy in (py + int(80 * s), py + ph // 2, py + ph - int(80 * s)):
            self.canvas.create_oval(
                px + int(20 * s), hy - int(12 * s), px + int(48 * s), hy + int(12 * s),
                fill=self.transparent_key, outline="#94a3b8", width=2
            )
            self.canvas.create_line(px + int(10 * s), hy, px + int(28 * s), hy, fill="#64748b", width=3)

        self.canvas.create_line(px + int(58 * s), py + int(8 * s), px + int(58 * s), py + ph - int(8 * s), fill="#94a3b8", dash=(4, 5), width=1.5)

        margin_x = px + int(76 * s)
        self.canvas.create_line(margin_x, py, margin_x, py + ph, fill="#ef4444", width=2.5)
        self.canvas.create_line(margin_x + int(3 * s), py, margin_x + int(3 * s), py + ph, fill="#fca5a5", width=1.0)

        grid_step = max(16, int(24 * s))
        for gx in range(margin_x + grid_step, px + pw - int(12 * s), grid_step):
            self.canvas.create_line(gx, py + int(14 * s), gx, py + ph - int(14 * s), fill="#e2e8f0", width=1)
        for gy in range(py + int(26 * s), py + ph - int(14 * s), grid_step):
            self.canvas.create_line(margin_x, gy, px + pw - int(12 * s), gy, fill="#e2e8f0", width=1)

        today_str = datetime.now().strftime("%d.%m.%Y")
        self.canvas.create_text(
            px + pw - int(24 * s), py + int(22 * s), text=f"✦ {self.class_name.upper()} • {today_str} ✦",
            font=self._cfont(10), fill="#64748b", anchor="e",
        )
        self.canvas.create_text(
            margin_x + int(16 * s), py + int(22 * s), text="📓 DERS İÇİ SORU & ETKİNLİK DEFTERİ",
            font=self._cfont(9), fill="#94a3b8", anchor="w",
        )

        name_center_x = (margin_x + px + pw) // 2
        name_center_y = py + (ph // 2) - int(15 * s)
        name_len = len(self.student_name)
        font_size = 54 if name_len <= 12 else (42 if name_len <= 20 else 32)

        self.canvas.create_text(
            name_center_x + 2, name_center_y + 2, text=self.student_name,
            font=self._cfont(font_size), fill="#94a3b8",
        )
        self.canvas.create_text(
            name_center_x, name_center_y, text=self.student_name,
            font=self._cfont(font_size), fill="#0f172a",
        )

        badge_y = name_center_y + int((font_size // 2 + 34) * s)
        bw_half = int(175 * s)
        bh_half = int(16 * s)
        self.canvas.create_rectangle(
            name_center_x - bw_half, badge_y - bh_half, name_center_x + bw_half, badge_y + bh_half,
            fill="#0369a1", outline="#38bdf8", width=2,
        )
        self.canvas.create_text(
            name_center_x, badge_y, text="🎯 Sıradaki Soru Bu Öğrencimizde 🎯",
            font=self._cfont(11), fill="#ffffff",
        )

    def _draw_crumpling_paper(self):
        f = self.crumple_factor
        cx = self.target_paper_x + self.paper_w // 2
        cy = self.target_paper_y + self.paper_h // 2
        cur_w = self.paper_w * (1.0 - f * 0.88)
        cur_h = self.paper_h * (1.0 - f * 0.88)

        jx = math.sin(f * 18) * 8 * (1.0 - f)
        jy = math.cos(f * 18) * 6 * (1.0 - f)

        p1 = (cx - cur_w / 2 + 20 * f * math.sin(f * 6) + jx, cy - cur_h / 2 + 15 * f + jy)
        p2 = (cx + cur_w / 2 - 25 * f + jx, cy - cur_h / 2 + 20 * f * math.cos(f * 5) + jy)
        p3 = (cx + cur_w / 2 - 10 * f + jx, cy + cur_h / 2 - 20 * f + jy)
        p4 = (cx - cur_w / 2 + 30 * f * math.cos(f * 7) + jx, cy + cur_h / 2 - 15 * f + jy)

        facets = [
            (p1, p2, "#f8fafc", "#cbd5e1"),
            (p2, p3, "#e2e8f0", "#94a3b8"),
            (p3, p4, "#cbd5e1", "#94a3b8"),
            (p4, p1, "#f1f5f9", "#cbd5e1"),
        ]
        for a, b, fill_c, out_c in facets:
            self.canvas.create_polygon(a[0], a[1], b[0], b[1], cx, cy, fill=fill_c, outline=out_c, width=1.5)

        if f > 0.15:
            for pt, col in [(p1, "#64748b"), (p2, "#64748b"), (p3, "#94a3b8"), (p4, "#94a3b8")]:
                self.canvas.create_line(pt[0], pt[1], cx, cy, fill=col, width=2)
            self.canvas.create_line(cx - 25 * f, cy - 12, cx + 25 * f, cy + 18, fill="#ef4444", width=2)

    def _draw_paper_ball(self, x, y, rot):
        r = 34
        if self.phase == "toss" and self.trail_positions:
            for idx, (tx, ty, _trot) in enumerate(self.trail_positions):
                alpha_r = int(r * (0.55 + 0.15 * idx))
                self.canvas.create_oval(tx - alpha_r, ty - alpha_r, tx + alpha_r, ty + alpha_r, fill="#334155", outline="")

        points = []
        for i in range(12):
            ang = math.radians(rot + i * 30)
            rad = r + (7 if i % 2 == 0 else -6) + (3 if i % 3 == 0 else 0)
            points.extend([x + rad * math.cos(ang), y + rad * math.sin(ang)])

        self.canvas.create_oval(x - r + 6, y - r + 8, x + r + 6, y + r + 8, fill="#020617", outline="")
        self.canvas.create_polygon(points, fill="#fdfbf7", outline="#94a3b8", width=2)

        for k in range(5):
            ang1 = math.radians(rot + k * 72)
            ang2 = math.radians(rot + k * 72 + 36)
            self.canvas.create_line(x, y, x + (r - 6) * math.cos(ang1), y + (r - 6) * math.sin(ang1), fill="#cbd5e1", width=2)
            self.canvas.create_line(
                x + 6 * math.cos(ang2), y + 6 * math.sin(ang2),
                x + (r - 10) * math.cos(ang2), y + (r - 10) * math.sin(ang2),
                fill="#38bdf8" if k % 2 == 0 else "#f87171", width=1.5,
            )

    def _draw_trash_bin(self, bx, by, bw, bh):
        bx, by, bw, bh = int(bx), int(by), int(bw), int(bh)
        self.canvas.create_oval(bx - 12, by + bh - 14, bx + bw + 12, by + bh + 14, fill="#020617", outline="")

        inset = 20
        body_pts = [bx, by + 20, bx + bw, by + 20, bx + bw - inset, by + bh, bx + inset, by + bh]
        self.canvas.create_polygon(body_pts, fill="#0f172a", outline="#475569", width=2)

        for step in range(1, 5):
            ratio = step / 5.0
            ly = by + 20 + int((bh - 20) * ratio)
            self.canvas.create_line(bx + inset * ratio, ly, bx + bw - inset * ratio, ly, fill="#334155", width=1.5)

        center_x = bx + bw // 2
        center_y = by + bh // 2 + int(10 * self.res_scale)
        self.canvas.create_text(center_x, center_y, text="♻", font=self._cfont(32, bold=False), fill="#38bdf8")
        self.canvas.create_text(center_x, center_y + int(38 * self.res_scale), text="NOVABOARD", font=self._cfont(8), fill="#94a3b8")

        self.canvas.create_oval(bx, by, bx + bw, by + 40, fill="#020617", outline="#94a3b8", width=3)
        self.canvas.create_arc(bx + 4, by + 2, bx + bw - 4, by + 38, start=180, extent=180, style="arc", outline="#f8fafc", width=2)

    # =========================================================================
    # ANİMASYON AŞAMALARI
    # =========================================================================
    def _run_frames(self, total_frames, delay_ms, on_frame, on_done):
        """Ortak kare zamanlayıcısı: her karede on_frame(step, progress) çağırır ve sahneyi yeniler."""
        step = 0

        def _tick():
            nonlocal step
            if self._is_closing:
                return
            step += 1
            on_frame(step, step / total_frames)
            self._draw_scene()
            if step < total_frames:
                self.after(delay_ms, _tick)
            else:
                on_done()

        _tick()

    def _step_paper_enter(self):
        start_y = self.target_paper_y - 80

        def _frame(_step, progress):
            eased = 1.0 - math.pow(1.0 - progress, 3)
            bounce = math.sin(progress * math.pi) * 8 * (1.0 - progress)
            self.paper_y = start_y + eased * (self.target_paper_y - start_y) - bounce
            for p in self.particles:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["life"] = max(0.0, p["life"] - p["decay"])

        def _done():
            self.paper_y = self.target_paper_y
            self.phase = "display"
            self.after(1600, self._step_bin_slide_up)

        self._run_frames(15, 20, _frame, _done)

    def _step_bin_slide_up(self):
        if self._is_closing:
            return
        self.phase = "bin_in"
        start_y = self.screen_h + 80

        def _frame(_step, progress):
            eased = 1.0 - math.pow(1.0 - progress, 2)
            self.bin_current_y = start_y - eased * (start_y - self.bin_target_y)

        def _done():
            self.bin_current_y = self.bin_target_y
            self.after(120, self._step_crumple_paper)

        self._run_frames(14, 20, _frame, _done)

    def _step_crumple_paper(self):
        if self._is_closing:
            return
        self.phase = "crumple"
        self.sound.play_crumple()

        def _frame(_step, progress):
            self.crumple_factor = progress

        def _done():
            self.crumple_factor = 1.0
            self.after(80, self._step_toss_ball)

        self._run_frames(16, 22, _frame, _done)

    def _step_toss_ball(self):
        if self._is_closing:
            return
        self.phase = "toss"
        start_x = self.target_paper_x + self.paper_w // 2
        start_y = self.target_paper_y + self.paper_h // 2
        target_x = self.bin_target_x + self.bin_w // 2
        target_y = self.bin_target_y + 20
        self.trail_positions = []

        def _frame(_step, t):
            self.trail_positions.append((self.ball_x, self.ball_y, self.ball_rot))
            if len(self.trail_positions) > 3:
                self.trail_positions.pop(0)
            self.ball_x = start_x + (target_x - start_x) * t
            self.ball_y = start_y + (target_y - start_y) * t - 230 * math.sin(math.pi * t)
            self.ball_rot = int(t * 720)

        def _done():
            self.sound.play_trash_swish()
            self._step_basket_impact()

        self._run_frames(20, 20, _frame, _done)

    def _step_basket_impact(self):
        if self._is_closing:
            return
        self.phase = "impact"
        self.ball_y = self.screen_h + 200
        self._init_splash_particles()

        bounce_frames = [10, 16, 8, -4, 2, 0]
        idx = 0

        def _bounce():
            nonlocal idx
            if self._is_closing:
                return
            for sp in self.splash_particles:
                sp["x"] += sp["vx"]
                sp["y"] += sp["vy"]
                sp["vy"] += 0.4
                sp["life"] -= 0.08

            self.bin_bounce = bounce_frames[idx] if idx < len(bounce_frames) else 0
            idx += 1
            self._draw_scene()

            if idx < len(bounce_frames) or any(sp["life"] > 0 for sp in self.splash_particles):
                self.after(30, _bounce)
            else:
                self.after(350, self._step_bin_slide_down)

        _bounce()

    def _step_bin_slide_down(self):
        if self._is_closing:
            return
        self.phase = "bin_out"
        start_y = self.bin_target_y

        def _frame(_step, progress):
            self.bin_current_y = start_y + (progress ** 2) * (self.screen_h + 80 - start_y)

        self._run_frames(12, 20, _frame, self.skip_and_close)

    def skip_and_close(self):
        if self._is_closing:
            return
        self._is_closing = True
        try:
            self.destroy()
        except Exception:
            pass
        if self.on_finish:
            try:
                self.on_finish()
            except Exception:
                pass
