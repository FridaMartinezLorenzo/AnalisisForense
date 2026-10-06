#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SUPPORTED_EXT="jpg|jpeg|png|bmp|gif"
REPORT_DIR="./reports"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
REPORT_FILE="${REPORT_DIR}/reporte_forense_${TIMESTAMP}.txt"
TMPDIR="$(mktemp -d)"

MIN_STRING_LEN=8
SUSPICIOUS_STR_COUNT=5

mkdir -p "$REPORT_DIR"
touch "$REPORT_FILE"

trap 'rm -rf "$TMPDIR"' EXIT

log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$REPORT_FILE"
}

log_header() {
    echo "========================================" | tee -a "$REPORT_FILE"
    log "$1"
    echo "----------------------------------------" | tee -a "$REPORT_FILE"
}

check_deps() {
    local deps=(exiftool strings binwalk steghide file identify pngcheck python3)
    for d in "${deps[@]}"; do
        if ! command -v "$d" >/dev/null; then
            echo "Falta dependencia: $d"
            exit 1
        fi
    done
}


#########################################
### ANALIZAR ARCHIVO
#########################################
analyze_file() {
    local img="$1"
    local base="$(basename "$img")"
    local safe="${base// /_}"
    safe="${safe//\//_}"
    local out="$TMPDIR/$safe"

    local SUSPICIOUS=0

    log_header "Analizando archivo: $img"
    echo "Ruta absoluta: $(realpath "$img")" >> "$REPORT_FILE"

    #########################################
    # FILE MAGIC
    #########################################
    file "$img" | tee -a "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"


    #########################################
    # EXIF
    #########################################
    exiftool "$img" > "${out}.exif" 2>/dev/null || true
    echo "[EXIF] Campos detectados:" >> "$REPORT_FILE"

    if grep -Ei 'Comment|Description|Artist|Software|UserComment' "${out}.exif" >> "$REPORT_FILE"; then
        SUSPICIOUS=1
    else
        echo "  (Ninguno)" >> "$REPORT_FILE"
    fi
    echo "" >> "$REPORT_FILE"


    #########################################
    # STRINGS
    #########################################
    strings -n 6 "$img" > "${out}.strings"
    echo "[STRINGS] Total encontradas: $(wc -l < "${out}.strings")" >> "$REPORT_FILE"

    grep -Ei 'secret|flag|key|password|hidden|steg|crypto' "${out}.strings" > "${out}.susp" || true
    if [ -s "${out}.susp" ]; then
        echo "  Palabras sospechosas:" >> "$REPORT_FILE"
        cat "${out}.susp" >> "$REPORT_FILE"
        SUSPICIOUS=1
    fi
    echo "" >> "$REPORT_FILE"


    #########################################
    # BASE64
    #########################################
    grep -Eo '[A-Za-z0-9+/]{50,}={0,2}' "${out}.strings" > "${out}.b64" || true

    if [ -s "${out}.b64" ]; then
        echo "[BASE64] Detectado bloque Base64. Intentando decodificar..." >> "$REPORT_FILE"
        SUSPICIOUS=1

        while read -r block; do
            decoded=$(echo "$block" | base64 -d 2>/dev/null || true)
            if [[ -n "$decoded" ]]; then
                echo "  -> Decodificación exitosa:" >> "$REPORT_FILE"
                echo "$decoded" | head -n 20 >> "$REPORT_FILE"
                echo "" >> "$REPORT_FILE"
            fi
        done < "${out}.b64"
    fi

    echo "" >> "$REPORT_FILE"


    #########################################
    # BINWALK
    #########################################
    binwalk "$img" > "${out}.binwalk"
    echo "[BINWALK] Resultados:" >> "$REPORT_FILE"
    cat "${out}.binwalk" | head -n 20 >> "$REPORT_FILE"

    if grep -qiE "Zip|RAR|PNG|JPEG|data" "${out}.binwalk"; then
        SUSPICIOUS=1
    fi

    echo "" >> "$REPORT_FILE"


    #########################################
    # STEGHIDE
    #########################################
    echo "[STEGHIDE]" >> "$REPORT_FILE"
    if steghide info -sf "$img" >> "$REPORT_FILE" 2>&1; then
        SUSPICIOUS=1
    fi
    echo "" >> "$REPORT_FILE"



    #########################################
    # SI ES SOSPECHOSO → EJECUTAR PYTHON STEGO
    #########################################
    if [[ "$SUSPICIOUS" -eq 1 ]]; then
        echo "[*] Archivo marcado como SUSPECHOSO. Ejecutando detector_esteganografia.py ..." >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"

        if [ -f "./detector_esteganografia.py" ]; then
            python3 detector_esteganografia.py "$img" > "${out}.py_stego" 2>/dev/null || true

            if [ -s "${out}.py_stego" ]; then
                echo "===== RESULTADOS AVANZADOS DE ESTEGANOGRAFÍA =====" >> "$REPORT_FILE"
                cat "${out}.py_stego" >> "$REPORT_FILE"
                echo "" >> "$REPORT_FILE"
            else
                echo "(Sin datos del script Python)" >> "$REPORT_FILE"
            fi
        else
            echo "  [ERROR] Script detector_esteganografia.py NO encontrado." >> "$REPORT_FILE"
        fi

    else
        echo "[OK] Archivo no presenta anomalías fuertes. No se ejecuta stego avanzado." >> "$REPORT_FILE"
    fi


    echo "" >> "$REPORT_FILE"
    log "Archivo finalizado."
}



#########################################
### MAIN
#########################################
main() {
    if [ $# -ne 1 ]; then
        echo "Uso: $0 carpeta"
        exit 1
    fi

    local folder="$1"
    check_deps
    log_header "INICIO DE ANÁLISIS"

    shopt -s nullglob
    for img in "$folder"/*; do
        if [[ "$img" =~ \.($SUPPORTED_EXT)$ ]]; then
            analyze_file "$img"
        fi
    done

    log_header "ANÁLISIS COMPLETADO"
}

main "$@"
