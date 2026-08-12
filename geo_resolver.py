import re
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

# Cache em memória para requisições de Reverse Geocoding
_REVERSE_GEOCODE_CACHE: Dict[str, Dict[str, Any]] = {}

# Importar banco de DDDs se disponível em phone_osint
try:
    from phone_osint import DDD_MAP
except ImportError:
    DDD_MAP = {}

def reverse_geocode(lat: float, lng: float) -> Dict[str, Any]:
    """
    Realiza Geocodificação Reversa via OpenStreetMap Nominatim.
    Converte latitude e longitude em endereço detalhado (Rua, Bairro, Cidade, Estado, País, CEP).
    """
    if lat is None or lng is None:
        return {"success": False, "address": None}

    cache_key = f"{round(lat, 4)},{round(lng, 4)}"
    if cache_key in _REVERSE_GEOCODE_CACHE:
        return _REVERSE_GEOCODE_CACHE[cache_key]

    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=18&addressdetails=1"
    
    headers = {
        'User-Agent': 'GEONIV-OSINT-Platform/2.0 (Forensic Analysis & OSINT Tool)'
    }

    result = {
        "success": False,
        "display_name": None,
        "road": None,
        "neighbourhood": None,
        "suburb": None,
        "city": None,
        "state": None,
        "country": None,
        "postcode": None,
        "error": None
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            
            if "display_name" in data:
                addr = data.get("address", {})
                city = addr.get("city") or addr.get("town") or addr.get("municipality") or addr.get("village") or addr.get("county")
                road = addr.get("road") or addr.get("pedestrian") or addr.get("street")
                suburb = addr.get("suburb") or addr.get("neighbourhood") or addr.get("residential")
                
                result.update({
                    "success": True,
                    "display_name": data.get("display_name"),
                    "road": road,
                    "suburb": suburb,
                    "city": city,
                    "state": addr.get("state"),
                    "country": addr.get("country"),
                    "postcode": addr.get("postcode")
                })
    except Exception as e:
        result["error"] = f"Geocodificação indisponível offline/timeout: {str(e)}"

def lookup_cep(cep: str) -> Optional[Dict[str, Any]]:
    """Consulta CEP na API ViaCEP."""
    try:
        cep_clean = re.sub(r'\D', '', cep)
        if len(cep_clean) != 8:
            return None
        url = f"https://viacep.com.br/ws/{cep_clean}/json/"
        req = urllib.request.Request(url, headers={'User-Agent': 'GEONIV-OSINT/2.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if 'erro' not in data:
                return data
    except Exception:
        pass
    return None


def geocode_address_query(query: str) -> Optional[Dict[str, Any]]:
    """Geocodificação direta de endereço (Texto -> Lat/Lng) via OpenStreetMap Nominatim."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={encoded}&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'GEONIV-OSINT-Platform/2.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data and len(data) > 0:
                item = data[0]
                return {
                    "latitude": float(item["lat"]),
                    "longitude": float(item["lon"]),
                    "display_name": item.get("display_name")
                }
    except Exception:
        pass
    return None


def resolve_cep_to_location(cep: str) -> Optional[Dict[str, Any]]:
    """Converte um CEP brasileiro em Coordenadas Geográficas (Lat/Lng) e Endereço."""
    cep_info = lookup_cep(cep)
    if not cep_info:
        return None

    street = cep_info.get('logradouro', '')
    neighborhood = cep_info.get('bairro', '')
    city = cep_info.get('localidade', '')
    uf = cep_info.get('uf', '')

    query_parts = [p for p in [street, neighborhood, city, uf, 'Brasil'] if p]
    query_str = ", ".join(query_parts)

    geo_res = geocode_address_query(query_str)
    if geo_res:
        return {
            "cep": cep_info.get("cep"),
            "latitude": geo_res["latitude"],
            "longitude": geo_res["longitude"],
            "display_name": geo_res["display_name"],
            "city": city,
            "uf": uf,
            "street": street,
            "neighborhood": neighborhood
        }
    return None



def detect_scrubbing_and_clues(filename: str, has_gps: bool = False, has_exif: bool = False) -> Dict[str, Any]:
    """
    Análise de origem e descarte (scrubbing) de metadados para mídias sem EXIF/GPS.
    Detecta marcas d'água em nome de arquivo (WhatsApp, Telegram, Screenshot) e infere localização visual.
    """
    res = {
        "scrubbing_detected": False,
        "scrubbing_source": None,
        "explanation": None,
        "inferred_coords": None,
        "inferred_location_name": None,
        "clues_found": []
    }

    fn_upper = filename.upper()

    # 1. Detecção de Descarte (Scrubbing) por Redes Sociais
    if not has_gps:
        if "WA" in fn_upper or "WHATSAPP" in fn_upper or re.search(r'IMG-\d{8}-WA', filename, re.IGNORECASE):
            res["scrubbing_detected"] = True
            res["scrubbing_source"] = "WhatsApp"
            res["explanation"] = "O WhatsApp remove automaticamente todos os metadados EXIF e GPS da imagem por motivos de privacidade do usuário antes da transmissão."
            res["clues_found"].append("Padronização de nome detectada: Envio via WhatsApp")

        elif "TELEGRAM" in fn_upper or "PHOTO_" in fn_upper or "DOC_" in fn_upper:
            res["scrubbing_detected"] = True
            res["scrubbing_source"] = "Telegram / Mensageiro"
            res["explanation"] = "O Telegram remove os metadados EXIF de fotos enviadas como imagem comum. (Apenas o envio como 'Arquivo' preserva o EXIF)."
            res["clues_found"].append("Padrão de nome típico do Telegram")

        elif "FB_IMG" in fn_upper or "FACEBOOK" in fn_upper:
            res["scrubbing_detected"] = True
            res["scrubbing_source"] = "Facebook"
            res["explanation"] = "O Facebook elimina metadados EXIF e insere identificadores proprietários de compressão."
            res["clues_found"].append("Marca de arquivo baixado do Facebook")

        elif "SCREENSHOT" in fn_upper or "CAPTURA" in fn_upper or "PRNT" in fn_upper:
            res["scrubbing_detected"] = True
            res["scrubbing_source"] = "Captura de Tela (Screenshot)"
            res["explanation"] = "Capturas de tela criam um arquivo de imagem novo sem o EXIF do sensor da câmera original."
            res["clues_found"].append("Captura de tela do sistema operacional")

        elif not has_exif:
            res["scrubbing_detected"] = True
            res["scrubbing_source"] = "Software de Edição ou Rede Social"
            res["explanation"] = "Metadados EXIF ausentes. O arquivo pode ter sido exportado por editor gráfico (Photoshop, Canva) ou baixado da web."

    # 2. Busca por Coordenadas no Nome do Arquivo (Ex: lat-23.5505_lon-46.6333)
    coord_match = re.search(r'([-+]?\d{1,2}\.\d{4,7})[,\s_]+([-+]?\d{1,3}\.\d{4,7})', filename)
    if coord_match:
        try:
            lat = float(coord_match.group(1))
            lng = float(coord_match.group(2))
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                res["inferred_coords"] = {"latitude": lat, "longitude": lng}
                res["clues_found"].append(f"Coordenadas extraídas do nome do arquivo: {lat}, {lng}")
        except Exception:
            pass

    # 3. Busca por Códigos de DDD no Nome do Arquivo (Ex: DDD11, (11), DDD-21)
    ddd_match = re.search(r'(?:DDD[_\s-]?)?\(?([1-9]{2})\)?', filename, re.IGNORECASE)
    if ddd_match and DDD_MAP:
        ddd_code = ddd_match.group(1)
        if ddd_code in DDD_MAP:
            ddd_info = DDD_MAP[ddd_code]
            res["inferred_location_name"] = f"DDD {ddd_code} — {ddd_info.get('city')}/{ddd_info.get('uf')}"
            if not res["inferred_coords"]:
                res["inferred_coords"] = {
                    "latitude": ddd_info.get("lat"),
                    "longitude": ddd_info.get("lng")
                }
            res["clues_found"].append(f"Indicativo regional DDD {ddd_code} ({ddd_info.get('city')}/{ddd_info.get('uf')})")

    return res


def get_reverse_image_search_pivots(filename: str, photo_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Gera atalhos diretos de investigação OSINT para Busca Reversa de Imagem Visual
    (Yandex, Google Lens, TinEye, Bing, GeoSpy AI).
    """
    encoded_url = urllib.parse.quote(photo_url or "") if photo_url else ""
    
    return {
        "google_lens": {
            "name": "Google Lens",
            "icon": "fa-brands fa-google",
            "color": "#4285f4",
            "url": "https://lens.google.com/",
            "description": "Reconhecimento de objetos, texto, marcos históricos e locais."
        },
        "yandex_images": {
            "name": "Yandex Visual GEOINT",
            "icon": "fa-solid fa-eye",
            "color": "#ff0000",
            "url": "https://yandex.com/images/search",
            "description": "Líder mundial em geolocalização OSINT por correspondência visual de estruturas."
        },
        "bing_visual": {
            "name": "Bing Visual Search",
            "icon": "fa-brands fa-microsoft",
            "color": "#00838f",
            "url": "https://www.bing.com/visualsearch",
            "description": "Identificação de arquitetura e pesquisa visual."
        },
        "tineye": {
            "name": "TinEye Reverse Search",
            "icon": "fa-solid fa-robot",
            "color": "#0284c7",
            "url": "https://tineye.com/",
            "description": "Rastreamento da versão mais antiga e sem edição da imagem na web."
        },
        "geospy": {
            "name": "GeoSpy AI (GEOINT)",
            "icon": "fa-solid fa-brain",
            "color": "#10b981",
            "url": "https://geospy.ai/",
            "description": "IA especializada em prever coordenadas geográficas a partir de elementos da paisagem."
        }
    }
