import os
from typing import Dict, Any, Optional
from PIL import Image, ExifTags

# Registrar suporte a fotos de iPhone (.HEIC)
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except Exception:
    pass


def _convert_to_degrees(value) -> float:
    try:
        if isinstance(value, (int, float)):
            return float(value)
        if hasattr(value, "__getitem__") and len(value) >= 3:
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        return float(value)
    except Exception:
        return 0.0


def extract_metadata(image_path: str) -> Dict[str, Any]:
    """
    Extração Avançada de Metadados Forenses EXIF para OSINT/GEOINT.
    Detecta GPS, Câmera, Lente, ISO, Abertura, Software de Edição e Resolução.
    """
    result: Dict[str, Any] = {
        "has_gps": False,
        "latitude": None,
        "longitude": None,
        "altitude": None,
        "datetime": None,
        "camera_make": None,
        "camera_model": None,
        "software": None,
        "is_edited": False,
        "iso": None,
        "aperture": None,
        "focal_length": None,
        "exposure_time": None,
        "lens_model": None,
        "image_width": None,
        "image_height": None,
        "error": None
    }
    
    if not os.path.exists(image_path):
        result["error"] = "Arquivo não encontrado"
        return result
        
    try:
        with Image.open(image_path) as img:
            result["image_width"] = int(img.width)
            result["image_height"] = int(img.height)

            exif = img.getexif()
            exif_raw = {}
            if exif:
                exif_raw = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
            else:
                exif_data = getattr(img, "_getexif", lambda: None)()
                if exif_data:
                    exif_raw = {ExifTags.TAGS.get(k, k): v for k, v in exif_data.items()}

            if not exif_raw and not exif:
                result["error"] = "Nenhum metadado EXIF encontrado nesta foto."
                return result

            make = exif_raw.get("Make") or (exif.get(ExifTags.Base.Make) if exif else None)
            model = exif_raw.get("Model") or (exif.get(ExifTags.Base.Model) if exif else None)
            dt = (exif_raw.get("DateTimeOriginal") or exif_raw.get("DateTime") or 
                  (exif.get(ExifTags.Base.DateTimeOriginal) if exif else None) or 
                  (exif.get(ExifTags.Base.DateTime) if exif else None))
            software = exif_raw.get("Software") or (exif.get(ExifTags.Base.Software) if exif else None)

            if make:
                result["camera_make"] = str(make).strip()
            if model:
                result["camera_model"] = str(model).strip()
            if dt:
                result["datetime"] = str(dt).strip()
            if software:
                sw_str = str(software).strip()
                result["software"] = sw_str
                sw_lower = sw_str.lower()
                if any(ed in sw_lower for ed in ["photoshop", "gimp", "lightroom", "snapseed", "canva", "picsart", "vsco"]):
                    result["is_edited"] = True

            # Extração de IFD Exif para ISO, Abertura e Lente
            if exif and hasattr(exif, "get_ifd"):
                try:
                    exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
                    if exif_ifd:
                        iso = exif_ifd.get(ExifTags.Base.ISOSpeedRatings) or exif_ifd.get(34855)
                        f_number = exif_ifd.get(ExifTags.Base.FNumber) or exif_ifd.get(33437)
                        focal = exif_ifd.get(ExifTags.Base.FocalLength) or exif_ifd.get(37386)
                        exp = exif_ifd.get(ExifTags.Base.ExposureTime) or exif_ifd.get(33434)
                        lens = exif_ifd.get(42036) or exif_ifd.get("LensModel")

                        if iso: result["iso"] = str(iso)
                        if f_number: result["aperture"] = f"f/{float(f_number):.1f}"
                        if focal: result["focal_length"] = f"{float(focal):.1f}mm"
                        if exp: result["exposure_time"] = f"{exp}s"
                        if lens: result["lens_model"] = str(lens).strip()
                except Exception:
                    pass

            # Extrair dados de GPS usando IFD GPSInfo
            gps_info = {}
            if exif and hasattr(exif, "get_ifd"):
                try:
                    gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
                    if gps_ifd:
                        for key, val in gps_ifd.items():
                            sub_tag = ExifTags.GPSTAGS.get(key, key)
                            gps_info[sub_tag] = val
                except Exception:
                    pass
            
            if not gps_info:
                raw_gps = exif_raw.get("GPSInfo") or (exif.get(ExifTags.Base.GPSInfo) if exif else None)
                if raw_gps and isinstance(raw_gps, dict):
                    for key, val in raw_gps.items():
                        sub_tag = ExifTags.GPSTAGS.get(key, key)
                        gps_info[sub_tag] = val

            lat_val = gps_info.get("GPSLatitude") or gps_info.get(2)
            lat_ref = gps_info.get("GPSLatitudeRef") or gps_info.get(1)
            lng_val = gps_info.get("GPSLongitude") or gps_info.get(4)
            lng_ref = gps_info.get("GPSLongitudeRef") or gps_info.get(3)

            if lat_val and lat_ref and lng_val and lng_ref:
                lat = _convert_to_degrees(lat_val)
                if str(lat_ref).upper() != "N":
                    lat = -lat
                    
                lng = _convert_to_degrees(lng_val)
                if str(lng_ref).upper() != "E":
                    lng = -lng
                    
                result["latitude"] = round(float(lat), 7)
                result["longitude"] = round(float(lng), 7)
                result["has_gps"] = True

            alt_val = gps_info.get("GPSAltitude") or gps_info.get(6)
            if alt_val is not None:
                try:
                    result["altitude"] = round(float(alt_val), 1)
                except Exception:
                    pass

    except Exception as e:
        result["error"] = f"Erro ao ler metadados forenses EXIF: {str(e)}"

    return result
