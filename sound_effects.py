import io
import math
import os
import struct
import subprocess
import sys
import tempfile
import threading
import wave

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


def _synthesize_wav(notes, sample_rate=22050):
    """
    Yumuşak, kulağı yormayan, doğal akustik (ahşap marimba / sakin zil) ses dalgası üretir.
    notes: [(freq_hz, duration_sec, volume_0_to_1,attack_sec, harm2_ratio), ...]
    freq_hz bir tuple (f_start, f_end) ise frekans yumuşakça kayar (pitch glide).
    freq_hz == 0 ise sessizlik / bekleme üretir.
    freq_hz == -1 ise yumuşak kağıt hışırtısı (filtrelenmiş hafif pembe gürültü) üretir.
    """
    samples = []
    rng_state = 1234567

    for item in notes:
        freq, dur, vol = item[0], item[1], item[2]
        attack = item[3] if len(item) > 3 else 0.010
        harm2 = item[4] if len(item) > 4 else 0.15

        n_samples = max(1, int(sample_rate * dur))
        if freq == 0:
            samples.extend([0] * n_samples)
            continue

        is_glide = isinstance(freq, (tuple, list))
        f0 = freq[0] if is_glide else float(freq)
        f1 = freq[1] if is_glide else float(freq)

        phase = 0.0
        lp_prev = 0.0
        decay_rate = 4.2 / max(0.02, dur)

        for i in range(n_samples):
            t = i / float(sample_rate)
            progress = i / float(n_samples)

            # Yumuşak fade-in (attack) ve doğal üstel sönümlenme (exponential decay)
            if t < attack:
                env = 0.5 * (1.0 - math.cos(math.pi * t / max(0.001, attack)))
            else:
                env = math.exp(-decay_rate * (t - attack))

            # Son %12'de tıklamayı önleyen yumuşak kapanış
            if progress > 0.88:
                env *= (1.0 - progress) / 0.12

            if freq == -1:
                # Çok hafif, filtrelenmiş yumuşak kağıt dokunuşu
                rng_state = (1103515245 * rng_state + 12345) & 0x7FFFFFFF
                white = (rng_state / 1073741824.0) - 1.0
                lp_prev = 0.82 * lp_prev + 0.18 * white
                val = lp_prev * env * vol
            else:
                cur_f = f0 + (f1 - f0) * progress
                phase += 2.0 * math.pi * cur_f / sample_rate
                # Temel sinüs + çok hafif oktav harmoniği (sıcak ahşap/zil tınısı)
                val = (math.sin(phase) + harm2 * math.sin(2.0 * phase)) / (1.0 + harm2)
                val *= env * vol

            pcm = max(-32767, min(32767, int(val * 32767)))
            samples.append(pcm)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return buf.getvalue()


class SoundPlayer:
    """
    Novaboard - Sakin, Akustik Ses Efektleri Motoru.
    Sert ve yapay bip sesleri yerine düşük ses seviyeli, yumuşak zarflı (fade-in/exponential decay)
    akustik ahşap/marimba tınıları üretir ve önbellekten gecikmesiz çalar.
    """

    def __init__(self, data_manager):
        self.dm = data_manager
        self._cache = {}
        self._temp_dir = None
        self._build_sound_cache()

    def _build_sound_cache(self):
        try:
            vol_pct = max(10, min(100, int(self.dm.get_setting("sound_volume", 75) or 75)))
            v_mul = vol_pct / 75.0
            # 1. Tık / Seçim Sesi: Tok, net ve kulağı yormayan mekanik anahtar/ahşap tıkırtısı
            self._cache["tick"] = _synthesize_wav([
                ((420.0, 220.0), 0.038, min(0.95, 0.42 * v_mul), 0.003, 0.14),
            ])
            # 2. Onay / Öğrenci Seçimi / Doğru Cevap: Sakin, tok ve net çift kademeli onay tınısı
            self._cache["reveal"] = _synthesize_wav([
                (330.0, 0.075, min(0.95, 0.48 * v_mul), 0.008, 0.14),
                (493.88, 0.180, min(0.95, 0.52 * v_mul), 0.010, 0.12),
            ])
            # 3. Hata / Yanlış Cevap Sesi: Düşük frekanslı, tok mekanik uyarı tonu
            self._cache["error"] = _synthesize_wav([
                ((210.0, 150.0), 0.080, min(0.95, 0.48 * v_mul), 0.005, 0.22),
                (0, 0.025, 0.0),
                ((180.0, 130.0), 0.110, min(0.95, 0.48 * v_mul), 0.005, 0.22),
            ])
            # 4. Kağıt buruşturma: Yumuşak, doğal kağıt dokusu
            self._cache["crumple"] = _synthesize_wav([
                (-1, 0.045, min(0.95, 0.30 * v_mul), 0.005, 0.0),
                (0, 0.014, 0.0),
                (-1, 0.055, min(0.95, 0.34 * v_mul), 0.005, 0.0),
                (0, 0.012, 0.0),
                (-1, 0.045, min(0.95, 0.28 * v_mul), 0.005, 0.0),
            ])
            # 5. Çöp kovasına düşüş: Tok akustik "thud" ve onay
            self._cache["trash_swish"] = _synthesize_wav([
                ((280.0, 140.0), 0.085, min(0.95, 0.50 * v_mul), 0.005, 0.15),
                (440.0, 0.130, min(0.95, 0.42 * v_mul), 0.008, 0.10),
            ])
            # 6. Çöp kovası boşaltma / çöplerin dışarı fırlaması: Tok yükselen efekt
            self._cache["trash_burst"] = _synthesize_wav([
                ((220.0, 480.0), 0.120, min(0.95, 0.48 * v_mul), 0.008, 0.14),
                (0, 0.018, 0.0),
                (587.33, 0.160, min(0.95, 0.46 * v_mul), 0.008, 0.10),
            ])
            # 7. Süre bitimi: Sakin, tok çift vuruşlu zil
            self._cache["timer_alarm"] = _synthesize_wav([
                (440.0, 0.180, min(0.95, 0.55 * v_mul), 0.010, 0.15),
                (0, 0.045, 0.0),
                (587.33, 0.280, min(0.95, 0.55 * v_mul), 0.010, 0.14),
            ])
            # 8. Tur tamamlandı: Üç kademeli sakin, sıcak onay dizisi
            self._cache["complete_fanfare"] = _synthesize_wav([
                (293.66, 0.095, min(0.95, 0.46 * v_mul), 0.008, 0.12),
                (369.99, 0.095, min(0.95, 0.48 * v_mul), 0.008, 0.12),
                (440.00, 0.240, min(0.95, 0.52 * v_mul), 0.010, 0.12),
            ])

            self._temp_dir = os.path.join(tempfile.gettempdir(), "novaboard_sounds_v2")
            os.makedirs(self._temp_dir, exist_ok=True)
            for key, data in self._cache.items():
                path = os.path.join(self._temp_dir, f"{key}.wav")
                with open(path, "wb") as f:
                    f.write(data)
        except Exception:
            pass

    def is_enabled(self):
        return bool(self.dm.get_setting("sound_enabled", True))

    def set_volume(self, volume_pct: int):
        v = max(10, min(100, int(volume_pct)))
        self.dm.set_setting("sound_volume", v)
        self._build_sound_cache()

    def toggle_audio(self) -> bool:
        new_state = not self.is_enabled()
        self.dm.set_setting("sound_enabled", new_state)
        if new_state:
            self.play_reveal()
        return new_state

    def play_error(self):
        self._play_cached("error")

    def _play_cached(self, key):
        if not self.is_enabled():
            return
        wav_bytes = self._cache.get(key)
        if not wav_bytes:
            return

        if HAS_WINSOUND:
            try:
                if self._temp_dir:
                    wav_path = os.path.join(self._temp_dir, f"{key}.wav")
                    if os.path.exists(wav_path):
                        winsound.PlaySound(
                            wav_path,
                            winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
                        )
                        return
            except Exception:
                pass

            def _run_win_mem():
                try:
                    winsound.PlaySound(wav_bytes, winsound.SND_MEMORY | winsound.SND_NODEFAULT)
                except Exception:
                    pass

            threading.Thread(target=_run_win_mem, daemon=True).start()
            return

        def _run_linux():
            try:
                if self._temp_dir:
                    wav_path = os.path.join(self._temp_dir, f"{key}.wav")
                    if os.path.exists(wav_path):
                        for cmd in (["aplay", "-q", wav_path], ["paplay", wav_path]):
                            try:
                                subprocess.Popen(
                                    cmd,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                )
                                return
                            except Exception:
                                continue
            except Exception:
                pass

        threading.Thread(target=_run_linux, daemon=True).start()

    def play_tick(self):
        self._play_cached("tick")

    def play_reveal(self):
        self._play_cached("reveal")

    def play_crumple(self):
        self._play_cached("crumple")

    def play_trash_swish(self):
        self._play_cached("trash_swish")

    def play_trash_burst(self):
        self._play_cached("trash_burst")

    def play_timer_alarm(self):
        self._play_cached("timer_alarm")

    def play_complete_fanfare(self):
        self._play_cached("complete_fanfare")
