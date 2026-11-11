import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Configurar credenciales desde las Variables de Entorno de la nube
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "burg_token_secreto")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route("/", methods=["GET"])
def home():
    return "Bot de WhatsApp activo y funcionando correctamente para BURG!", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    # Verificación del Webhook de Meta
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Token de verificación inválido", 403
    return "Parámetros faltantes", 400

@app.route("/webhook", methods=["POST"])
def receive_message():
    body = request.get_json()
    try:
        if body.get("entry"):
            changes = body["entry"][0]["changes"][0]["value"]
            if "messages" in changes:
                message = changes["messages"][0]
                from_number = message["from"]
                
                # Validar si es un mensaje de texto
                if message.get("type") == "text":
                    msg_body = message["text"]["body"]
                    
                    # Generar respuesta con Gemini
                    response = model.generate_content(msg_body)
                    reply_text = response.text
                    
                    # Enviar respuesta por WhatsApp
                    send_whatsapp_message(from_number, reply_text)
                    
    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        
    return jsonify({"status": "success"}), 200

def send_whatsapp_message(to_number, message_text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text}
    }
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
