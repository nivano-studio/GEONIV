import os
import re
import hashlib
import mimetypes
import datetime
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from PIL import Image, ExifTags

# HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

# PDF support via pypdf
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    from modules.geo_resolver import reverse_geocode, detect_scrubbing_and_clues, get_reverse_image_search_pivots, resolve_cep_to_location
except ImportError:
    from geo_resolver import reverse_geocode, detect_scrubbing_and_clues, get_reverse_image_search_pivots, resolve_cep_to_location



def compute_file_hashes(filepath: str) -> Dict[str, str]:
    """Calcula Hashes Forenses MD5 e SHA256 para verificação de integridade."""
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()
    
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)
        return {
            "md5": md5_hash.hexdigest(),
            "sha256": sha256_hash.hexdigest()
        }
    except Exception:
        return {"md5": None, "sha256": None}


def format_file_size(size_bytes: int) -> str:
    """Formata tamanho de arquivo em Bytes, KB ou MB."""
    if size_bytes < 1024:
        return f"{size_bytes} Bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def _convert_to_degrees(value) -> float:
    try:
        if isinstance(value, (int, float)):
            return float(value)
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)
    except Exception:
        return 0.0


def extract_image_metadata(filepath: str) -> Dict[str, Any]:
    """Extração avançada de EXIF e GPS para Imagens (JPG, PNG, HEIC, WEBP, TIFF)."""
    result = {
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
        "has_exif": False,
        "error": None
    }

    try:
        with Image.open(filepath) as img:
            result["image_width"] = img.width
            result["image_height"] = img.height

            exif = img.getexif()
            exif_raw = {}
            
            if exif:
                exif_raw = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
            else:
                exif_data = getattr(img, "_getexif", lambda: None)()
                if exif_data:
                    exif_raw = {ExifTags.TAGS.get(k, k): v for k, v in exif_data.items()}

            if exif_raw:
                result["has_exif"] = True
                make = exif_raw.get(ExifTags.Base.Make) or exif_raw.get("Make")
                model = exif_raw.get(ExifTags.Base.Model) or exif_raw.get("Model")
                dt = (exif_raw.get(ExifTags.Base.DateTimeOriginal) or 
                      exif_raw.get(ExifTags.Base.DateTime) or 
                      exif_raw.get("DateTimeOriginal") or 
                      exif_raw.get("DateTime"))
                software = exif_raw.get(ExifTags.Base.Software) or exif_raw.get("Software")

                if make: result["camera_make"] = str(make).strip()
                if model: result["camera_model"] = str(model).strip()
                if dt: result["datetime"] = str(dt).strip()
                if software:
                    sw_str = str(software).strip()
                    result["software"] = sw_str
                    if any(ed in sw_str.lower() for ed in ["photoshop", "gimp", "lightroom", "snapseed", "canva", "picsart", "paint", "vsco"]):
                        result["is_edited"] = True

                # IFD Exif extra
                if hasattr(exif, "get_ifd"):
                    try:
                        exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
                        if exif_ifd:
                            iso = exif_ifd.get(ExifTags.Base.ISOSpeedRatings) or exif_ifd.get(34855)
                            f_num = exif_ifd.get(ExifTags.Base.FNumber) or exif_ifd.get(33437)
                            focal = exif_ifd.get(ExifTags.Base.FocalLength) or exif_ifd.get(37386)
                            exp = exif_ifd.get(ExifTags.Base.ExposureTime) or exif_ifd.get(33434)
                            lens = exif_ifd.get(42036) or exif_ifd.get("LensModel")

                            if iso: result["iso"] = str(iso)
                            if f_num: result["aperture"] = f"f/{float(f_num):.1f}"
                            if focal: result["focal_length"] = f"{float(focal):.1f}mm"
                            if exp: result["exposure_time"] = f"{exp}s"
                            if lens: result["lens_model"] = str(lens).strip()
                    except Exception:
                        pass

                # GPS IFD
                gps_info = {}
                if hasattr(exif, "get_ifd"):
                    gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
                    if gps_ifd:
                        for key, val in gps_ifd.items():
                            sub_tag = ExifTags.GPSTAGS.get(key, key)
                            gps_info[sub_tag] = val

                if not gps_info:
                    raw_gps = exif_raw.get(ExifTags.Base.GPSInfo) or exif_raw.get("GPSInfo")
                    if isinstance(raw_gps, dict):
                        for key, val in raw_gps.items():
                            sub_tag = ExifTags.GPSTAGS.get(key, key)
                            gps_info[sub_tag] = val

                lat_val = gps_info.get("GPSLatitude") or gps_info.get(2)
                lat_ref = gps_info.get("GPSLatitudeRef") or gps_info.get(1)
                lng_val = gps_info.get("GPSLongitude") or gps_info.get(4)
                lng_ref = gps_info.get("GPSLongitudeRef") or gps_info.get(3)

                if lat_val and lat_ref and lng_val and lng_ref:
                    lat = _convert_to_degrees(lat_val)
                    if str(lat_ref).upper() != "N": lat = -lat

                    lng = _convert_to_degrees(lng_val)
                    if str(lng_ref).upper() != "E": lng = -lng

                    result["latitude"] = round(lat, 7)
                    result["longitude"] = round(lng, 7)
                    result["has_gps"] = True

                alt_val = gps_info.get("GPSAltitude") or gps_info.get(6)
                if alt_val is not None:
                    try:
                        result["altitude"] = round(float(alt_val), 1)
                    except Exception:
                        pass

    except Exception as e:
        result["error"] = f"Erro na análise de imagem: {str(e)}"

    return result


def extract_pdf_metadata(filepath: str) -> Dict[str, Any]:
    """Extração avançada de metadados forenses de PDF + Varredura de Texto por CEPs/Coordenadas."""
    result = {
        "title": None,
        "author": None,
        "subject": None,
        "creator": None,
        "producer": None,
        "creation_date": None,
        "mod_date": None,
        "pages_count": 0,
        "is_encrypted": False,
        "extracted_ceps": [],
        "inferred_coords": None,
        "inferred_address": None,
        "clues_found": [],
        "error": None
    }

    if not PYPDF_AVAILABLE:
        result["error"] = "Biblioteca pypdf não instalada."
        return result

    try:
        reader = PdfReader(filepath)
        result["pages_count"] = len(reader.pages)
        result["is_encrypted"] = reader.is_encrypted

        meta = reader.metadata
        if meta:
            result["title"] = meta.title or meta.get("/Title")
            result["author"] = meta.author or meta.get("/Author")
            result["subject"] = meta.subject or meta.get("/Subject")
            result["creator"] = meta.creator or meta.get("/Creator")
            result["producer"] = meta.producer or meta.get("/Producer")

            c_date = meta.get("/CreationDate")
            m_date = meta.get("/ModDate")

            if c_date: result["creation_date"] = str(c_date).replace("D:", "")
            if m_date: result["mod_date"] = str(m_date).replace("D:", "")

        # Varredura de Texto por CEPs e Coordenadas no conteúdo das páginas
        full_text = ""
        max_pages_to_scan = min(10, len(reader.pages))
        for i in range(max_pages_to_scan):
            try:
                page_text = reader.pages[i].extract_text() or ""
                full_text += " " + page_text
            except Exception:
                pass

        if full_text:
            # 1. Busca por CEPs (Ex: 20040-002 ou 20040002)
            found_ceps = re.findall(r'\b\d{5}[-.\s]?\d{3}\b', full_text)
            unique_ceps = list(set(found_ceps))
            if unique_ceps:
                result["extracted_ceps"] = unique_ceps
                # Tentar geolocalizar o primeiro CEP válido encontrado
                for cep in unique_ceps[:3]:
                    loc = resolve_cep_to_location(cep)
                    if loc:
                        result["inferred_coords"] = {
                            "latitude": loc["latitude"],
                            "longitude": loc["longitude"]
                        }
                        result["inferred_address"] = loc["display_name"]
                        result["clues_found"].append(f"CEP {loc['cep']} extraído do texto do PDF ({loc['street']}, {loc['city']}/{loc['uf']})")
                        break

            # 2. Busca por Coordenadas explícitas no texto (Ex: -22.9068, -43.1729)
            if not result["inferred_coords"]:
                coord_match = re.search(r'([-+]?\d{1,2}\.\d{4,7})[,\s_]+([-+]?\d{1,3}\.\d{4,7})', full_text)
                if coord_match:
                    try:
                        lat = float(coord_match.group(1))
                        lng = float(coord_match.group(2))
                        if -90 <= lat <= 90 and -180 <= lng <= 180:
                            result["inferred_coords"] = {"latitude": lat, "longitude": lng}
                            result["clues_found"].append(f"Coordenadas geográficas extraídas do texto do PDF: {lat}, {lng}")
                    except Exception:
                        pass

    except Exception as e:
        result["error"] = f"Erro ao ler PDF: {str(e)}"

    return result


def extract_office_metadata(filepath: str) -> Dict[str, Any]:
    """Extração nativa de metadados de arquivos Office (DOCX, XLSX, PPTX) via estrutura ZIP XML."""
    result = {
        "title": None,
        "author": None,
        "last_modified_by": None,
        "creation_date": None,
        "mod_date": None,
        "application": None,
        "revision": None,
        "words_count": None,
        "pages_count": None,
        "error": None
    }

    try:
        with zipfile.ZipFile(filepath, "r") as z:
            # Ler docProps/core.xml
            if "docProps/core.xml" in z.namelist():
                xml_data = z.read("docProps/core.xml")
                root = ET.fromstring(xml_data)
                
                namespaces = {
                    'dc': 'http://purl.org/dc/elements/1.1/',
                    'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
                    'dcterms': 'http://purl.org/dc/terms/'
                }

                title_elem = root.find('dc:title', namespaces)
                creator_elem = root.find('dc:creator', namespaces)
                last_mod_elem = root.find('cp:lastModifiedBy', namespaces)
                revision_elem = root.find('cp:revision', namespaces)
                created_elem = root.find('dcterms:created', namespaces)
                modified_elem = root.find('dcterms:modified', namespaces)

                if title_elem is not None: result["title"] = title_elem.text
                if creator_elem is not None: result["author"] = creator_elem.text
                if last_mod_elem is not None: result["last_modified_by"] = last_mod_elem.text
                if revision_elem is not None: result["revision"] = revision_elem.text
                if created_elem is not None: result["creation_date"] = created_elem.text
                if modified_elem is not None: result["mod_date"] = modified_elem.text

            # Ler docProps/app.xml
            if "docProps/app.xml" in z.namelist():
                xml_data = z.read("docProps/app.xml")
                root = ET.fromstring(xml_data)
                
                app_elem = root.find('{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Application')
                words_elem = root.find('{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Words')
                pages_elem = root.find('{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Pages') or root.find('{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Slides')

                if app_elem is not None: result["application"] = app_elem.text
                if words_elem is not None: result["words_count"] = words_elem.text
                if pages_elem is not None: result["pages_count"] = pages_elem.text

    except Exception as e:
        result["error"] = f"Erro na análise do arquivo Office: {str(e)}"

    return result


def extract_media_metadata(filepath: str, ext: str) -> Dict[str, Any]:
    """Extração básica de arquivos de áudio/vídeo."""
    result = {
        "media_type": "Áudio" if ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a'] else "Vídeo",
        "duration": None,
        "format": ext.upper().replace(".", ""),
        "error": None
    }
    return result


def analyze_any_file(filepath: str, original_filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Função principal de inteligência e extração forense para qualquer arquivo.
    Classifica automaticamente entre Imagem, PDF, Documento Office, Mídia ou Arquivo Genérico.
    Calcula Hashes MD5/SHA256, realiza Geocodificação Reversa e Inferência OSINT.
    """
    fn = original_filename or os.path.basename(filepath)
    ext = os.path.splitext(fn)[1].lower()
    
    file_size_bytes = os.path.getsize(filepath) if os.path.exists(filepath) else 0
    mime_type, _ = mimetypes.guess_type(fn)

    base_record = {
        "filename": fn,
        "file_ext": ext,
        "file_size": format_file_size(file_size_bytes),
        "file_size_bytes": file_size_bytes,
        "mime_type": mime_type or "application/octet-stream",
        "hashes": compute_file_hashes(filepath),
        "category": "file",
        "has_gps": False,
        "latitude": None,
        "longitude": None,
        "altitude": None,
        "address": None,
        "camera_info": "Não aplicável",
        "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "specific_metadata": {},
        "scrubbing_analysis": None,
        "osint_pivots": get_reverse_image_search_pivots(fn)
    }

    # 1. IMAGENS (.jpg, .jpeg, .png, .heic, .webp, .tiff)
    if ext in ['.jpg', '.jpeg', '.png', '.heic', '.webp', '.tiff', '.bmp']:
        base_record["category"] = "image"
        img_meta = extract_image_metadata(filepath)
        base_record["specific_metadata"] = img_meta

        if img_meta.get("has_gps"):
            base_record["has_gps"] = True
            base_record["latitude"] = img_meta["latitude"]
            base_record["longitude"] = img_meta["longitude"]
            base_record["altitude"] = img_meta.get("altitude")

        # Câmera
        cam = f"{img_meta.get('camera_make', '')} {img_meta.get('camera_model', '')}".strip()
        base_record["camera_info"] = cam if cam else ("Sem metadados EXIF" if not img_meta.get("has_exif") else "Câmera Desconhecida")
        if img_meta.get("datetime"):
            base_record["date_added"] = img_meta["datetime"]

        # Análise de Scrubbing e Clues (para fotos com ou sem GPS)
        scrub = detect_scrubbing_and_clues(fn, has_gps=base_record["has_gps"], has_exif=img_meta.get("has_exif", False))
        base_record["scrubbing_analysis"] = scrub

        # Se não tinha GPS mas a análise inferiu coordenadas por DDD ou nome de arquivo
        if not base_record["has_gps"] and scrub.get("inferred_coords"):
            base_record["latitude"] = scrub["inferred_coords"]["latitude"]
            base_record["longitude"] = scrub["inferred_coords"]["longitude"]
            base_record["has_gps"] = True
            base_record["is_inferred_gps"] = True

    # 2. DOCUMENTOS PDF (.pdf)
    elif ext == '.pdf':
        base_record["category"] = "pdf"
        pdf_meta = extract_pdf_metadata(filepath)
        base_record["specific_metadata"] = pdf_meta
        base_record["camera_info"] = f"PDF ({pdf_meta.get('pages_count', 0)} Pág)"
        if pdf_meta.get("creation_date"):
            base_record["date_added"] = pdf_meta["creation_date"]
        if pdf_meta.get("inferred_coords"):
            base_record["latitude"] = pdf_meta["inferred_coords"]["latitude"]
            base_record["longitude"] = pdf_meta["inferred_coords"]["longitude"]
            base_record["has_gps"] = True
            base_record["is_inferred_gps"] = True


    # 3. DOCUMENTOS OFFICE (.docx, .xlsx, .pptx)
    elif ext in ['.docx', '.xlsx', '.pptx']:
        base_record["category"] = "document"
        office_meta = extract_office_metadata(filepath)
        base_record["specific_metadata"] = office_meta
        base_record["camera_info"] = f"Office {ext.upper().replace('.', '')}"
        if office_meta.get("author"):
            base_record["camera_info"] += f" — Autor: {office_meta['author']}"

    # 4. MÍDIAS DE ÁUDIO / VÍDEO (.mp3, .wav, .mp4, .mov, .m4a, .mkv)
    elif ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.mp4', '.mov', '.avi', '.mkv']:
        base_record["category"] = "audio" if ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a'] else "video"
        media_meta = extract_media_metadata(filepath, ext)
        base_record["specific_metadata"] = media_meta
        base_record["camera_info"] = f"Arquivo de {media_meta['media_type']} ({ext.upper()})"

    # 5. OUTROS ARQUIVOS
    else:
        base_record["category"] = "file"
        base_record["camera_info"] = f"Arquivo {ext.upper()}"

    # 6. Geocodificação Reversa (OSM Nominatim) se tivermos latitude e longitude (reais ou inferidas)
    if base_record.get("latitude") and base_record.get("longitude"):
        base_record["address"] = reverse_geocode(base_record["latitude"], base_record["longitude"])

    return base_record
