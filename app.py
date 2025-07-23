from flask import Flask, request
import requests
import os

app = Flask(__name__)

# API Key de OpenWeather (usa variable de entorno en Render)
OPENWEATHER_API_KEY = os.environ.get("08d022fcd1eb33514eae9451cf3cc2ac")

# Diccionario simple para convertir días a índice (0=hoy)
DIAS = {
    "lunes": 0,
    "martes": 1,
    "miércoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sábado": 5,
    "domingo": 6
}

@app.route("/webhook", methods=["POST"])
def webhook():
    # Leer el mensaje entrante desde Twilio
    incoming_msg = request.values.get("Body", "").strip().lower()
    from_number = request.values.get("From", "")
    
    partes = incoming_msg.split()
    if len(partes) < 2:
        return respond("Por favor enviá: ciudad + día. Ej: 'Rosario martes'")

    ciudad = partes[0].capitalize()
    dia = partes[1]

    # Llamar a OpenWeather
    try:
        lat, lon = get_lat_lon(ciudad)
        forecast = get_forecast(lat, lon)
        dia_idx = DIAS.get(dia, 0)
        weather = forecast[dia_idx]

        descripcion = weather["weather"][0]["description"].capitalize()
        temp = weather["main"]["temp"]
        viento = weather["wind"]["speed"]

        mensaje = f"📍 *{ciudad}* el *{dia}*:\n🌡️ Temp: {temp}°C\n💨 Viento: {viento} m/s\n🌥️ Estado: {descripcion}"
    except Exception as e:
        mensaje = f"No pude obtener el clima para {ciudad}. Verificá el nombre y el día."

    return respond(mensaje)

def respond(message):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{message}</Message>
</Response>"""

def get_lat_lon(ciudad):
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={ciudad}&limit=1&appid={OPENWEATHER_API_KEY}"
    r = requests.get(url)
    data = r.json()
    if not data:
        raise Exception("Ciudad no encontrada")
    return data[0]["lat"], data[0]["lon"]

def get_forecast(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&lang=es&appid={OPENWEATHER_API_KEY}"
    r = requests.get(url)
    data = r.json()
    dias = []
    # Tomar 1 muestra por día (cada 24h, cada 8 datos)
    for i in range(0, len(data["list"]), 8):
        dias.append(data["list"][i])
    return dias

if __name__ == "__main__":
    app.run(debug=True)
