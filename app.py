import os
import json
import uuid
import math
import socket
import base64
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import shutil
from PIL import Image
import io

from modules.exif_extractor import extract_metadata
from modules.metadata_extractor import analyze_any_file
from modules.phone_osint import phone_lookup


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuração de diretórios com suporte completo a Vercel Serverless (/tmp)
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
    try:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
    except Exception:
        pass

app = FastAPI(title="GEONIV 3D - Plataforma de Inteligência OSINT & GEOINT")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handler Global Amigável
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    return JSONResponse(
        status_code=500,
        content={
            "status": "Runtime Exception in FastAPI",
            "path": str(request.url),
            "error": str(exc),
            "type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
    )

# Configuração de Arquivos Estáticos e Templates
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

import mimetypes

@app.get("/static/{file_path:path}")
async def serve_static_file(file_path: str):
    candidate_dirs = [
        STATIC_DIR,
        os.path.join(BASE_DIR, "static"),
        os.path.join(os.getcwd(), "static"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"),
        "static"
    ]
    for cdir in candidate_dirs:
        full_path = os.path.join(cdir, file_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            mime, _ = mimetypes.guess_type(full_path)
            if not mime:
                if file_path.endswith('.css'):
                    mime = 'text/css'
                elif file_path.endswith('.js'):
                    mime = 'application/javascript'
                elif file_path.endswith('.png'):
                    mime = 'image/png'
                elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                    mime = 'image/jpeg'
                elif file_path.endswith('.svg'):
                    mime = 'image/svg+xml'
                else:
                    mime = 'application/octet-stream'
            with open(full_path, "rb") as f:
                return Response(
                    content=f.read(),
                    media_type=mime,
                    headers={"Cache-Control": "public, max-age=86400"}
                )
    raise HTTPException(status_code=404, detail=f"Arquivo estático não encontrado: {file_path}")

if os.path.exists(UPLOADS_DIR):
    try:
        app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
    except Exception:
        pass

# --- GERENCIAMENTO DE DADOS COM SUPORTE A READ-ONLY E SERVERLESS ---
_IN_MEMORY_RECORDS: List[Dict[str, Any]] = []

def load_records() -> list:
    global _IN_MEMORY_RECORDS
    target_files = [
        DATA_FILE,
        "/tmp/geoniv_data.json",
        os.path.join(BASE_DIR, "geoniv_data.json")
    ]
    for tf in target_files:
        if os.path.exists(tf):
            try:
                with open(tf, "r", encoding="utf-8") as f:
                    records = json.load(f)
                    if records:
                        _IN_MEMORY_RECORDS = records
                        return records
            except Exception:
                pass

    if _IN_MEMORY_RECORDS:
        return _IN_MEMORY_RECORDS

    return []

def save_records(records: list):
    global _IN_MEMORY_RECORDS
    _IN_MEMORY_RECORDS = records

    target_files = [DATA_FILE, "/tmp/geoniv_data.json"]
    for tf in target_files:
        try:
            with open(tf, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            break
        except (PermissionError, OSError):
            continue

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
    candidate_paths = [
        os.path.join(TEMPLATES_DIR, "index.html"),
        os.path.join(BASE_DIR, "templates", "index.html"),
        os.path.join(os.getcwd(), "templates", "index.html"),
        "templates/index.html"
    ]
    for p in candidate_paths:
        if os.path.exists(p) and os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(content="<h1>GEONIV 3D - Plataforma Online</h1>", status_code=200)

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "service": "GEONIV OSINT & GEOINT Platform",
        "version": "2.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

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
    
    file_bytes = await file.read()
    
    try:
        with open(final_path, "wb") as buffer:
            buffer.write(file_bytes)
    except Exception:
        # Se falhar escrita física, continuamos em memória
        pass

    file_url = f"/uploads/{final_filename}"
    base64_thumbnail = None

    # Se for imagem, gerar Base64 data URI para resiliência no Vercel
    if ext in ['.jpg', '.jpeg', '.png', '.heic', '.webp', '.tiff', '.bmp']:
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                rgb_img = img.convert("RGB")
                
                # Salvar JPG otimizado no disco se possível
                jpg_filename = f"img_{unique_id}.jpg"
                jpg_path = os.path.join(UPLOADS_DIR, jpg_filename)
                try:
                    rgb_img.save(jpg_path, "JPEG", quality=85)
                    file_url = f"/uploads/{jpg_filename}"
                except Exception:
                    pass

                # Criar thumbnail base64 (máx 400px de largura) para persistência serverless
                thumb_img = rgb_img.copy()
                thumb_img.thumbnail((400, 400))
                thumb_io = io.BytesIO()
                thumb_img.save(thumb_io, format="JPEG", quality=80)
                thumb_bytes = thumb_io.getvalue()
                base64_thumbnail = f"data:image/jpeg;base64,{base64.b64encode(thumb_bytes).decode('ascii')}"
        except Exception:
            pass

    # Análise Forense Multi-Arquivo
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
        "photo_thumbnail": base64_thumbnail,
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
    R = 6371000  # Raio da Terra em metros
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

# --- FERRAMENTAS OSINT DE REDE & INFRAESTRUTURA ---
@app.get("/api/osint/ip-lookup")
async def ip_geolocation_lookup(target: str):
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
    if not target.startswith("http://") and not target.startswith("https://"):
        url = f"https://{target.strip()}"
    else:
        url = target.strip()
        
    result: Dict[str, Any] = {
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

            result["server_tech"] = headers_dict.get("Server") or headers_dict.get("server") or "Oculto/CDN"

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
    clean_phone = phone.strip()
    if not clean_phone or len(clean_phone) < 7:
        raise HTTPException(status_code=400, detail="Número de telefone inválido ou muito curto.")

    result = phone_lookup(clean_phone)

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
