import os
import json
import uuid
import math
import socket
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
from PIL import Image

from modules.exif_extractor import extract_metadata
from modules.metadata_extractor import analyze_any_file
from modules.phone_osint import phone_lookup


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Teste dinâmico de permissão de escrita para compatibilidade total com Vercel
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
DATA_FILE = os.path.join(BASE_DIR, "geoniv_data.json")

try:
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    test_file = os.path.join(UPLOADS_DIR, ".write_test")
    with open(test_file, "w") as f:
        f.write("ok")
    os.remove(test_file)
except Exception:
    UPLOADS_DIR = "/tmp/uploads"
    DATA_FILE = "/tmp/geoniv_data.json"
    os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI(title="GEONIV 3D - Plataforma de Inteligência OSINT & GEOINT")

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# --- GERENCIAMENTO DE DADOS LOCAL (JSON) COM SUPORTE A READ-ONLY ---
def load_records() -> list:
    target_file = DATA_FILE
    if not os.path.exists(target_file):
        seed_file = os.path.join(BASE_DIR, "geoniv_data.json")
        if os.path.exists(seed_file):
            target_file = seed_file
        else:
            return []
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_records(records: list):
    target_file = DATA_FILE
    try:
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except (PermissionError, OSError):
        tmp_file = "/tmp/geoniv_data.json"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

def generate_next_code(records: list) -> str:
    count = len(records) + 1
    return f"GEO-{count:03d}"

# --- ROTAS DA INTERFACE WEB ---
@app.get("/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
@app.get("/api/", response_class=HTMLResponse)
@app.get("/api/index", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- API ENDPOINTS ---
@app.get("/api/boxes")
@app.get("/api/records")
async def get_all_records():
    return load_records()

@app.post("/api/upload")
async def upload_geo_photo(
    file: UploadFile = File(...),
    notes: str = Form("")
):
    records = load_records()
    
    ext = os.path.splitext(file.filename)[1].lower()
    unique_id = uuid.uuid4().hex[:10]
    
    final_filename = f"file_{unique_id}{ext}"
    final_path = os.path.join(UPLOADS_DIR, final_filename)
    
    with open(final_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Se for imagem, também salvamos uma versão otimizada se necessário
    if ext in ['.jpg', '.jpeg', '.png', '.heic', '.webp', '.tiff', '.bmp']:
        jpg_filename = f"img_{unique_id}.jpg"
        jpg_path = os.path.join(UPLOADS_DIR, jpg_filename)
        try:
            with Image.open(final_path) as img:
                rgb_img = img.convert("RGB")
                rgb_img.save(jpg_path, "JPEG", quality=88)
            file_url = f"/uploads/{jpg_filename}"
        except Exception:
            file_url = f"/uploads/{final_filename}"
    else:
        file_url = f"/uploads/{final_filename}"
        
    meta = analyze_any_file(final_path, file.filename)
    
    record_id = str(uuid.uuid4())
    code = generate_next_code(records)
    
    spec = meta.get("specific_metadata", {})

    new_record = {
        "id": record_id,
        "code": code,
        "title": file.filename,
        "notes": notes,
        "photo_url": file_url,
        "filename": file.filename,
        "category": meta.get("category", "file"),
        "file_size": meta.get("file_size"),
        "file_size_bytes": meta.get("file_size_bytes"),
        "mime_type": meta.get("mime_type"),
        "hashes": meta.get("hashes", {}),
        "latitude": meta.get("latitude"),
        "longitude": meta.get("longitude"),
        "altitude": meta.get("altitude"),
        "has_gps": meta.get("has_gps", False),
        "is_inferred_gps": meta.get("is_inferred_gps", False),
        "address": meta.get("address"),
        "date_added": meta.get("date_added"),
        "camera_info": meta.get("camera_info", "Não informada"),
        "software": spec.get("software"),
        "is_edited": spec.get("is_edited", False),
        "iso": spec.get("iso"),
        "aperture": spec.get("aperture"),
        "focal_length": spec.get("focal_length"),
        "exposure_time": spec.get("exposure_time"),
        "lens_model": spec.get("lens_model"),
        "dimensions": f"{spec.get('image_width')} x {spec.get('image_height')}" if spec.get('image_width') else None,
        "specific_metadata": spec,
        "scrubbing_analysis": meta.get("scrubbing_analysis"),
        "osint_pivots": meta.get("osint_pivots")
    }
    
    records.append(new_record)
    save_records(records)
    
    return new_record


@app.post("/api/boxes/manual")
@app.post("/api/records/manual")
async def create_record_manual(data: dict):
    records = load_records()
    record_id = str(uuid.uuid4())
    code = data.get("code") or generate_next_code(records)
    
    lat = float(data.get("latitude")) if data.get("latitude") is not None and data.get("latitude") != "" else None
    lng = float(data.get("longitude")) if data.get("longitude") is not None and data.get("longitude") != "" else None
    has_gps = lat is not None and lng is not None

    new_record = {
        "id": record_id,
        "code": code,
        "title": data.get("title", "Ponto GEOINT"),
        "notes": data.get("notes", ""),
        "photo_url": data.get("photo_url", ""),
        "filename": data.get("filename", "Registro Manual"),
        "latitude": lat,
        "longitude": lng,
        "altitude": float(data.get("altitude")) if data.get("altitude") is not None and data.get("altitude") != "" else None,
        "has_gps": has_gps,
        "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "camera_info": "Cadastro Manual"
    }
    
    records.append(new_record)
    save_records(records)
    return new_record

@app.put("/api/boxes/{record_id}")
@app.put("/api/records/{record_id}")
async def update_record(record_id: str, data: dict):
    records = load_records()
    found = False
    updated = None
    
    for i, r in enumerate(records):
        if r["id"] == record_id:
            records[i]["code"] = data.get("code", r.get("code", "GEO-001"))
            records[i]["title"] = data.get("title", r.get("title", "Ponto GEOINT"))
            records[i]["notes"] = data.get("notes", r.get("notes", ""))
            if "latitude" in data and data["latitude"] is not None:
                records[i]["latitude"] = float(data["latitude"])
                records[i]["has_gps"] = True
            if "longitude" in data and data["longitude"] is not None:
                records[i]["longitude"] = float(data["longitude"])
                records[i]["has_gps"] = True
            if "altitude" in data:
                records[i]["altitude"] = float(data["altitude"]) if data["altitude"] is not None else None
            
            updated = records[i]
            found = True
            break
            
    if not found:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")
        
    save_records(records)
    return updated

@app.delete("/api/boxes/{record_id}")
@app.delete("/api/records/{record_id}")
async def delete_record(record_id: str):
    records = load_records()
    new_records = []
    deleted_photo = None
    
    for r in records:
        if r["id"] == record_id:
            deleted_photo = r.get("photo_url")
        else:
            new_records.append(r)
            
    save_records(new_records)
    
    if deleted_photo and deleted_photo.startswith("/uploads/"):
        filename = os.path.basename(deleted_photo)
        filepath = os.path.join(UPLOADS_DIR, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
                
    return {"message": "Registro removido com sucesso."}

# --- CÁLCULO GEODÉSICO HAVERSINE OSINT ---
@app.get("/api/osint/distance")
async def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance_m = R * c
    distance_km = distance_m / 1000.0

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing_deg = (math.degrees(math.atan2(y, x)) + 360) % 360

    return {
        "distance_meters": round(distance_m, 2),
        "distance_km": round(distance_km, 3),
        "distance_nautical_miles": round(distance_km * 0.539957, 3),
        "bearing_degrees": round(bearing_deg, 2)
    }

# --- NOVAS FERRAMENTAS OSINT DE REDE & INFRAESTRUTURA ---

@app.get("/api/osint/ip-lookup")
async def ip_geolocation_lookup(target: str):
    """
    Geolocalização pública de IP / Domínio OSINT.
    Resolve hostname para IP e consulta geolocalização física do servidor.
    Plota automaticamente a localização no mapa 3D/2D.
    """
    clean_target = target.strip().replace("http://", "").replace("https://", "").split("/")[0]
    
    try:
        resolved_ip = socket.gethostbyname(clean_target)
    except Exception:
        resolved_ip = clean_target

    url = f"http://ip-api.com/json/{resolved_ip}?fields=status,message,country,city,lat,lon,isp,org,as,query"
    
    geo_data = {}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GEONIV-OSINT/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            geo_data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        geo_data = {"status": "fail", "message": f"Erro na consulta de IP: {str(e)}"}

    if geo_data.get("status") == "success":
        lat = geo_data.get("lat")
        lon = geo_data.get("lon")

        # Salvar o servidor como um ponto de inteligência mapeado
        records = load_records()
        record_id = str(uuid.uuid4())
        code = generate_next_code(records)
        
        new_record = {
            "id": record_id,
            "code": code,
            "title": f"Servidor {clean_target}",
            "filename": f"IP: {resolved_ip}",
            "latitude": lat,
            "longitude": lon,
            "altitude": 0.0,
            "has_gps": True,
            "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "camera_info": f"ISP: {geo_data.get('isp')} ({geo_data.get('as')})",
            "notes": f"Localizado em {geo_data.get('city')}, {geo_data.get('country')}. Org: {geo_data.get('org')}"
        }
        
        records.append(new_record)
        save_records(records)
        geo_data["record"] = new_record

    return geo_data

@app.get("/api/osint/dns-lookup")
async def dns_records_lookup(domain: str):
    """
    Resolução pública de registros DNS (A, Hostname) e porta.
    """
    clean_domain = domain.strip().replace("http://", "").replace("https://", "").split("/")[0]
    result = {
        "domain": clean_domain,
        "resolved_ips": [],
        "canonical_name": None,
        "error": None
    }
    
    try:
        host_info = socket.gethostbyname_ex(clean_domain)
        result["canonical_name"] = host_info[0]
        result["resolved_ips"] = host_info[2]
    except Exception as e:
        result["error"] = f"Erro na consulta DNS: {str(e)}"
        
    return result

@app.get("/api/osint/http-headers")
async def http_headers_inspector(target: str):
    """
    Inspeção defensiva de cabeçalhos HTTP e Stack Tecnológico do servidor.
    """
    if not target.startswith("http://") and not target.startswith("https://"):
        url = f"https://{target.strip()}"
    else:
        url = target.strip()
        
    result = {
        "target_url": url,
        "status_code": None,
        "headers": {},
        "security_score": "Forte",
        "missing_security_headers": [],
        "server_tech": "Desconhecido"
    }

    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GEONIV-OSINT/1.0'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            result["status_code"] = resp.status
            headers_dict = dict(resp.headers)
            result["headers"] = headers_dict

            # Análise de servidor
            result["server_tech"] = headers_dict.get("Server") or headers_dict.get("server") or "Oculto/CDN"

            # Checagem de cabeçalhos defensivos de segurança
            sec_headers = {
                "Strict-Transport-Security": "HSTS ausente",
                "Content-Security-Policy": "CSP ausente",
                "X-Frame-Options": "Proteção contra Clickjacking ausente",
                "X-Content-Type-Options": "Proteção MIME ausente"
            }

            for sh, msg in sec_headers.items():
                if not any(k.lower() == sh.lower() for k in headers_dict.keys()):
                    result["missing_security_headers"].append(msg)

            if len(result["missing_security_headers"]) > 2:
                result["security_score"] = "Básica"
            elif len(result["missing_security_headers"]) > 0:
                result["security_score"] = "Moderada"

    except Exception as e:
        result["error"] = f"Erro ao acessar cabeçalhos HTTP: {str(e)}"

    return result

# --- OSINT DE TELEFONIA: CONSULTA DE NÚMERO DE TELEFONE ---

@app.get("/api/osint/phone-lookup")
async def phone_number_lookup(phone: str, plot: bool = True):
    """
    Consulta OSINT de número de telefone.
    Identifica operadora, tipo de linha, localização do DDD,
    e gera links para investigação em plataformas externas.
    """
    clean_phone = phone.strip()
    if not clean_phone or len(clean_phone) < 7:
        raise HTTPException(status_code=400, detail="Número de telefone inválido ou muito curto.")

    result = phone_lookup(clean_phone)

    # Se plot=True e temos localização do DDD, salvar como ponto no mapa
    if plot and result.get("ddd_info"):
        ddd_info = result["ddd_info"]
        lat = ddd_info.get("lat")
        lng = ddd_info.get("lng")

        if lat is not None and lng is not None:
            records = load_records()
            record_id = str(uuid.uuid4())
            code = generate_next_code(records)

            formatted = result.get("formatted") or clean_phone
            carrier = result.get("carrier_hint", "Desconhecida")
            line_type = result.get("line_type", "Desconhecido")

            new_record = {
                "id": record_id,
                "code": code,
                "title": f"Tel: {formatted}",
                "filename": f"Telefone: {formatted}",
                "latitude": lat,
                "longitude": lng,
                "altitude": 0.0,
                "has_gps": True,
                "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "camera_info": f"Operadora: {carrier.split('—')[0].strip()}",
                "notes": f"DDD {result.get('ddd')} — {ddd_info.get('city')}/{ddd_info.get('uf')}. "
                         f"Tipo: {line_type}. Operadora (prefixo): {carrier}"
            }

            records.append(new_record)
            save_records(records)
            result["record"] = new_record

    return result

# --- EXPORTAÇÃO (KML E CSV) ---
@app.get("/api/export/kml")
async def export_kml():
    records = load_records()
    
    kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    document = ET.SubElement(kml, "Document")
    
    doc_name = ET.SubElement(document, "name")
    doc_name.text = "GEONIV_OSINT_Target_Map"

    for r in records:
        if r.get("latitude") is not None and r.get("longitude") is not None:
            placemark = ET.SubElement(document, "Placemark")
            
            name = ET.SubElement(placemark, "name")
            name.text = f"{r.get('code', 'GEO')} - {r.get('filename', 'Target')}"
            
            desc = ET.SubElement(placemark, "description")
            alt_info = f"Altitude: {r.get('altitude')}m\n" if r.get('altitude') else ""
            desc.text = f"Info: {r.get('camera_info')}\nData: {r.get('date_added')}\n{alt_info}Notas: {r.get('notes')}"
            
            point = ET.SubElement(placemark, "Point")
            coords = ET.SubElement(point, "coordinates")
            alt_val = r.get("altitude") or 0.0
            coords.text = f"{r.get('longitude')},{r.get('latitude')},{alt_val}"

    xml_str = ET.tostring(kml, encoding="utf-8", method="xml")
    return Response(
        content=xml_str,
        media_type="application/vnd.google-earth.kml+xml",
        headers={"Content-Disposition": "attachment; filename=alvos_osint_geoniv.kml"}
    )

@app.get("/api/export/csv")
async def export_csv():
    records = load_records()
    lines = ["ID,Codigo,Arquivo,Latitude,Longitude,Altitude_m,Data_Registro,Info,Software,Observacoes"]
    
    for r in records:
        notes = (r.get('notes') or '').replace(',', ';').replace('\n', ' ')
        line = f"{r.get('id')},{r.get('code')},{r.get('filename')},{r.get('latitude') or ''},{r.get('longitude') or ''},{r.get('altitude') or ''},{r.get('date_added')},{r.get('camera_info')},{r.get('software') or ''},{notes}"
        lines.append(line)
        
    csv_content = "\n".join(lines)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=relatorio_osint_geoniv.csv"}
    )
