# 🚀 Ares Travel - Deploy su Vercel

## 📋 Guida Deploy

### 1. Preparazione
```bash
# Clone del progetto
git clone <your-repo>
cd ares-travel

# Installa Vercel CLI
npm i -g vercel
```

### 2. Configurazione Variabili
Nel dashboard Vercel, aggiungi:
- `CESIUM_TOKEN` - Token Cesium Ion  
- `OPENAI_API_KEY` - Chiave OpenAI
- `OPENWEATHER_API_KEY` - Chiave OpenWeather

### 3. Deploy
```bash
vercel --prod
```

## 🔧 Struttura Vercel

- `public/` → Static files (frontend)
- `api/` → Vercel Functions (backend)
- `vercel.json` → Configurazione routing
- `requirements.txt` → Dipendenze Python

## ⚡ Differenze da Replit

- **WebSocket**: Non supportati - funzionalità chat disabilitata su Vercel
- **Database**: Storage temporaneo /tmp (non persistente), considera Vercel KV per produzione
- **Performance**: CDN globale, auto-scaling
- **Token Cesium**: Caricato dinamicamente da `/api/config`

## 📱 Frontend
Il frontend CesiumJS funziona identicamente. Il token viene iniettato automaticamente.

## 🔄 API Endpoints
- `GET /health` - Status sistema
- `GET /api/destinations` - Lista destinazioni  
- `POST /api/bookings` - Nuova prenotazione

## 🌐 Live URL
Dopo il deploy: `https://ares-travel.vercel.app`