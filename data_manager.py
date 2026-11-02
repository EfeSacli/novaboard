import json
import os
import sys
import re
import random
import shutil
from datetime import datetime

# Yeni kurulumda eksik olan ayarlar bu değerlerle tamamlanır.
# (drawer_pos_x / drawer_pos_y çekmece taşındığında ayrıca kaydedilir.)
DEFAULT_SETTINGS = {
    "sound_enabled": True,
    "theme": "dark",
    "custom_bg": "",
    "custom_accent": "",
    "paper_animation_enabled": True,
    "font_family": "Segoe UI",
    "font_size_scale": "Standart",
    "quick_notes": "",
}

CLASS_LIST_KEYS = ("students", "picked", "exempt", "history")


class DataManager:
    """
    Novaboard - Veri katmanı.
    Sınıfları, öğrencileri, kura durumunu (seçilen / muaf), seçim geçmişini,
    kelime yarışması döngüsünü ve uygulama ayarlarını tek bir JSON dosyasında saklar.

    Dosya konumu:  Windows -> %APPDATA%/Novaboard/novaboard_verileri.json
                   Linux   -> ~/.config/Novaboard/novaboard_verileri.json

    Bir sınıfın JSON yapısı:
        {"students": [...], "picked": [...], "exempt": [...],
         "history": [{"student": ..., "timestamp": "HH:MM:SS"}], "vocab_competed": [...]}
    """

    def __init__(self):
        if sys.platform == "win32":
            base_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
        else:
            base_dir = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))

        appdata_dir = os.path.join(base_dir, "Novaboard")
        os.makedirs(appdata_dir, exist_ok=True)
        self.file_path = os.path.join(appdata_dir, "novaboard_verileri.json")

        if not os.path.exists(self.file_path):
            self._migrate_legacy_file(base_dir)

        self.data = {"active_class": "", "settings": {}, "classes": {}}
        self.load_data()

    def _migrate_legacy_file(self, base_dir):
        """Eski sürümlerden (Sorufelek / OgrenciSecici / yerel dosya) kalan veriyi yeni konuma kopyalar."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(base_dir, "Sorufelek", "sorufelek_verileri.json"),
            os.path.join(script_dir, "sorufelek_verileri.json"),
            os.path.join(base_dir, "OgrenciSecici", "ogrenci_verileri.json"),
            os.path.join(script_dir, "novaboard_verileri.json"),
        ]
        for old_path in candidates:
            if os.path.exists(old_path):
                try:
                    shutil.copy2(old_path, self.file_path)
                    return
                except Exception:
                    pass

    def load_data(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict) and "classes" in loaded:
                    self.data = loaded
            except Exception as e:
                print(f"Veri yükleme hatası: {e}")

        # Eksik alanları tamamla
        settings = self.data.setdefault("settings", {})
        for key, value in DEFAULT_SETTINGS.items():
            settings.setdefault(key, value)
        for cdata in self.data["classes"].values():
            for key in CLASS_LIST_KEYS:
                cdata.setdefault(key, [])

        self.get_active_class()  # geçersiz aktif sınıfı düzeltir
        self.save_data()

    def save_data(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Veri kaydetme hatası: {e}")

    def _class(self, class_name=None):
        """Sınıfın veri sözlüğünü döndürür (verilmezse aktif sınıf). Sınıf yoksa None."""
        return self.data["classes"].get(class_name or self.get_active_class())

    # --- Sınıf Yönetimi ---
    def get_class_names(self):
        return sorted(self.data["classes"].keys())

    def get_active_class(self):
        if self.data.get("active_class") not in self.data["classes"]:
            names = self.get_class_names()
            self.data["active_class"] = names[0] if names else ""
        return self.data["active_class"]

    def set_active_class(self, class_name):
        if class_name in self.data["classes"]:
            self.data["active_class"] = class_name
            self.save_data()

    def add_class(self, class_name):
        class_name = class_name.strip()
        if not class_name:
            return False, "Sınıf adı boş bırakılamaz."
        if class_name in self.data["classes"]:
            return False, f"'{class_name}' adına sahip bir sınıf kaydı sistemde zaten mevcuttur."

        self.data["classes"][class_name] = {key: [] for key in CLASS_LIST_KEYS}
        self.data["active_class"] = class_name
        self.save_data()
        return True, "Sınıf kaydı başarıyla oluşturulmuştur."

    def delete_class(self, class_name):
        if class_name not in self.data["classes"]:
            return False
        del self.data["classes"][class_name]
        names = self.get_class_names()
        self.data["active_class"] = names[0] if names else ""
        self.save_data()
        return True

    def rename_class(self, old_name, new_name):
        new_name = new_name.strip()
        if not new_name:
            return False, "Sınıf adı boş bırakılamaz."
        if old_name not in self.data["classes"]:
            return False, "Belirtilen sınıf sistemde bulunamadı."
        if new_name != old_name and new_name in self.data["classes"]:
            return False, f"'{new_name}' adına sahip bir sınıf kaydı zaten mevcuttur."

        self.data["classes"][new_name] = self.data["classes"].pop(old_name)
        if self.data.get("active_class") == old_name:
            self.data["active_class"] = new_name
        self.save_data()
        return True, "Sınıf bilgisi güncellenmiştir."

    # --- Öğrenci Listeleri ---
    def get_all_students(self, class_name=None):
        c = self._class(class_name)
        return c["students"] if c else []

    def get_picked_students(self, class_name=None):
        c = self._class(class_name)
        return c["picked"] if c else []

    def get_exempt_students(self, class_name=None):
        c = self._class(class_name)
        return c["exempt"] if c else []

    def get_remaining_students(self, class_name=None):
        """Henüz seçilmemiş ve muaf olmayan öğrenciler."""
        c = self._class(class_name)
        if not c:
            return []
        excluded = set(c["picked"]) | set(c["exempt"])
        return [s for s in c["students"] if s not in excluded]

    def get_active_students(self, class_name=None):
        """Muaf (devamsız) olmayan tüm öğrenciler."""
        c = self._class(class_name)
        if not c:
            return []
        exempt = set(c["exempt"])
        return [s for s in c["students"] if s not in exempt]

    def add_student(self, student_name, class_name=None):
        c = self._class(class_name)
        student_name = student_name.strip()
        if not student_name or not c:
            return False, "Geçersiz öğrenci kaydı veya sınıf seçimi."
        if student_name in c["students"]:
            return False, f"'{student_name}' isimli öğrenci bu sınıfta kayıtlıdır."

        c["students"].append(student_name)
        self.save_data()
        return True, "Öğrenci kaydı başarıyla eklendi."

    def remove_student(self, student_name, class_name=None):
        c = self._class(class_name)
        if not c:
            return False
        for key in ("students", "picked", "exempt"):
            if student_name in c[key]:
                c[key].remove(student_name)
        self.save_data()
        return True

    def set_students_list(self, students_list, class_name=None):
        """Öğrenci listesini tamamen değiştirir; listede olmayanların seçim/muaf kayıtlarını siler."""
        c = self._class(class_name)
        if not c:
            return False

        unique_students = []
        for s in students_list:
            clean = s.strip()
            if clean and clean not in unique_students:
                unique_students.append(clean)

        c["students"] = unique_students
        existing = set(unique_students)
        c["picked"] = [p for p in c["picked"] if p in existing]
        c["exempt"] = [e for e in c["exempt"] if e in existing]
        self.save_data()
        return True

    def parse_bulk_text(self, text):
        """
        e-Okul / Excel'den yapıştırılan metni isim listesine çevirir.
        Sekmeli satırlarda sayı olmayan ilk sütunu alır, baştaki sıra numaralarını ("1.", "2-", "3)") siler.
        """
        parsed = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            if "\t" in line:
                parts = [p.strip() for p in line.split("\t") if p.strip()]
                name_parts = [p for p in parts if not p.replace(".", "").replace("-", "").isdigit()]
                if name_parts:
                    line = name_parts[0]
                elif parts:
                    line = parts[-1]

            cleaned = re.sub(r"^\s*\d+[\.\-\)\:\s\t]+", "", line).strip() or line.strip()
            cleaned = cleaned.strip("\"'")
            if cleaned and cleaned not in parsed:
                parsed.append(cleaned)
        return parsed

    # --- Kura (Öğrenci Seçimi) ---
    def pick_random(self, class_name=None):
        """Kalan öğrencilerden birini seçer. Dönüş: (seçilen, liste_bitti_mi)."""
        cname = class_name or self.get_active_class()
        remaining = self.get_remaining_students(cname)
        if not remaining:
            return None, True

        chosen = random.choice(remaining)
        c = self.data["classes"][cname]
        c["picked"].append(chosen)
        c["history"].append({"student": chosen, "timestamp": datetime.now().strftime("%H:%M:%S")})
        self.save_data()
        return chosen, len(remaining) == 1

    def undo_pick(self, class_name=None):
        c = self._class(class_name)
        if not c or not c["picked"]:
            return None
        undone = c["picked"].pop()
        if c["history"] and c["history"][-1].get("student") == undone:
            c["history"].pop()
        self.save_data()
        return undone

    def reset_picked(self, class_name=None):
        c = self._class(class_name)
        if not c:
            return False
        c["picked"] = []
        self.save_data()
        return True

    def cycle_student_status(self, student_name, class_name=None):
        """Durumu sırayla değiştirir: Sırada -> Seçildi -> Muaf -> Sırada."""
        c = self._class(class_name)
        if not c:
            return "remaining"

        if student_name in c["picked"]:
            c["picked"].remove(student_name)
            if student_name not in c["exempt"]:
                c["exempt"].append(student_name)
            new_status = "exempt"
        elif student_name in c["exempt"]:
            c["exempt"].remove(student_name)
            new_status = "remaining"
        else:
            c["picked"].append(student_name)
            new_status = "picked"

        self.save_data()
        return new_status

    def get_student_status(self, student_name, class_name=None):
        c = self._class(class_name)
        if c and student_name in c["picked"]:
            return "picked"
        if c and student_name in c["exempt"]:
            return "exempt"
        return "remaining"

    def get_history(self, class_name=None):
        c = self._class(class_name)
        return c["history"] if c else []

    def clear_history(self, class_name=None):
        c = self._class(class_name)
        if c:
            c["history"] = []
            self.save_data()

    # --- Kelime Yarışması Döngüsü (bir kez yarışan, liste sıfırlanana kadar tekrar çıkmaz) ---
    def get_vocab_competed(self, class_name=None):
        c = self._class(class_name)
        return c.setdefault("vocab_competed", []) if c else []

    def mark_vocab_competed(self, student_name, class_name=None):
        c = self._class(class_name)
        if not c or not student_name:
            return
        competed = c.setdefault("vocab_competed", [])
        if student_name not in competed:
            competed.append(student_name)
            self.save_data()

    def reset_vocab_competed(self, class_name=None):
        c = self._class(class_name)
        if c:
            c["vocab_competed"] = []
            self.save_data()

    # --- Ayarlar ---
    def get_setting(self, key, default=None):
        return self.data.get("settings", {}).get(key, default)

    def set_setting(self, key, value):
        self.data.setdefault("settings", {})[key] = value
        self.save_data()
