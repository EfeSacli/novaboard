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
            # 1. Stream / Yazım / Seçim Tıkırtısı: 150Hz-380Hz arası kısa mekanik röle/anahtar darbesi
            self._cache["tick"] = _synthesize_wav([
                ((330.0, 155.0), 0.018, 0.10, 0.002, 0.12),
            ])
            # 2. Onay / Tamamlanma Sesi: Fiziksel mekanik anahtarın kapanma hissi veren kısa, tok "click/thud"
            self._cache["reveal"] = _synthesize_wav([
                ((190.0, 88.0), 0.036, 0.18, 0.002, 0.15),
                ((380.0, 210.0), 0.024, 0.12, 0.001, 0.10),
            ])
            # 3. Hata / Uyarı Sesi: Düşük frekanslı, kısa mekanik uyarı tonu
            self._cache["error"] = _synthesize_wav([
                ((145.0, 108.0), 0.042, 0.16, 0.003, 0.25),
                (0, 0.016, 0.0),
                ((135.0, 98.0), 0.045, 0.16, 0.003, 0.25),
            ])
            # 4. Kağıt buruşturma: Kuru, mekanik dokulu kısa kağıt hışırtısı
            self._cache["crumple"] = _synthesize_wav([
                (-1, 0.032, 0.07, 0.004, 0.0),
                (0, 0.010, 0.0),
                (-1, 0.038, 0.08, 0.004, 0.0),
                (0, 0.010, 0.0),
                (-1, 0.030, 0.06, 0.004, 0.0),
            ])
            # 5. Çöp kovasına düşüş: Tok, kuru mekanik "thud"
            self._cache["trash_swish"] = _synthesize_wav([
                ((220.0, 110.0), 0.055, 0.18, 0.003, 0.12),
                ((310.0, 180.0), 0.035, 0.12, 0.002, 0.08),
            ])
            # 6. Çöp kovası boşaltma: Kuru mekanik röle serisi
            self._cache["trash_burst"] = _synthesize_wav([
                ((160.0, 320.0), 0.045, 0.15, 0.003, 0.12),
                (0, 0.012, 0.0),
                ((240.0, 390.0), 0.040, 0.14, 0.002, 0.10),
            ])
            # 7. Süre bitimi: Mekanik çift darbeli düşük-orta frekanslı tok uyarı
            self._cache["timer_alarm"] = _synthesize_wav([
                ((320.0, 220.0), 0.065, 0.18, 0.003, 0.14),
                (0, 0.035, 0.0),
                ((320.0, 220.0), 0.085, 0.18, 0.003, 0.14),
            ])
            # 8. Tur tamamlandı: Üç kademeli mekanik kilit/onay sesi
            self._cache["complete_fanfare"] = _synthesize_wav([
                ((220.0, 140.0), 0.035, 0.14, 0.002, 0.10),
                (0, 0.012, 0.0),
                ((280.0, 180.0), 0.035, 0.15, 0.002, 0.10),
                (0, 0.012, 0.0),
                ((360.0, 220.0), 0.055, 0.18, 0.002, 0.12),
            ])

            if not HAS_WINSOUND:
                self._temp_dir = os.path.join(tempfile.gettempdir(), "novaboard_sounds")
                os.makedirs(self._temp_dir, exist_ok=True)
                for key, data in self._cache.items():
                    path = os.path.join(self._temp_dir, f"{key}.wav")
                    if not os.path.exists(path):
                        with open(path, "wb") as f:
                            f.write(data)
        except Exception:
            pass

    def is_enabled(self):
        return bool(self.dm.get_setting("sound_enabled", True))

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
                winsound.PlaySound(
                    wav_bytes,
                    winsound.SND_MEMORY | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
                )
                return
            except Exception:
                pass

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
