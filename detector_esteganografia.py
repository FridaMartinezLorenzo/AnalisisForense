#!/usr/bin/env python3
import piexif
from PIL import Image
import os

# ============================
# EXTRACCIÓN LSB (canal rojo)
# ============================
def extract_lsb_red(image_path, terminator='§'):
    try:
        img = Image.open(image_path).convert("RGB")
    except:
        return None

    pixels = img.load()
    bits = []

    # leer solo canal rojo
    for y in range(img.height):
        for x in range(img.width):
            bits.append(str(pixels[x, y][0] & 1))

    # bits → bytes
    byte_vals = []
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            break
        byte_vals.append(int(''.join(chunk), 2))

    data = bytes(byte_vals)

    try:
        text = data.decode('utf-8', errors='ignore')
    except:
        text = ''.join(chr(b) for b in data)

    # cortar en terminador si existe
    if terminator in text:
        return text.split(terminator)[0]

    # eliminar basura nula
    text = text.split('\x00')[0]

    # si el texto parece vacío, no reportes nada
    clean = text.strip()
    return clean if len(clean) >= 1 else None


# ============================
# EXTRACCIÓN EXIF
# ============================
def extract_exif_comment(image_path):
    try:
        img = Image.open(image_path)
        exif_bytes = img.info.get("exif", None)
        if not exif_bytes:
            return None

        exif_dict = piexif.load(exif_bytes)

        user_comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment, None)
        if user_comment:
            try:
                text = user_comment.decode("utf-8", errors="ignore").strip()
                return text if text else None
            except:
                return None

    except Exception:
        pass
    return None


# ============================
# EXTRACCIÓN FILE PADDING
# ============================
def extract_file_padding(image_path):
    suspicious_strings = [
        b"HOLA", b"TEST", b"SECRET", b"PRUEBA", b"ESTE", b"OCULTO",
        b"padding", b"hidden", b"stego", b"estenografia"
    ]

    try:
        with open(image_path, "rb") as f:
            data = f.read()
    except:
        return None

    # buscar texto ASCII en el último 5% del archivo
    tail = data[-int(len(data) * 0.05):]

    try:
        decoded = tail.decode("utf-8", errors="ignore")
    except:
        return None

    # detectar cadenas sospechosas
    for s in suspicious_strings:
        if s.decode("utf-8", "ignore") in decoded:
            return decoded.strip()

    # si hay mucho texto imprimible, también lo reportamos
    printable = ''.join(c for c in decoded if 32 <= ord(c) <= 126 or c in "\n\r\t")
    if len(printable.strip()) > 10:
        return printable.strip()

    return None


# ============================
# SCRIPT PRINCIPAL
# ============================
def analizar_imagen(image_path):
    print(f"\n===== ANALIZANDO {image_path} =====")

    results = {}

    # probar LSB
    lsb = extract_lsb_red(image_path)
    if lsb:
        results["LSB (canal rojo)"] = lsb

    # probar EXIF
    exif = extract_exif_comment(image_path)
    if exif:
        results["EXIF UserComment"] = exif

    # probar file padding
    padding = extract_file_padding(image_path)
    if padding:
        results["File Padding"] = padding

    # reporte final
    if not results:
        print("→ No se detectó esteganografía evidente.")
    else:
        print("→ Posible esteganografía detectada:")
        print("--------------------------------------")
        for tipo, contenido in results.items():
            print(f"[{tipo}]")
            print(contenido)
            print("--------------------------------------")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python3 detector_esteganografia.py imagen.jpg")
    else:
        analizar_imagen(sys.argv[1])
