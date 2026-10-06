def append_text(filename, output, texto="HOLA"):
    with open(filename, "rb") as f:
        data = f.read()
    with open(output, "wb") as f:
        f.write(data)
        f.write(b"\nHola esto es una prueba para insercion de texto de tipo file padding\n")
    print(f"[OK] Bytes agregados al final: ->", output)

if __name__ == "__main__":
    append_text("imgs/img1.jpg", "imgs/img1_oculta.jpg")
