#!/usr/bin/env python3
"""
ARES TRAVEL - Sistema Stabile v1 con OpenAI
Globe.gl v2.27.5 + Three.js v0.150.1 + Chat AI
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import asyncio
import time
from datetime import datetime
from typing import List
from contextlib import asynccontextmanager
import openai

# === MODELLI ===
class ChatMessage(BaseModel):
    text: str

# === DATI VIAGGI ===
DESTINATIONS = [
    {
        "id": 1,
        "name": "Tokyo, Giappone", 
        "lat": 35.6762,
        "lng": 139.6503,
        "color": "#ff6b6b",
        "price": 2500,
        "description": "Metropoli futuristica e cultura millenaria"
    },
    {
        "id": 2,
        "name": "Santorini, Grecia",
        "lat": 36.3932, 
        "lng": 25.4615,
        "color": "#4ecdc4",
        "price": 1800,
        "description": "Tramonti mozzafiato sul Mar Egeo"
    },
    {
        "id": 3,
        "name": "Machu Picchu, Perù",
        "lat": -13.1631,
        "lng": -72.5450, 
        "color": "#45b7d1",
        "price": 2200,
        "description": "Cittadella inca nelle Ande"
    },
    {
        "id": 4,
        "name": "Maldive",
        "lat": 3.2028,
        "lng": 73.2207,
        "color": "#f9ca24", 
        "price": 3500,
        "description": "Atolli paradisiaci nell'Oceano Indiano"
    },
    {
        "id": 5,
        "name": "Reykjavík, Islanda",
        "lat": 64.1466,
        "lng": -21.9426,
        "color": "#6c5ce7",
        "price": 2800,
        "description": "Aurora boreale e paesaggi vulcanici"
    }
]

# === WEBSOCKET MANAGER ===
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🔗 WebSocket connesso. Totale: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"❌ WebSocket disconnesso. Totale: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Errore invio messaggio: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                dead_connections.append(connection)
        
        for dead in dead_connections:
            self.disconnect(dead)

manager = WebSocketManager()

# === OPENAI SETUP CON MOCK ===
openai.api_key = os.getenv("OPENAI_API_KEY")
USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() == "true"

async def get_ai_response(user_message: str) -> dict:
    """Genera risposta intelligente con OpenAI"""
    
    # Context per Ares Travel
    system_prompt = """Sei l'assistente AI di Ares Travel, un'agenzia di viaggi premium che ama creare esperienze indimenticabili! 
    
    Le nostre destinazioni disponibili sono:
    - Tokyo, Giappone (€2500) - Metropoli futuristica e cultura millenaria
    - Santorini, Grecia (€1800) - Tramonti mozzafiato sul Mar Egeo  
    - Machu Picchu, Perù (€2200) - Cittadella inca nelle Ande
    - Maldive (€3500) - Atolli paradisiaci nell'Oceano Indiano
    - Reykjavík, Islanda (€2800) - Aurora boreale e paesaggi vulcanici
    
    Il tuo stile è caloroso, entusiasta e sempre propositivo. Rispondi con varietà e creatività.
    Saluto iniziale: "Benvenuto! Posso consigliarti 2 mete basate sul periodo e budget. Preferisci mare o città?"
    Ogni risposta deve includere una chiamata all'azione: focus sul globe, apertura pacchetti, o richiesta dettagli.
    Usa emojis per rendere più vivace la conversazione e mantieni il tono entusiasta ma professionale.
    
    Mantieni le risposte coinvolgenti (2-3 frasi) e sempre con una proposta d'azione."""
    
    if not USE_OPENAI:
        # MOCK RESPONSE
        print(f"[MOCK] User: {user_message}")
        mock_responses = {
            "tokyo": "🗾 Tokyo è una metropoli incredibile che fonde tradizione e modernità. I nostri pacchetti includono visite ai templi storici e ai quartieri futuristici di Shibuya.",
            "santorini": "🏛️ Santorini offre tramonti mozzafiato e architettura unica. Le nostre escursioni includono degustazioni di vino locale e tour delle tipiche case bianche.",
            "maldive": "🏝️ Le Maldive sono il paradiso tropicale perfetto per una fuga romantica. I nostri resort offrono bungalow sull'acqua e attività subacquee esclusive.",
            "machu": "🏔️ Machu Picchu è un'esperienza spirituale unica nelle Ande. I nostri tour includono trekking guidati e visite ai siti archeologici più importanti.",
            "islanda": "❄️ L'Islanda offre paesaggi vulcanici e aurore boreali spettacolari. Le nostre escursioni includono bagni termali e tour dei geyser più famosi.",
            "prezzo": "💰 I nostri prezzi vanno da €1800 (Santorini) a €3500 (Maldive). Tutti i pacchetti includono volo, hotel 4 stelle e escursioni guidate.",
            "viaggio": "✈️ Offriamo 5 destinazioni esclusive con pacchetti completi. Ogni viaggio include servizi premium e guide esperte locali per un'esperienza indimenticabile."
        }
        
        for key, response in mock_responses.items():
            if key in user_message.lower():
                return {"text": response, "mock": True}
        
        return {"text": f"🌍 Grazie per la tua domanda su '{user_message}'. I nostri consulenti sono specializzati in viaggi premium verso destinazioni esclusive. Come posso aiutarti a pianificare la tua prossima avventura?", "mock": True}
    
    try:
        client = openai.AsyncOpenAI(api_key=openai.api_key)
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300,
            temperature=0.6,
            presence_penalty=0.3,
            frequency_penalty=0.1
        )
        
        return {"text": response.choices[0].message.content.strip(), "mock": False}
        
    except Exception as e:
        print(f"OpenAI API error: {e}")
        if "429" in str(e) or "insufficient_quota" in str(e):
            return {
                "error": True,
                "code": 429,
                "ui": "Credito API esaurito. Modalità demo attiva."
            }
        raise e

# === LIFESPAN SETUP ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Ares Travel v5.0 - Sistema Completo")
    print(f"📍 {len(DESTINATIONS)} destinazioni caricate")
    print("✅ Server pronto!")
    yield
    # Shutdown - operations when shutting down
    print("🛑 Sistema fermato")

# === APP SETUP ===
app = FastAPI(
    title="Ares Travel API",
    description="Sistema completo ricostruito",
    version="5.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ROUTES ===
@app.get("/")
async def homepage():
    """Homepage con token Cesium injection"""
    try:
        with open("public/index.html", "r", encoding="utf-8") as f:
            html = f.read()
        
        # Inject Cesium token
        cesium_token = os.getenv("CESIUM_TOKEN", "")
        if cesium_token:
            html = html.replace("YOUR_CESIUM_TOKEN_HERE", cesium_token)
            print(f"✅ Token Cesium injected: {cesium_token[:15]}...")
        
        return HTMLResponse(html)
        
    except FileNotFoundError:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Ares Travel</title></head>
        <body>
            <h1>🚀 Ares Travel</h1>
            <p>Sistema in costruzione...</p>
        </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check dettagliato per monitoraggio"""
    # Test WS
    ws_connections = len(manager.active_connections)
    ws_status = ws_connections > 0
    
    # Test OpenAI dettagliato
    openai_status = "mock"
    openai_details = {"mode": "mock", "enabled": USE_OPENAI}
    
    if USE_OPENAI:
        if not openai.api_key:
            openai_status = "no_key"
            openai_details["error"] = "API key mancante"
        else:
            try:
                test_response = await get_ai_response("test")
                if test_response.get("error"):
                    openai_status = "quota"
                    openai_details["error"] = "Quota esaurita"
                else:
                    openai_status = "live"
                    openai_details["last_test"] = "ok"
            except Exception as e:
                openai_status = "error"
                openai_details["error"] = str(e)[:100]
    
    # Globe status evoluto
    globe_status = "cesium" if os.getenv("CESIUM_TOKEN") else "fallback"
    globe_details = {
        "cesium_token": bool(os.getenv("CESIUM_TOKEN")),
        "destinations_loaded": len(DESTINATIONS)
    }
    
    # Logging dettagliato
    print(f"[CHECK] WS {'ok' if ws_status else 'no connections'} ({ws_connections})")
    if USE_OPENAI:
        print(f"[CHECK] OpenAI {openai_status}")
    print(f"[CHECK] Globe {globe_status}")
    
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "destinations": len(DESTINATIONS),
        "connections": ws_connections,
        "ws": ws_status,
        "globe": globe_status,
        "globe_details": globe_details,
        "openai": openai_status,
        "openai_details": openai_details,
        "version": "5.1"
    }

@app.get("/destinations")
async def get_destinations():
    """Destinazioni per globe"""
    return {
        "destinations": DESTINATIONS,
        "count": len(DESTINATIONS),
        "server_time": datetime.now().strftime("%H:%M:%S")
    }

@app.get("/api/test-openai")
async def test_openai():
    """Test diagnostico OpenAI con timing"""
    if not USE_OPENAI:
        return {"ok": False, "error": "OpenAI disabilitato", "mode": "mock"}
    
    if not openai.api_key:
        return {"ok": False, "error": "API key mancante", "mode": "mock"}
    
    try:
        start_time = time.time()
        client = openai.AsyncOpenAI(api_key=openai.api_key)
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test rapido, rispondi solo 'OK'"}],
            max_tokens=10,
            temperature=0
        )
        elapsed = int((time.time() - start_time) * 1000)
        
        if elapsed > 1500:
            print(f"[OpenAI] ⚠️ Test lento: {elapsed}ms")
            return {"ok": False, "error": f"Troppo lento ({elapsed}ms)", "response_time": elapsed}
        
        print(f"[OpenAI] ✅ Test OK in {elapsed}ms")
        return {"ok": True, "response_time": elapsed, "model": "gpt-3.5-turbo"}
        
    except Exception as e:
        error_msg = str(e)
        print(f"[OpenAI] ❌ Test fallito: {error_msg}")
        
        if "quota" in error_msg.lower() or "rate_limit" in error_msg.lower():
            return {"ok": False, "error": "Quota esaurita", "details": error_msg}
        elif "invalid" in error_msg.lower():
            return {"ok": False, "error": "API key invalida", "details": error_msg}
        else:
            return {"ok": False, "error": "Errore generico", "details": error_msg}

@app.post("/api/chat")
async def chat_endpoint(message: ChatMessage):
    """Endpoint chat HTTP fallback"""
    user_text = message.text.strip()
    
    if not user_text:
        return {"response": "Messaggio vuoto ricevuto"}
    
    # Chat AI con OpenAI o Mock
    try:
        ai_response = await get_ai_response(user_text)
        if ai_response.get("error"):
            return ai_response
        return {"response": ai_response["text"]}
    except Exception as e:
        print(f"❌ AI error: {e}")
        # Fallback a risposte predefinite
        if "prezzo" in user_text.lower() or "costo" in user_text.lower() or "economico" in user_text.lower():
            response = "💰 I nostri viaggi vanno da €1800 (Santorini) a €3500 (Maldive). Quale ti interessa?"
        elif "tokyo" in user_text.lower():
            response = "🗾 Tokyo è una destinazione fantastica! Vuoi vedere i dettagli del viaggio?"
        elif "santorini" in user_text.lower():
            response = "🏛️ Santorini offre tramonti indimenticabili! Ti interessa prenotare?"
        elif "maldive" in user_text.lower():
            response = "🏝️ Le Maldive sono il paradiso tropicale! Posso mostrarti i nostri pacchetti."
        elif "machu" in user_text.lower() or "peru" in user_text.lower():
            response = "🏔️ Machu Picchu è un'esperienza mistica! Ti piacerebbe esplorare le Ande?"
        elif "islanda" in user_text.lower() or "iceland" in user_text.lower():
            response = "❄️ L'Islanda offre aurore boreali spettacolari! Quando vorresti partire?"
        elif "viaggio" in user_text.lower() or "viaggi" in user_text.lower():
            response = "✈️ Perfetto! Abbiamo 5 destinazioni incredibili. Quale preferisci?"
        else:
            response = f"🌍 Ho ricevuto: '{user_text}'. Come posso aiutarti con i tuoi viaggi?"
        
        return {"response": response}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket stabile con keep-alive mobile-friendly"""
    await manager.connect(websocket)
    
    # Messaggio di benvenuto
    await manager.send_personal_message({
        "type": "system",
        "message": "🌍 Benvenuto in Ares Travel! Come posso aiutarti?"
    }, websocket)
    
    last_activity = time.time()
    
    try:
        while True:
            try:
                # Timeout 60s per rilevare connessioni morte
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                msg_data = json.loads(data)
                last_activity = time.time()
                
                # Handle ping/pong keep-alive
                if msg_data.get("type") == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "t": msg_data.get("t", int(time.time() * 1000))
                    }, websocket)
                    continue
                
                # Handle chat messages
                user_text = msg_data.get("text", "").strip()
                message_type = msg_data.get("type", "legacy")
                
                if user_text:
                    print(f"💬 Ricevuto: {user_text}")
                    
                    # Processa con AI
                    try:
                        ai_response = await get_ai_response(user_text)
                        
                        if ai_response.get("error"):
                            # Gestione quota 429
                            await manager.send_personal_message(ai_response, websocket)
                            continue
                        
                        response = ai_response["text"]
                        
                    except Exception as e:
                        print(f"❌ AI fallback: {e}")
                        # Fallback logica
                        if "tokyo" in user_text.lower():
                            response = "🗾 Tokyo è una destinazione fantastica! Vuoi vedere i dettagli del viaggio?"
                        elif "santorini" in user_text.lower():
                            response = "🏛️ Santorini offre tramonti indimenticabili! Ti interessa prenotare?"
                        elif "maldive" in user_text.lower():
                            response = "🏝️ Le Maldive sono il paradiso tropicale! Posso mostrarti i nostri pacchetti."
                        elif "machu" in user_text.lower() or "peru" in user_text.lower():
                            response = "🏔️ Machu Picchu è un'esperienza mistica! Ti piacerebbe esplorare le Ande?"
                        elif "islanda" in user_text.lower():
                            response = "❄️ L'Islanda offre aurore boreali spettacolari! Quando vorresti partire?"
                        elif "prezzo" in user_text.lower() or "costo" in user_text.lower() or "economico" in user_text.lower():
                            response = "💰 Santorini €1800 | Tokyo €2500 | Machu Picchu €2200 | Islanda €2800 | Maldive €3500. Quale ti interessa?"
                        elif "viaggio" in user_text.lower():
                            response = "✈️ Perfetto! Abbiamo 5 destinazioni incredibili. Clicca sui pin colorati sul globo per esplorare!"
                        elif "test" in user_text.lower():
                            response = "🔧 Sistema funzionante! Pronto per pianificare il tuo viaggio da sogno?"
                        else:
                            response = f"🌍 Ho ricevuto: '{user_text}'. Come posso aiutarti con i tuoi viaggi?"
                    
                    # PROTOCOLLO SEMPLICE - Invia risposta
                    if message_type == "user":
                        # Formato nuovo
                        await manager.send_personal_message({
                            "type": "assistant",
                            "text": response
                        }, websocket)
                    else:
                        # Formato legacy
                        await manager.send_personal_message({
                            "message": response
                        }, websocket)
                
                # Handle destination clicks
                elif msg_data.get("type") == "dest-click":
                    dest_name = msg_data.get("dest", "destinazione")
                    await manager.send_personal_message({
                        "type": "assistant",
                        "text": f"Interessante scelta! {dest_name} è una destinazione fantastica. Vuoi che ti racconti di più sui viaggi disponibili?"
                    }, websocket)
            
            except asyncio.TimeoutError:
                # Keep-alive: invia ping se nessun messaggio per 60s
                current_time = time.time()
                if current_time - last_activity > 60:
                    try:
                        await manager.send_personal_message({
                            "type": "ping",
                            "server_time": int(current_time * 1000)
                        }, websocket)
                        print(f"[WS] Keep-alive ping inviato")
                    except Exception as e:
                        print(f"[WS] Errore ping keep-alive: {e}")
                        break
                        
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error", 
                    "message": "Formato messaggio non valido"
                }, websocket)
                
    except WebSocketDisconnect as e:
        print(f"❌ WebSocket disconnesso. Code: {e.code}, Reason: {getattr(e, 'reason', 'N/A')}")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket errore: {e}")
        manager.disconnect(websocket)

# Modernized lifespan events implemented above

if __name__ == "__main__":
    import uvicorn
    # Usa porta 5000 per compatibilità Replit webview
    port = 5000
    print(f"🔗 URL pubblico: https://{os.getenv('REPL_SLUG')}.{os.getenv('REPL_OWNER')}.repl.co")
    print(f"📡 Server interno: http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, proxy_headers=True, forwarded_allow_ips="*")