#!/bin/bash
# ========================================================================
# Novaboard - Akıllı Tahta & Öğretmen Asistanı (Pardus / Linux Başlatıcı)
# Geliştirici: Efe Saçlı
# ========================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
if [ -z "$DIR" ] || [ ! -f "$DIR/app.py" ]; then
    if [ -f "/opt/novaboard/app.py" ]; then
        DIR="/opt/novaboard"
    elif [ -f "$HOME/.local/share/novaboard/app.py" ]; then
        DIR="$HOME/.local/share/novaboard"
    fi
fi

cd "$DIR" || exit 1
export PYTHONPATH="$DIR:$PYTHONPATH"

# Log dizini
LOG_DIR="$HOME/.config/Novaboard"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/novaboard.log"
: > "$LOG_FILE"

# Python 3 kontrolü
if ! command -v python3 >/dev/null 2>&1; then
    ERR="Python 3 sisteminizde bulunamadı! Lütfen kurunuz: sudo apt install -y python3 python3-tk python3-pil"
    echo "$ERR" >> "$LOG_FILE"
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --no-markup --title="Novaboard" --text="$ERR" --width=450
    fi
    exit 1
fi

# Eksik sistem paketi kontrolü (yalnızca tkinter veya PIL eksikse)
if ! python3 -c "import tkinter, PIL" >/dev/null 2>&1; then
    if command -v pkexec >/dev/null 2>&1; then
        pkexec apt-get install -y python3-tk python3-pil python3-pil.imagetk >/dev/null 2>&1 || true
    fi
fi

# Uygulamayı doğrudan başlat
python3 "$DIR/app.py" "$@" >>"$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    ERR_DETAILS=$(tail -n 20 "$LOG_FILE" 2>/dev/null)
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --no-markup --title="Novaboard - Başlatma Hatası" \
            --text="Novaboard başlatılamadı (Kod: $EXIT_CODE).\n\nHata ayrıntısı:\n$ERR_DETAILS\n\nLog: $LOG_FILE" \
            --width=540
    elif command -v notify-send >/dev/null 2>&1; then
        notify-send "Novaboard Hatası" "$ERR_DETAILS"
    fi
    exit $EXIT_CODE
fi
