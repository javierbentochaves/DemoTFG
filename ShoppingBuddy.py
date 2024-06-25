from flask import Flask, render_template, request, session
import requests
import http.client
import json
import re
from urllib.parse import quote_plus
import random
import string

def random_alphanumeric(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def respuesta_openai(texto, conversacion_previa):
    conn = http.client.HTTPSConnection("tevia01s-swcedc-ctocuopegpt.openai.azure.com")
    headers = {'Content-Type': "application/json",'api-key': "4fd5aea11c5448f08ccb9d3224606740"}

    payload = {
    "messages": [],
    "max_tokens": 400,
    "temperature": 0.7,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "top_p": 0.95,
    "stop": None}
    
    random_tag=random_alphanumeric(8)
    message={}
    message['role']='system'
    if texto=="[TEMA NO APLICA]":
        message['content'] = f"En un chat de una tienda online el usuario ha enviado un texto que no tiene nada que ver. Respóndele educadamente para que hable solo de temas como info de productos de la tienda, seguimiento de pedidos o devoluciones. Ten en cuenta que por defecto le habíamos contestado esto: {conversacion_previa}. No concemos el nombre del usuario."
    else:
        message['content'] = f'''A continuación te voy a mostrar un texto entre las marcas [{random_tag}] y [{random_tag}]. 
        En el texto debes identificar si se trata de las siguientes opciones: 1: saludo o inicio de conversacion. 2: Información sobre un producto de la tienda. 3: Seguimiento de un pedido. 4: Continuación de la conversacion. 5: Cualquier tema distinto de una tienda de ropa. 
        Este texto es parte de una conversación. La conversación previa que sirve de conexto es esta: [Inicio conversacion previa]{conversacion_previa}[fin conversacion previa]. 
        El texto es: [{random_tag}]{texto}[{random_tag}]. 
        Debes responder un texto en formato json con lo siguiente:{{ "intent": "[valor 1, 2, 3 o 4]", "info_producto": "[nombre o descripción del producto]", "pedido": "[numero de pedido]", "mensaje": "[Resumen del mensaje del usuario]", "respuesta_sistema": "[La respuesta que le darías normalmente al usuario teniendo en cuenta la conversación previa y el texto que acaba de escribir]"}}'''
    payload['messages'].append(message)

    json_payload = json.dumps(payload)
    #print(json.dumps(payload, indent=1))
    
    modelo="gpt-35-turbo"
    #modelo="gpt-4-turbo"
    conn.request("POST", f"/openai/deployments/{modelo}/chat/completions?api-version=2023-07-01-preview", json_payload, headers)

    res = conn.getresponse()
    data = res.read()
    data_decoded = data.decode('utf-8')
    
    json_data=json.loads(data_decoded)
    respuesta=""
    if "choices" in json_data and isinstance(json_data["choices"], list) and len(json_data["choices"])>0:
        primer_choice=json_data["choices"][0]
        if "message" in primer_choice and "content" in primer_choice["message"]:
            respuesta=primer_choice["message"]["content"]
            respuesta=respuesta.replace("json", "").replace("```","")
    completion_tokens=json_data["usage"]["completion_tokens"]
    prompt_tokens=json_data["usage"]["completion_tokens"]
    print(f"Prompt tokens: {prompt_tokens}")
    print(f"Response tokens: {completion_tokens}")
    print(f"respuesta: {respuesta}")
    return respuesta


app = Flask(__name__)
app.secret_key='feafabadafeacebada'

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    user_input = request.form['user_input']
    if 'conversacion_previa' not in session:
        session['conversacion_previa'] = ''
    if request.method == 'POST':
        texto = request.form['user_input']
        respuesta = respuesta_openai(texto, session['conversacion_previa'])
        respuesta_json = json.loads(respuesta)
        intent = respuesta_json["intent"]
        articulo = respuesta_json["info_producto"]
        pedido = respuesta_json["pedido"]
        respuesta_chat = respuesta_json["respuesta_sistema"]
        if intent == "5":
            respuesta_chat = respuesta_openai(f"[TEMA NO APLICA]", f"{respuesta_chat}")
        session['conversacion_previa'] += texto + "\n" + respuesta_chat + "\n"
        response = respuesta_chat
        return render_template('index.html', response=response, intent=intent, articulo=articulo, pedido=pedido)
    else:
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)





"""
conversacion_previa=""
while True:
    texto=input("Chat:")
    if texto=="exit":
        break
    respuesta=respuesta_openai(texto, conversacion_previa)
    respuesta_json=json.loads(respuesta)
    intent=respuesta_json["intent"]
    if intent=="5":
        respuesta_chat=respuesta_openai("[TEMA NO APLICA]", "")
    else:
        respuesta_chat=respuesta_json["respuesta_sistema"]
    print(f"Respuesta: {respuesta_chat}")
    conversacion_previa=conversacion_previa+texto+"\n"+respuesta_chat+"\n"
"""