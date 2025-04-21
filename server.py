# flask makes it so i can use an ngrok website as a host
from flask import Flask, request
from flask_socketio import SocketIO, emit, disconnect

# for the encryption. not 100% secure but this is eventually gonna get expanded on
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from pyngrok import ngrok

# secret key generation
from secrets import choice
from string import ascii_letters, digits

# other imports, bad practice :(
import os, threading

app = Flask(__name__)
app.config['SECRET_KEY'] = ''.join(choice(ascii_letters + digits) for _ in range(100))
socketio = SocketIO(app)

clients = {}
client_public_keys = {}
client_lock = threading.Lock()

global logs
logs = input("Would you like to store chat logs? (Y/N)\n> ")
while logs not in ["Y", "y", "N", "n"]:
    logs = input("Invalid answer. (Y/N)\n> ")
if logs.lower() == "y":
    LOG_DIR = "logs"
    LOG_FILE = os.path.join(LOG_DIR, "chat_log.txt")
    os.makedirs(LOG_DIR, exist_ok=True)

server_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
server_public_key = server_private_key.public_key()

def rsa_encrypt(public_key, message):
    return public_key.encrypt(
        message.encode('utf-8'),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )

def rsa_decrypt(private_key, ciphertext):
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    ).decode('utf-8')

def log_message(username, message):
    if logs.lower() == "y":
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(f'[{username}]: {message}\n')
    elif logs.lower() == "n":
        pass


@socketio.on('connect')
def handle_connect():
    server_public_key_pem = server_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    emit('server_public_key', server_public_key_pem)

@socketio.on('client_key')
def handle_client_key(client_key_pem):
    client_socket = request.sid
    client_public_key = serialization.load_pem_public_key(client_key_pem)

    with client_lock:
        client_public_keys[client_socket] = client_public_key

@socketio.on('set_username')
def handle_username(username):
    client_socket = request.sid
    
    with client_lock:
        if username in clients.values():
            emit('error', 'Username already taken.')
            disconnect()
            return
        clients[client_socket] = username
    broadcast(f'{username} has joined the chat.')

@socketio.on('message')
def handle_message(encrypted_message):
    client_socket = request.sid
    username = clients.get(client_socket)
    
    if not username:
        return

    try:
        decrypted_message = rsa_decrypt(server_private_key, encrypted_message)
    except Exception as e:
        print(f"Error decrypting message: {e}")
        return
    log_message(username, decrypted_message)
    broadcast(f'[{username}]: {decrypted_message}')

@socketio.on('disconnect')
def handle_disconnect():
    client_socket = request.sid
    username = clients.pop(client_socket, None)

    if username:
        broadcast(f'{username} has left the chat.')
        with client_lock:
            client_public_keys.pop(client_socket, None)

def broadcast(message):
    with client_lock:
        for client_socket, public_key in client_public_keys.items():
            try:
                encrypted_message = rsa_encrypt(public_key, message)
                socketio.emit('message', encrypted_message, room=client_socket)
            except Exception as e:
                print(f'Error sending message to {clients[client_socket]}: {e}')

if __name__ == '__main__':
    url = ngrok.connect("5555")
    print(f"URL: {url}")
    socketio.run(app, host='0.0.0.0', port=5555)