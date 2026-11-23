"""
Novaboard - Otomatik Uygulama İçi Güncelleme (In-App Auto-Updater) Modülü.

Çalışma Mantığı:
  1. Uygulama açıldıktan kısa bir süre sonra (root.after + daemon thread) arka planda
     GitHub Releases API'sine (https://api.github.com/repos/EfeSacli/novaboard/releases/latest)
     sessizce istek atar.
  2. Gelen 'tag_name' (örn: 'v1.1.0') ile yerel CURRENT_VERSION ('1.0.0') sürümünü karşılaştırır.
  3. GitHub'daki sürüm daha yüksekse ana Tkinter thread'inde kullanıcıya
     "Yeni Güncelleme Var! 🎉" onay penceresi gösterir.
  4. Kullanıcı "Evet" derse tarayıcı açmak yerine:
     - Release içindeki uygun .exe / .deb / .zip dosyasını (asset) bulur,
     - TEMP klasörüne arka planda indirir,
     - İndirme bitince yeni .exe dosyasını os.startfile() ile başlatır (veya taşınabilir
       .exe ise mevcut dosyayı da güncelleyip başlatır) ve mevcut uygulamayı sys.exit(0) ile kapatır.
  5. İnternet yoksa, API erişilemezse veya sürüm zaten güncelse hiçbir hata/uyarı
     göstermeden sessizce çalışmaya devam eder.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import urllib.request
from tkinter import messagebox

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

CURRENT_VERSION = "1.2.0"
GITHUB_REPO = "EfeSacli/novaboard"
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RAW_SURUMLER_BASE = f"https://github.com/{GITHUB_REPO}/raw/main/surumler"


def parse_version_tuple(version_str: str) -> tuple:
    """'v1.1.0', '1.0.0-beta' gibi sürüm etiketlerini (1, 1, 0) sayısal demetine çevirir."""
    cleaned = (version_str or "").strip().lstrip("vV")
    nums = [int(n) for n in re.findall(r"\d+", cleaned)]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3])


def is_newer_version(remote_tag: str, local_version: str = CURRENT_VERSION) -> bool:
    """GitHub'daki sürüm yerel sürümden daha yüksekse True döndürür."""
    try:
        return parse_version_tuple(remote_tag) > parse_version_tuple(local_version)
    except Exception:
        return False


def _http_get_json(url: str, timeout: int = 6) -> dict:
    """requests varsa requests ile, yoksa urllib ile JSON verisini çeker."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"Novaboard-Updater/{CURRENT_VERSION}",
    }
    if HAS_REQUESTS:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _select_best_asset(release_data: dict) -> tuple:
    """
    Release JSON verisinden işletim sistemine en uygun indirme bağlantısını ve dosya adını seçer.
    Eğer Release'e doğrudan binary asset yüklenmemişse repo içindeki surumler/ klasörüne yedek bağlantı kurar.
    Dönüş: (download_url, filename)
    """
    assets = release_data.get("assets") or []
    is_win = sys.platform == "win32"

    if is_win:
        # Çalışan mevcut exe kurulumlu mu yoksa taşınabilir mi kontrol et
        exe_path = os.path.abspath(sys.executable).lower()
        is_installed = "program files" in exe_path or "appdata\\local\\programs" in exe_path

        exe_assets = [a for a in assets if a.get("name", "").lower().endswith(".exe")]
        zip_assets = [a for a in assets if a.get("name", "").lower().endswith(".zip") and "windows" in a.get("name", "").lower()]

        if exe_assets:
            if is_installed:
                preferred = [a for a in exe_assets if "kurulumlu" in a.get("name", "").lower() or "setup" in a.get("name", "").lower()]
            else:
                preferred = [a for a in exe_assets if "kurulumsuz" in a.get("name", "").lower() or "portable" in a.get("name", "").lower()]
            chosen = preferred[0] if preferred else exe_assets[0]
            return chosen.get("browser_download_url"), chosen.get("name")

        if zip_assets:
            return zip_assets[0].get("browser_download_url"), zip_assets[0].get("name")

        # Release'e dosya eklenmemişse (sadece metin/tag açılmışsa) doğrudan surumler/ altındaki .exe'yi indir
        fallback_name = "Novaboard-Windows-Kurulumlu-v1.0.exe" if is_installed else "Novaboard-Windows-Kurulumsuz-v1.0.exe"
        return f"{RAW_SURUMLER_BASE}/{fallback_name}", fallback_name

    else:
        # Pardus / Linux
        deb_assets = [a for a in assets if a.get("name", "").lower().endswith(".deb")]
        if deb_assets:
            return deb_assets[0].get("browser_download_url"), deb_assets[0].get("name")
        fallback_name = "Novaboard-Pardus-Kurulumlu-v1.0.deb"
        return f"{RAW_SURUMLER_BASE}/{fallback_name}", fallback_name


def _download_file(url: str, dest_path: str, on_progress=None, timeout: int = 30):
    """Dosyayı arka planda TEMP klasörüne indirir (requests veya urllib ile)."""
    headers = {"User-Agent": f"Novaboard-Updater/{CURRENT_VERSION}"}

    if HAS_REQUESTS:
        with requests.get(url, headers=headers, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length") or 0)
            downloaded = 0
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
                    if on_progress and total > 0:
                        on_progress(min(100, int(downloaded * 100 / total)))
        return

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        downloaded = 0
        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if on_progress and total > 0:
                    on_progress(min(100, int(downloaded * 100 / total)))


def _launch_downloaded_update_and_exit(downloaded_path: str):
    """
    İndirilen yeni .exe dosyasını çalıştırır ve mevcut uygulamayı sys.exit(0) ile kapatır.
    Eğer kullanıcı kurulumsuz (taşınabilir) tek dosya .exe çalıştırıyorsa ve indirilen dosya da
    kurulumsuz .exe ise, mevcut .exe kapandıktan 1 sn sonra eski .exe'yi yenisiyle değiştirip başlatır.
    """
    if sys.platform == "win32":
        is_frozen = getattr(sys, "frozen", False)
        current_exe = os.path.abspath(sys.executable)
        dl_name_lower = os.path.basename(downloaded_path).lower()
        is_portable_update = "kurulumsuz" in dl_name_lower and downloaded_path.lower().endswith(".exe")

        if is_frozen and is_portable_update and os.path.exists(current_exe):
            try:
                # Mevcut taşınabilir .exe kapandıktan hemen sonra üzerine yazıp yeniden başlatan yardımcı betik
                bat_path = os.path.join(tempfile.gettempdir(), "novaboard_self_update.bat")
                with open(bat_path, "w", encoding="utf-8") as bf:
                    bf.write(
                        "@echo off\n"
                        "timeout /t 1 /nobreak >nul\n"
                        f'copy /y "{downloaded_path}" "{current_exe}" >nul\n'
                        f'start "" "{current_exe}"\n'
                        'del "%~f0"\n'
                    )
                os.startfile(bat_path)
                sys.exit(0)
            except Exception:
                pass

        # Kurulumlu (.exe) veya standart çalıştırma: doğrudan os.startfile ile başlat ve çık
        os.startfile(downloaded_path)
        sys.exit(0)
    else:
        # Pardus / Linux için indirilen paketi aç ve çık
        subprocess.Popen(["xdg-open", downloaded_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sys.exit(0)


class AutoUpdater:
    """
    Tkinter / CustomTkinter ana penceresine bağlanan sessiz otomatik güncelleme denetleyicisi.
    Kullanım:
        updater = AutoUpdater(self.main_window)
        updater.schedule_check(delay_ms=2500)
    """

    def __init__(self, root_window):
        self.root = root_window

    def schedule_check(self, delay_ms: int = 2500):
        """Uygulama açıldıktan delay_ms milisaniye sonra arka planda güncelleme kontrolünü başlatır."""
        try:
            self.root.after(delay_ms, self._start_check_thread)
        except Exception:
            pass

    def _start_check_thread(self):
        threading.Thread(target=self._check_worker, daemon=True).start()

    def _check_worker(self):
        """Arka plan thread'i: GitHub API'sini sorgular, yeni sürüm varsa UI thread'ine bildirir."""
        try:
            release_data = _http_get_json(GITHUB_API_LATEST, timeout=6)
            remote_tag = (release_data.get("tag_name") or "").strip()
            if not remote_tag or not is_newer_version(remote_tag, CURRENT_VERSION):
                return

            download_url, filename = _select_best_asset(release_data)
            if not download_url or not filename:
                return

            release_title = (release_data.get("name") or remote_tag).strip()
            try:
                self.root.after(0, lambda: self._prompt_user_on_ui(remote_tag, release_title, download_url, filename))
            except Exception:
                pass
        except Exception:
            # İnternet yoksa, zaman aşımı olursa veya henüz release yoksa sessizce devam et
            return

    def _prompt_user_on_ui(self, remote_tag: str, release_title: str, download_url: str, filename: str):
        """Ana Tkinter thread'inde kullanıcıya güncelleme sorusunu gösterir."""
        if not self.root.winfo_exists():
            return

        msg = (
            f"Novaboard'un yeni bir sürümü mevcut!\n\n"
            f"• Mevcut Sürüm: v{CURRENT_VERSION}\n"
            f"• Yeni Sürüm: {remote_tag} ({release_title})\n\n"
            f"Güncelleme şimdi arka planda indirilip otomatik olarak kurulsun mu?"
        )
        accepted = messagebox.askyesno("Yeni Güncelleme Var! 🎉", msg, parent=self.root)
        if not accepted:
            return

        self._log_to_status_bar(f"Downloading update {remote_tag} ({filename})...")
        threading.Thread(
            target=self._download_and_apply_worker,
            args=(remote_tag, download_url, filename),
            daemon=True,
        ).start()

    def _log_to_status_bar(self, text: str):
        try:
            if hasattr(self.root, "log_action"):
                self.root.log_action(text)
        except Exception:
            pass

    def _download_and_apply_worker(self, remote_tag: str, download_url: str, filename: str):
        """Arka planda yeni sürümü TEMP klasörüne indirir ve tamamlanınca başlatıp uygulamayı kapatır."""
        try:
            temp_dir = os.path.join(tempfile.gettempdir(), "Novaboard_Update")
            os.makedirs(temp_dir, exist_ok=True)
            dest_path = os.path.join(temp_dir, filename)

            def _on_prog(pct):
                try:
                    self.root.after(0, lambda p=pct: self._log_to_status_bar(f"Downloading update {remote_tag}... %{p}"))
                except Exception:
                    pass

            _download_file(download_url, dest_path, on_progress=_on_prog, timeout=60)

            if not os.path.exists(dest_path) or os.path.getsize(dest_path) < 1024:
                raise RuntimeError("İndirilen güncelleme dosyası doğrulanamadı.")

            self.root.after(0, lambda: _launch_downloaded_update_and_exit(dest_path))
        except Exception:
            # İndirme sırasında bağlantı koparsa kullanıcıyı kilitlemeden sessizce logla
            try:
                self.root.after(0, lambda: self._log_to_status_bar("Update download failed // continuing offline"))
            except Exception:
                pass
