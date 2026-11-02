#!/bin/bash
# ========================================================================
# Novaboard - Pardus / Linux Kolay Kurulum Betiği
# Geliştirici: Efe Saçlı
# ========================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "      NOVABOARD PARDUS / LINUX KURULUM SİHİRBAZI         "
echo "=========================================================="

INSTALL_DIR="$HOME/.local/share/novaboard"
APP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
DESKTOP_DIR="$HOME/Masaüstü"

if [ ! -d "$DESKTOP_DIR" ]; then
    DESKTOP_DIR="$HOME/Desktop"
fi

echo "1. Dosyalar kopyalanıyor ($INSTALL_DIR)..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$APP_DIR"
mkdir -p "$ICON_DIR"

cp -r *.py *.png *.ico requirements.txt baslat.sh "$INSTALL_DIR/"
for pkg in customtkinter packaging darkdetect; do
    if [ -d "$DIR/$pkg" ]; then
        cp -r "$DIR/$pkg" "$INSTALL_DIR/"
    fi
done
chmod +x "$INSTALL_DIR/baslat.sh"

echo "2. Uygulama ikonu yükleniyor..."
cp icon.png "$ICON_DIR/novaboard.png"

echo "3. Menü kısayolu oluşturuluyor..."
cat << EOF > "$APP_DIR/novaboard.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Novaboard
GenericName=Akıllı Tahta ve Öğretmen Asistanı
Comment=Öğretmenler için modern kura, sayaç, grup oluşturucu ve tahta araçları
Exec=/bin/bash "$INSTALL_DIR/baslat.sh"
Path=$INSTALL_DIR
Icon=$ICON_DIR/novaboard.png
Terminal=false
Categories=Education;Teaching;Utility;
StartupNotify=false
EOF

chmod +x "$APP_DIR/novaboard.desktop"

if [ -d "$DESKTOP_DIR" ]; then
    cp "$APP_DIR/novaboard.desktop" "$DESKTOP_DIR/novaboard.desktop"
    chmod +x "$DESKTOP_DIR/novaboard.desktop"
    if command -v gio >/dev/null 2>&1; then
        gio set "$DESKTOP_DIR/novaboard.desktop" metadata::trusted true 2>/dev/null || true
    fi
    echo "4. Masaüstü kısayolu eklendi ($DESKTOP_DIR)."
fi

echo ""
echo "=========================================================="
echo "  KURULUM BAŞARIYLA TAMAMLANDI!"
echo "  - Novaboard artık Pardus Başlat Menüsü > Eğitim altında."
echo "  - Masaüstünüze Novaboard kısayolu eklendi."
echo "=========================================================="
