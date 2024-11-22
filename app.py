import json
from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, disconnect
from datetime import datetime
import eventlet
eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Carregar usuários do arquivo JSON
def load_users():
    try:
        with open('usuarios.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Salvar usuários no arquivo JSON
def save_users(users):
    with open('usuarios.json', 'w') as f:
        json.dump(users, f, indent=2)

# Dicionário para armazenar as sessões de usuário
usuarios_conectados = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('set_user')
def handle_set_user(username):
    usuarios = load_users()  # Carregar usuários ao tentar autenticar
    usuario = next((u for u in usuarios if u['nome'] == username), None)
    
    if usuario:
        usuarios_conectados[request.sid] = usuario['nome']
        send(f'Bem-vindo, {usuario["nome"]}!', broadcast=False)

        # Carregar as mensagens anteriores de todos os usuários
        all_messages = load_chat_messages()
        for msg in all_messages:
            send(msg, broadcast=False)  # Envia todas as mensagens antigas ao novo usuário
    else:
        send('Usuário não encontrado no sistema.', broadcast=False)
        disconnect()

@socketio.on('message')
def handle_message(msg):
    user_name = usuarios_conectados.get(request.sid, 'Desconhecido')

    # Enviar a mensagem para todos os usuários conectados
    send(f'{user_name}: {msg}', broadcast=True)

    # Salvar a mensagem no arquivo JSON
    all_messages = load_chat_messages()
    all_messages.append(f'{user_name}: {msg}')
    save_chat_messages(all_messages)

@socketio.on('disconnect')
def handle_disconnect():
    user_name = usuarios_conectados.get(request.sid, 'Desconhecido')
    usuarios_conectados.pop(request.sid, None)

def load_chat_messages():
    """Carregar mensagens do chat de um arquivo (persistência)"""
    try:
        with open('chat_messages.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_chat_messages(messages):
    """Salvar mensagens no arquivo (persistência)"""
    with open('chat_messages.json', 'w') as f:
        json.dump(messages, f, indent=2)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

