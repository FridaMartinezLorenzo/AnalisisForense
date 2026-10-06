from PIL import Image
import piexif

def insertar_exif(input_img, output_img, texto="Hola esto es una prueba de extraccion de texto EXIF"):
    img = Image.open(input_img)
    
    # Cargar EXIF existente o crear uno nuevo
    try:
        exif_dict = piexif.load(img.info.get('exif', b""))
    except:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    
    # Insertar texto en UserComment
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = texto.encode("utf-8")
    
    exif_bytes = piexif.dump(exif_dict)
    img.save(output_img, exif=exif_bytes)

    print(f"[OK] Texto '{texto}' insertado en EXIF -> {output_img}")

if __name__ == "__main__":
    insertar_exif("imgs/img1.jpg", "imgs/img1_exif.jpg")
