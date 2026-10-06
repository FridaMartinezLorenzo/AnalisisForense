#!/usr/bin/env python3
from PIL import Image

def extract_text_from_lsb_red(image_path, terminator='§'):
    img = Image.open(image_path).convert("RGB")
    pixels = img.load()
    w, h = img.size

    bit_buffer = ""
    byte_buffer = bytearray()

    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            bit_buffer += str(r & 1)

            # Cada 8 bits = 1 byte
            if len(bit_buffer) == 8:
                byte_value = int(bit_buffer, 2)
                byte_buffer.append(byte_value)
                bit_buffer = ""

                # Intentar decodificar solo el último carácter insertado
                try:
                    ultimo_char = byte_buffer.decode("utf-8", errors="strict")[-1]
                except Exception:
                    continue  # todavía no es un carácter UTF-8 completo

                # Detectar terminador exacto
                if ultimo_char == terminator:
                    # Decodificar el mensaje completo
                    mensaje = byte_buffer.decode("utf-8", errors="strict")
                    # quitar terminador
                    return mensaje[:-1]

    return "[ERROR] No se encontró terminador"


if __name__ == "__main__":
    import sys
    img = sys.argv[1] if len(sys.argv) > 1 else "imgs/img1_output_lsb_fixed.png"
    mensaje = extract_text_from_lsb_red(img)
    print("MENSAJE EXTRAÍDO:", mensaje)
