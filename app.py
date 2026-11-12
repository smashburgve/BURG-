import os
import requests
from flask import Flask, jsonify, request
import google.generativeai as genai

app = Flask(__name__)

# Configurar credenciales desde las Variables de Entorno
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


@app.route("/", methods=["GET"])
def home():
  return "¡El bot de BURG está activo!", 200


# Ruta GET para la verificación inicial del Webhook
@app.route("/webhook", methods=["GET"])
def webhook_verify():
  mode = request.args.get("hub.mode")
  token = request.args.get("hub.verify_token")
  challenge = request.args.get("hub.challenge")

  if mode and token:
    if mode == "subscribe" and token == VERIFY_TOKEN:
      print("WEBHOOK_VERIFIED")
      return challenge, 200
    else:
      return "Verification token mismatch", 403
  return "Hello World", 200


# Ruta POST para recibir los mensajes entrantes y responder con Gemini
@app.route("/webhook", methods=["POST"])
def webhook_post():
  body = request.get_json()
  print("¡Mensaje recibido de Meta!", body)

  try:
    # Verificamos si el payload contiene un mensaje de texto de WhatsApp
    entry = body.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value = changes.get("value", {})
    messages = value.get("messages")

    if messages:
      message = messages[0]
      from_number = message.get("from")  # Número del cliente
      msg_body = message.get("text", {}).get("body")  # Texto enviado

      if msg_body and from_number:
        print(f"Mensaje de {from_number}: {msg_body}")

        # Generamos la respuesta utilizando Gemini
        ai_response = model.generate_content(msg_body)
        reply_text = ai_response.text

        # Preparamos la petición para enviar la respuesta por la API de WhatsApp
        url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": from_number,
            "text": {"body": reply_text},
        }

        # Enviamos el mensaje de vuelta
        response = requests.post(url, json=payload, headers=headers)
        print("Respuesta enviada a WhatsApp:", response.status_code)

  except Exception as e:
    print("Error procesando el mensaje:", e)

  return "OK", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
