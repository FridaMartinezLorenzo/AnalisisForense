#!/usr/bin/env python3
from PIL import Image

def ocultar_lsb_bytes(input_img, output_img, mensaje="Hola esta es una prueba para detección de estenografia lsb", terminator='§'):
    # codificar a bytes UTF-8 e incluir terminador
    payload = (mensaje + terminator).encode('utf-8')
    # convertir payload a cadena de bits
    mensaje_bin = ''.join(format(b, '08b') for b in payload)

    img = Image.open(input_img)
    img = img.convert("RGB")
    pixels = img.load()

    ancho, alto = img.size
    total_pixels = ancho * alto
    required_bits = len(mensaje_bin)
    if required_bits > total_pixels:
        print("[ERROR] Imagen demasiado pequeña. Necesitas al menos", required_bits, "píxeles (bits).")
        return

    idx = 0
    for y in range(alto):
        for x in range(ancho):
            if idx >= len(mensaje_bin):
                img.save(output_img)
                print(f"[OK] Mensaje insertado en {output_img}")
                return

            r, g, b = pixels[x, y]
            # escribir solo en LSB del canal rojo (como en tu versión)
            r = (r & ~1) | int(mensaje_bin[idx])
            idx += 1
            pixels[x, y] = (r, g, b)

    # en caso de no terminar (no debería pasar)
    img.save(output_img)
    print("[ERROR] Proceso terminó sin alcanzar todo el mensaje, revisa tamaños.")

if __name__ == "__main__":
    ocultar_lsb_bytes("imgs/ejemplo.png", "imgs/img1_output_lsb_fixed.png")
