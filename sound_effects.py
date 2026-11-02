import threading
import time
import sys

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class SoundPlayer:
    """
    Novaboard - Ses Efektleri Motoru.
    Kura seçimi, kareli kağıt buruşturma, çöp kovası basket atışı,
    sayaç zili ve kutlama seslerini arka planda kesintisiz çalar.
    """

    def __init__(self, data_manager):
        self.dm = data_manager

    def is_enabled(self):
        return bool(self.dm.get_setting("sound_enabled", True))

    def _play_sequence(self, tones, fallback_beeps=1, fallback_pause=0.0):
        """Frekans/süre/bekleme dizisini arka planda çalar: [(freq_hz, duration_ms, sleep_sec), ...]."""
        if not self.is_enabled():
            return

        def _run():
            try:
                if HAS_WINSOUND:
                    for freq, dur, pause in tones:
                        winsound.Beep(freq, dur)
                        if pause > 0:
                            time.sleep(pause)
                else:
                    for i in range(fallback_beeps):
                        sys.stdout.write("\a")
                        sys.stdout.flush()
                        if fallback_pause > 0 and i + 1 < fallback_beeps:
                            time.sleep(fallback_pause)
            except Exception:
                pass

        threading.Thread(target=_run, daemon=True).start()

    def play_tick(self):
        self._play_sequence([(920, 22, 0)])

    def play_reveal(self):
        """Neşeli, berrak kutlama akoru (E5, G5, C6)."""
        self._play_sequence([(659, 70, 0.015), (784, 80, 0.015), (1046, 220, 0.015)])

    def play_crumple(self):
        """Kağıt buruşturma sesi efekti."""
        self._play_sequence(
            [(240, 30, 0.01), (380, 25, 0.01), (190, 40, 0.01), (420, 25, 0.01), (280, 35, 0.01), (210, 45, 0.01)],
            fallback_beeps=0,
        )

    def play_trash_swish(self):
        """Kağıdın çöp kovasına düşme / basket atışı sesi efekti."""
        self._play_sequence([(1200, 35, 0.01), (850, 45, 0.02), (1046, 110, 0)])

    def play_timer_alarm(self):
        """Sınav ve ders süresi bittiğinde çalan uyarı zili."""
        bar = [(880, 110, 0.03), (1174, 110, 0.03), (880, 110, 0.03), (1318, 110, 0.15)]
        self._play_sequence(bar * 2, fallback_beeps=3, fallback_pause=0.15)

    def play_complete_fanfare(self):
        """Tur tamamlandığında çalan kutlama melodisi."""
        self._play_sequence([(523, 100, 0.03), (659, 100, 0.03), (784, 100, 0.03), (1046, 300, 0.03)])
