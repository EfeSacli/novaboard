"""
Novaboard - Tüm Sürümleri Derleme ve Paketleme Betiği.

Tek komutla (python build_exe.py) tüm resmi dağıtım paketlerini surumler/ klasörüne üretir:
  1. surumler/Novaboard-Windows-Kurulumsuz-v1.0.exe   (PyInstaller tek dosya taşınabilir .exe)
  2. surumler/Novaboard-Windows-Kurulumlu-v1.0.exe    (Inno Setup kurulum sihirbazı .exe)
  3. surumler/Novaboard-Windows-Kurulumsuz-v1.0.zip   (Windows kurulumsuz hazır klasör .zip)
  4. surumler/Novaboard-Pardus-Kurulumlu-v1.0.deb     (MEB ETAP Pardus / Debian paket kurucu .deb)
  5. surumler/Novaboard-Pardus-Kurulumsuz-v1.0.zip    (Pardus / Linux kurulumsuz klasör .zip)
"""
import io
import os
import sys
import time
import shutil
import tarfile
import zipfile
import subprocess

SURUMLER_DIR = "surumler"

APP_SOURCE_FILES = [
    "app.py", "main_window.py", "drawer_hud.py", "screen_pen.py", "notebook_overlay.py",
    "theme_manager.py", "teacher_tools.py", "vocabulary_game.py", "vocabulary_data.py",
    "data_manager.py", "sound_effects.py", "ui_kit.py",
]

PARDUS_SOURCE_FILES = APP_SOURCE_FILES + [
    "requirements.txt", "baslat.sh", "kurulum_pardus.sh", "novaboard.desktop",
    "icon.png", "icon.ico", "PARDUS_KULLANIM_REHBERI.txt", "README.md", "LICENSE",
]

WINDOWS_EXTRA_FILES = [
    "icon.ico", "icon.png", "KULLANIM_REHBERI.txt", "Masaustune_Kisayol_Ekle.vbs", "Baslat_Windows.vbs",
]

TEXT_EXTENSIONS = (".py", ".sh", ".desktop", ".txt", ".md", ".json")

PYINSTALLER_COMMON_ARGS = [
    "--noconsole",
    "--name=Novaboard",
    "--icon=icon.ico",
    "--add-data=icon.ico;.",
    "--add-data=icon.png;.",
    "--version-file=version_info.txt",
    "--collect-all=customtkinter",
    "--hidden-import=PIL",
    "--hidden-import=PIL.Image",
    "--hidden-import=PIL.ImageDraw",
    "--hidden-import=PIL.ImageTk",
    "--hidden-import=PIL.ImageGrab",
    "--hidden-import=encodings",
    "--collect-all=encodings",
    "--clean",
    "app.py",
]


def clean_temp_files():
    """Derleme sonrası geçici klasörleri ve dosyaları temizler."""
    temp_paths = [
        "build", "dist", "__pycache__", "temp_pardus_package", "temp_windows_portable",
        "Novaboard.spec", "TestBoot.spec", "Novaboard.exe", "Novaboard_Kurulum.exe",
    ]
    for path in temp_paths:
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)
            except Exception:
                pass


def zip_directory(folder_to_zip, zip_output_path, root_dir_in_zip="Novaboard"):
    """Bir klasörü tüm alt dosyalarıyla birlikte (__pycache__ hariç) zip arşivine dönüştürür."""
    if os.path.exists(zip_output_path):
        os.remove(zip_output_path)
    with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder_to_zip):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for file in files:
                if file.endswith((".pyc", ".pyo")) or file == ".DS_Store":
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, folder_to_zip)
                zf.write(full_path, os.path.join(root_dir_in_zip, rel_path))


def _add_bytes_to_tar(tar, name, data_bytes, mode=0o644):
    ti = tarfile.TarInfo(name=name)
    ti.size = len(data_bytes)
    ti.mtime = int(time.time())
    ti.mode = mode
    ti.uid = 0
    ti.gid = 0
    ti.uname = "root"
    ti.gname = "root"
    tar.addfile(ti, io.BytesIO(data_bytes))


def _add_dir_to_tar(tar, name):
    ti = tarfile.TarInfo(name=name)
    ti.type = tarfile.DIRTYPE
    ti.mode = 0o755
    ti.mtime = int(time.time())
    ti.uid = 0
    ti.gid = 0
    ti.uname = "root"
    ti.gname = "root"
    tar.addfile(ti)


def _add_package_tree_to_tar(tar, src_dir, target_root):
    """Bir Python paket klasörünü (customtkinter, packaging, darkdetect) .deb data.tar.gz içine ekler."""
    if not os.path.isdir(src_dir):
        return
    _add_dir_to_tar(tar, target_root)
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for d in dirs:
            rel = os.path.relpath(os.path.join(root, d), src_dir).replace("\\", "/")
            _add_dir_to_tar(tar, f"{target_root}/{rel}")
        for fname in files:
            if fname.endswith((".pyc", ".pyo")) or fname == ".DS_Store":
                continue
            f_path = os.path.join(root, fname)
            rel = os.path.relpath(f_path, src_dir).replace("\\", "/")
            with open(f_path, "rb") as fh:
                raw = fh.read()
            if fname.endswith(TEXT_EXTENSIONS):
                raw = raw.replace(b"\r\n", b"\n")
            _add_bytes_to_tar(tar, f"{target_root}/{rel}", raw, 0o644)


def make_deb_package(output_deb_path):
    """MEB Fatih Akıllı Tahta (Pardus ETAP / Debian) uyumlu .deb paketini oluşturur."""
    print("  -> Pardus ETAP .deb paketi oluşturuluyor...")
    deb_binary = b"2.0\n"

    # 1. control.tar.gz
    ctrl_buf = io.BytesIO()
    with tarfile.open(fileobj=ctrl_buf, mode="w:gz") as tar:
        ctrl_content = (
            "Package: novaboard\n"
            "Version: 1.0.0\n"
            "Section: education\n"
            "Priority: optional\n"
            "Architecture: all\n"
            "Depends: python3, python3-tk, python3-pil\n"
            "Recommends: python3-pil.imagetk\n"
            "Maintainer: Efe Sacli <efesc16@gmail.com>\n"
            "Description: Novaboard - Akilli Tahta ve Ogretmen Asistani\n"
            " MEB Fatih Projesi Pardus ETAP akilli tahtalar ve ogretmenler icin\n"
            " kayan ogrenci secme cekmecesi, akilli tahta kalemi, sayac,\n"
            " grup olusturucu ve kelime yarismasi iceren masaustu uygulamasidir.\n"
        ).encode("utf-8")
        _add_bytes_to_tar(tar, "./control", ctrl_content, 0o644)

        postinst_content = (
            "#!/bin/sh\n"
            "set -e\n"
            "chmod -R a+rX /opt/novaboard 2>/dev/null || true\n"
            "chmod +x /opt/novaboard/baslat.sh 2>/dev/null || true\n"
            "chmod +x /usr/bin/novaboard 2>/dev/null || true\n"
            "update-desktop-database /usr/share/applications 2>/dev/null || true\n"
            "gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true\n"
            "exit 0\n"
        ).encode("utf-8")
        _add_bytes_to_tar(tar, "./postinst", postinst_content, 0o755)
    ctrl_data = ctrl_buf.getvalue()

    # 2. data.tar.gz
    data_buf = io.BytesIO()
    with tarfile.open(fileobj=data_buf, mode="w:gz") as tar:
        for d in [
            "./opt", "./opt/novaboard", "./usr", "./usr/bin", "./usr/share",
            "./usr/share/applications", "./usr/share/icons", "./usr/share/icons/hicolor",
            "./usr/share/icons/hicolor/256x256", "./usr/share/icons/hicolor/256x256/apps",
            "./usr/share/doc", "./usr/share/doc/novaboard",
        ]:
            _add_dir_to_tar(tar, d)

        for pf in PARDUS_SOURCE_FILES:
            if os.path.exists(pf):
                with open(pf, "rb") as f:
                    raw = f.read()
                if pf.endswith(TEXT_EXTENSIONS):
                    raw = raw.replace(b"\r\n", b"\n")
                _add_bytes_to_tar(tar, f"./opt/novaboard/{pf}", raw, 0o755 if pf.endswith(".sh") else 0o644)

        # customtkinter + saf Python bağımlılıkları (packaging, darkdetect) doğrudan gömülür
        _add_package_tree_to_tar(tar, "customtkinter", "./opt/novaboard/customtkinter")
        site_pkg = os.path.join(sys.base_prefix, "Lib", "site-packages")
        for pure_pkg in ["packaging", "darkdetect"]:
            src_pkg = os.path.join(site_pkg, pure_pkg)
            if os.path.isdir(src_pkg):
                _add_package_tree_to_tar(tar, src_pkg, f"./opt/novaboard/{pure_pkg}")

        bin_launcher = (
            "#!/bin/sh\n"
            "cd /opt/novaboard || exit 1\n"
            "export PYTHONPATH=\"/opt/novaboard:${PYTHONPATH}\"\n"
            "exec /bin/bash /opt/novaboard/baslat.sh \"$@\"\n"
        ).encode("utf-8")
        _add_bytes_to_tar(tar, "./usr/bin/novaboard", bin_launcher, 0o755)

        desktop_content = (
            "[Desktop Entry]\n"
            "Version=1.0\n"
            "Type=Application\n"
            "Name=Novaboard\n"
            "GenericName=Akıllı Tahta ve Öğretmen Asistanı\n"
            "Comment=Öğretmenler için modern kura, sayaç, grup oluşturucu ve tahta araçları\n"
            "Exec=/usr/bin/novaboard\n"
            "Path=/opt/novaboard\n"
            "Icon=/usr/share/icons/hicolor/256x256/apps/novaboard.png\n"
            "Terminal=false\n"
            "Categories=Education;Teaching;Utility;\n"
            "StartupNotify=false\n"
        ).encode("utf-8")
        _add_bytes_to_tar(tar, "./usr/share/applications/novaboard.desktop", desktop_content, 0o644)

        if os.path.exists("icon.png"):
            with open("icon.png", "rb") as f:
                _add_bytes_to_tar(tar, "./usr/share/icons/hicolor/256x256/apps/novaboard.png", f.read(), 0o644)
    data_bytes = data_buf.getvalue()

    # 3. ar arşiv birleştirme
    if os.path.exists(output_deb_path):
        os.remove(output_deb_path)
    with open(output_deb_path, "wb") as f:
        f.write(b"!<arch>\n")
        for name, data in [("debian-binary", deb_binary), ("control.tar.gz", ctrl_data), ("data.tar.gz", data_bytes)]:
            hdr = f"{name:<16}{int(time.time()):<12}0     0     100644  {len(data):<10}\x60\n".encode("ascii")
            f.write(hdr)
            f.write(data)
            if len(data) % 2 != 0:
                f.write(b"\n")
    print(f"  -> {output_deb_path} hazır ({os.path.getsize(output_deb_path)} bayt).")


def build_pardus_packages():
    """Pardus ETAP .deb ve kurulumsuz .zip paketlerini üretir."""
    os.makedirs(SURUMLER_DIR, exist_ok=True)

    for sh_file in ["baslat.sh", "kurulum_pardus.sh", "novaboard.desktop"]:
        if os.path.exists(sh_file):
            with open(sh_file, "rb") as f:
                data = f.read().replace(b"\r\n", b"\n")
            with open(sh_file, "wb") as f:
                f.write(data)

    make_deb_package(os.path.join(SURUMLER_DIR, "Novaboard-Pardus-Kurulumlu-v1.0.deb"))

    temp_p = "temp_pardus_package"
    shutil.rmtree(temp_p, ignore_errors=True)
    os.makedirs(temp_p, exist_ok=True)
    for f in PARDUS_SOURCE_FILES:
        if os.path.exists(f):
            shutil.copy2(f, temp_p)
    if os.path.exists("customtkinter"):
        shutil.copytree(
            "customtkinter",
            os.path.join(temp_p, "customtkinter"),
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )
    site_pkg = os.path.join(sys.base_prefix, "Lib", "site-packages")
    for pure_pkg in ["packaging", "darkdetect"]:
        src_pkg = os.path.join(site_pkg, pure_pkg)
        if os.path.isdir(src_pkg):
            shutil.copytree(
                src_pkg,
                os.path.join(temp_p, pure_pkg),
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
            )
    out_zip = os.path.join(SURUMLER_DIR, "Novaboard-Pardus-Kurulumsuz-v1.0.zip")
    zip_directory(temp_p, out_zip, "Novaboard")
    shutil.rmtree(temp_p, ignore_errors=True)
    print(f"  -> {out_zip} hazır.")


def build_all():
    print("=" * 60)
    print("   NOVABOARD TAM DAĞITIM VE DERLEME SİHİRBAZI")
    print("=" * 60)
    os.makedirs(SURUMLER_DIR, exist_ok=True)

    # 1. Tek Dosya EXE (Novaboard-Windows-Kurulumsuz-v1.0.exe)
    print("\n[1/4] Tek dosya taşınabilir Novaboard-Windows-Kurulumsuz-v1.0.exe derleniyor...")
    res_onefile = subprocess.run([sys.executable, "-m", "PyInstaller", "--onefile", *PYINSTALLER_COMMON_ARGS])
    exe_src = os.path.join("dist", "Novaboard.exe")
    if res_onefile.returncode != 0 or not os.path.exists(exe_src):
        print("  [HATA] Novaboard.exe derlenemedi!")
        return False

    shutil.copy2(exe_src, "Novaboard.exe")  # Inno Setup için geçici kopya
    shutil.copy2(exe_src, os.path.join(SURUMLER_DIR, "Novaboard-Windows-Kurulumsuz-v1.0.exe"))
    print("  -> surumler/Novaboard-Windows-Kurulumsuz-v1.0.exe hazır.")

    # 2. Windows Kurulum Sihirbazı (Novaboard-Windows-Kurulumlu-v1.0.exe)
    print("\n[2/4] Inno Setup ile Novaboard-Windows-Kurulumlu-v1.0.exe derleniyor...")
    iscc_candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Inno Setup 6", "ISCC.exe"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    iscc_path = next((p for p in iscc_candidates if os.path.exists(p)), None)
    if iscc_path and os.path.exists("setup.iss"):
        if subprocess.run([iscc_path, "setup.iss"]).returncode == 0 and os.path.exists("Novaboard_Kurulum.exe"):
            shutil.copy2("Novaboard_Kurulum.exe", os.path.join(SURUMLER_DIR, "Novaboard-Windows-Kurulumlu-v1.0.exe"))
            print("  -> surumler/Novaboard-Windows-Kurulumlu-v1.0.exe hazır.")
    else:
        print("  [UYARI] Inno Setup bulunamadı, kurulum sihirbazı atlandı.")

    # 3. Önceden Kurulmuş Windows Klasörü (Novaboard-Windows-Kurulumsuz-v1.0.zip)
    print("\n[3/4] Kurulumsuz hazır Windows klasörü (onedir) oluşturuluyor...")
    res_onedir = subprocess.run([sys.executable, "-m", "PyInstaller", "--onedir", *PYINSTALLER_COMMON_ARGS])
    onedir_output = os.path.join("dist", "Novaboard")
    if res_onedir.returncode == 0 and os.path.exists(onedir_output):
        for extra in WINDOWS_EXTRA_FILES + APP_SOURCE_FILES:
            if os.path.exists(extra):
                shutil.copy2(extra, onedir_output)
        win_zip = os.path.join(SURUMLER_DIR, "Novaboard-Windows-Kurulumsuz-v1.0.zip")
        zip_directory(onedir_output, win_zip, "Novaboard")
        print(f"  -> {win_zip} hazır.")

    # 4. Pardus ETAP / Linux Paketleri (.deb ve .zip)
    print("\n[4/4] Pardus ETAP (MEB Akıllı Tahta) paketleri hazırlanıyor...")
    build_pardus_packages()

    clean_temp_files()
    if os.path.exists(os.path.join(SURUMLER_DIR, "Baslat_Windows.vbs")):
        try:
            os.remove(os.path.join(SURUMLER_DIR, "Baslat_Windows.vbs"))
        except Exception:
            pass

    print("\n" + "=" * 60)
    print("   TÜM 5 SÜRÜM surumler/ KLASÖRÜNDE HAZIRLANDI")
    print("=" * 60)
    return True


if __name__ == "__main__":
    if "--pardus-only" in sys.argv:
        build_pardus_packages()
    elif not build_all():
        sys.exit(1)
