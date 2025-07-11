import json
import requests
import yfinance as yf
from datetime import datetime
from pytz import timezone

# 🕒 Zona horaria local
TZ_LOCAL = "America/Lima"

# 🔗 Archivo de activos en Google Drive (POKE)
DRIVE_FILE_ID = "1U_wdqz5cLPTz03ycAsJDL_s9O7TvQoOd"
DRIVE_URL = f"https://drive.google.com/uc?export=download&id={DRIVE_FILE_ID}"

# 📬 Configuración de Telegram
TELEGRAM_TOKEN = '7666801859:AAFPwyWI_gPtqJO9CxJzUHyi1hu9eEQAj-c'
TELEGRAM_CHAT_ID = '7361418502'

# 📬 Función para enviar alertas a Telegram
def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")

# 📂 Cargar activos desde Google Drive
def cargar_activos_remotos():
    try:
        r = requests.get(DRIVE_URL)
        activos = json.loads(r.text)
        return activos
    except Exception as e:
        print(f"❌ Error al cargar activos: {e}")
        return []

# 🔍 Evaluar condiciones de alerta
def evaluar_alertas(activos):
    ahora = datetime.now(timezone(TZ_LOCAL))
    print(f"📡 Evaluando [POKE]: {ahora.strftime('%Y-%m-%d %H:%M:%S')}")

    for activo in activos:
        try:
            symbol = activo.get("symbol")
            data = yf.Ticker(symbol).history(period="1d", interval="1m")
            if data.empty:
                print(f"⚠️ Sin datos para {symbol}")
                continue

            precio_actual = data["Close"].iloc[-1]
            señales = []

            # 🎯 Señal por target_price
            target = activo.get("target_price")
            if target and precio_actual <= target:
                señales.append(f"🎯 {symbol} llegó a ${precio_actual:.2f} (target: ${target})")

            # 📉 Señal por caída porcentual
            ref = activo.get("reference_price")
            drop_pct = activo.get("drop_threshold_pct")
            if ref and drop_pct:
                caida = ((ref - precio_actual) / ref) * 100
                if caida >= drop_pct:
                    señales.append(f"📉 {symbol} cayó {caida:.2f}% desde ${ref} (ahora ${precio_actual:.2f})")

            for señal in señales:
                print(señal)
                mensaje = f"[POKE] {señal} – {ahora.strftime('%H:%M %Z')}"
                enviar_telegram(mensaje)

        except Exception as e:
            print(f"❌ Error evaluando {symbol}: {e}")

# ▶️ Ejecución principal
if __name__ == "__main__":
    activos = cargar_activos_remotos()
    print(f"✅ Se cargaron {len(activos)} activos desde Drive")
    evaluar_alertas(activos)
    fin = datetime.now(timezone(TZ_LOCAL)).strftime('%H:%M')
    print(f"🕒 Evaluación completada a las {fin} ({TZ_LOCAL})")
