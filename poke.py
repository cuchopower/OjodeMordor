#!/usr/bin/env python3
import json
import time
import requests
from datetime import datetime, time as dtime
from pytz import timezone
import yfinance as yf

# ————————— CONFIGURACIÓN —————————

# ID del archivo JSON en Google Drive (activos para “poke”)
DRIVE_FILE_ID = "ID_DEL_ARCHIVO_POKE"
DRIVE_URL     = f"https://drive.google.com/uc?export=download&id={DRIVE_FILE_ID}"

# Telegram
TELEGRAM_TOKEN = '7666801859:AAFPwyWI_gPtqJO9CxJzUHyi1hu9eEQAj-c'
TELEGRAM_CHAT_ID = '7361418502'

# Zona horaria local
TZ_LOCAL = "America/Lima"

# Intervalo de ciclo (segundos)
SLEEP_SECONDS = 300  # 5 minutos

# ————————— FUNCIONES —————————

def cargar_activos_remotos():
    """Descarga y parsea el JSON de Google Drive."""
    try:
        r = requests.get(DRIVE_URL, timeout=10)
        r.raise_for_status()
        return json.loads(r.text)
    except Exception as e:
        print("Error descargando activos:", e)
        return []

def enviar_telegram(mensaje):
    """Envía un mensaje por Telegram."""
    url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje}
    try:
        r = requests.post(url, data=payload, timeout=10)
        if not r.ok:
            print("⚠️ Error Telegram:", r.text)
    except Exception as e:
        print("⚠️ Excepción Telegram:", e)

def get_current_price(ticker):
    """Obtiene el precio de cierre más reciente."""
    try:
        df = yf.Ticker(ticker).history(period="1d")
        return round(df["Close"].iloc[-1], 2)
    except Exception:
        return None

def estado_mercado():
    """Determina si el mercado está open/closed/pre-/post-market (UTC)."""
    ahora_utc = datetime.utcnow().time()
    if dtime(13, 30) <= ahora_utc <= dtime(20, 0):
        return "mercado regular"
    if dtime(9, 0) <= ahora_utc < dtime(13, 30):
        return "pre-market"
    if dtime(20, 0) <= ahora_utc < dtime(23, 59):
        return "post-market"
    return "cerrado"

def evaluar_alertas(activos):
    """Revisa cada activo y envía alertas si se cumplen las condiciones."""
    tz         = timezone(TZ_LOCAL)
    hora_local = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n📡 Evaluando [POKE]: {hora_local} ({estado_mercado()})")

    ultimos_alertados = {}
    for a in activos:
        sym = a.get("symbol")
        cur = get_current_price(sym)
        if cur is None:
            continue

        mensajes = []

        # 🎯 Target Price
        if a.get("target_price") and cur <= a["target_price"]:
            prev = ultimos_alertados.get(sym)
            if prev is None or cur < prev:
                ultimos_alertados[sym] = cur
                mensajes.append(
                    f"🎯 {sym} llegó a ${cur} (target: ${a['target_price']})"
                )

        # 📉 Caída desde referencia
        if a.get("drop_threshold_pct"):
            ref  = a.get("reference_price", cur)
            drop = (ref - cur) / ref * 100
            if drop >= a["drop_threshold_pct"]:
                mensajes.append(
                    f"📉 {sym} cayó {drop:.2f}% desde ${ref:.2f} (ahora ${cur})"
                )

        # Envío de alertas
        for m in mensajes:
            hora_simple = datetime.now(tz).strftime('%H:%M')
            alerta      = f"[POKE] {m} – {hora_simple} {TZ_LOCAL}"
            print(alerta)
            enviar_telegram(alerta)

# ————————— MAIN LOOP —————————

if __name__ == "__main__":
    print("⏳ Iniciando bot POKE…")
    while True:
        activos = cargar_activos_remotos()
        if estado_mercado() == "mercado regular":
            evaluar_alertas(activos)
        else:
            tz = timezone(TZ_LOCAL)
            print(f"🔕 Mercado {estado_mercado()}. ({datetime.now(tz).strftime('%H:%M')})")
        time.sleep(SLEEP_SECONDS)