"""
Vercel Function per Ares Travel - Adattamento main.py
"""
import json
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Ares Travel API", version="5.2")

# CORS per Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carica dati da file JSON (Vercel read-only + temp storage)
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data.json")
TEMP_DATA_FILE = "/tmp/data.json"

def load_data():
    # Vercel: prova temp file, poi file statico iniziale
    if os.path.exists(TEMP_DATA_FILE):
        try:
            with open(TEMP_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # Fallback: file statico iniziale
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"destinations": [], "bookings": []}

def save_data(data):
    # Vercel: salva in /tmp (non persistente tra requests)
    try:
        with open(TEMP_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save data - {e}")

@app.get("/")
async def health_check():
    data = load_data()
    return JSONResponse({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "destinations": len(data.get("destinations", [])),
        "connections": 0,  # WebSocket gestito separatamente su Vercel
        "ws": False,
        "globe": "cesium",
        "globe_details": {
            "cesium_token": bool(os.getenv("CESIUM_TOKEN")),
            "destinations_loaded": len(data.get("destinations", []))
        },
        "openai": "vercel",
        "openai_details": {
            "mode": "vercel",
            "enabled": bool(os.getenv("OPENAI_API_KEY"))
        },
        "version": "5.2"
    })

@app.get("/destinations")
async def get_destinations():
    data = load_data()
    return {"destinations": data.get("destinations", [])}

@app.get("/config")
async def get_config():
    return JSONResponse({
        "cesiumToken": os.getenv("CESIUM_TOKEN", ""),
        "openaiEnabled": bool(os.getenv("OPENAI_API_KEY")),
        "version": "5.2"
    })

@app.post("/bookings")
async def create_booking(booking_data: dict):
    data = load_data()
    
    # Genera ID booking
    booking_id = f"BK{len(data.get('bookings', [])) + 1:04d}"
    
    new_booking = {
        "id": booking_id,
        "tripId": booking_data.get("tripId"),
        "customerName": booking_data.get("customerName"),
        "customerEmail": booking_data.get("customerEmail"),
        "guests": booking_data.get("guests", 1),
        "notes": booking_data.get("notes", ""),
        "bookingDate": datetime.now().isoformat(),
        "status": "confirmed"
    }
    
    if "bookings" not in data:
        data["bookings"] = []
    data["bookings"].append(new_booking)
    
    save_data(data)
    
    return JSONResponse({
        "success": True,
        "booking": new_booking,
        "message": f"Prenotazione {booking_id} creata con successo!"
    })

# Vercel handler per FastAPI
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    # Fallback per sviluppo locale
    handler = app