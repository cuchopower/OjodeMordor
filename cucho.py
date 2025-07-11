import json
import requests
import yfinance as yf
from datetime import datetime, UTC
from pytz import timezone

# Zona horaria local (ajustala si no usás Lima)
TZ_LOCAL = "America/Lima"

# ID del archivo JSON en Google Drive
DRIVE_FILE_ID = "1-N5YQIburpJFO3uT_mqZj3_SVze3uWG9"
DRIVE_URL     = f"https://drive.google.com/uc?export=download&id={DRIVE_FILE_ID}"

# Cargar activos desde Drive
def cargar_activos_remotos():
    try:
        r = requests.get(DRIVE_URL)
        activos = json.loads(r.text)
        return activos
    except Exception as e:
        print(f"❌ Error descargando activos: {e}")
        return []

# Función para evaluar alertas
def evaluar_alertas(activos):
    print(f"📡 Evaluando [CUCHO]: {datetime.now(timezone(TZ_LOCAL)).strftime('%Y-%m-%d %H:%M:%S')}")

    for activo in activos:
        try:
            symbol = activo.get("symbol")
            data = yf.Ticker(symbol).history(period="1d", interval="1m")
            if data.empty:
                print(f"⚠️ No hay datos para {symbol}")
                continue
            precio_actual = data["Close"].iloc[-1]

            señales = []

            # 🎯 Alerta por target_price
            target = activo.get("target_price")
            if target and precio_actual <= target:
                señales.append(f"🎯 {symbol} llegó a ${precio_actual:.2f} (target: ${target})")

            # 📉 Alerta por caída porcentual
            ref = activo.get("reference_price")
            drop_pct = activo.get("drop_threshold_pct")
            if ref and drop_pct:
                caida = ((ref - precio_actual) / ref) * 100
                if caida >= drop_pct:
                    señales.append(f"📉 {symbol} cayó {caida:.2f}% desde ${ref} (ahora ${precio_actual:.2f})")

            # Imprimir señales
            for s in señales:
                print(s)
                # Podés agregar aquí envío a Telegram si está configurado

        except Exception as e:
            print(f"❌ Error evaluando {symbol}: {e}")

# ▶️ Ejecución principal
activos = cargar_activos_remotos()
print(f"✅ {len(activos)} activos cargados desde Drive")

evaluar_alertas(activos)

hora_local = datetime.now(timezone(TZ_LOCAL)).strftime('%H:%M')
print(f"🕒 Evaluación terminada a las {hora_local} ({TZ_LOCAL})")
