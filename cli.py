import socketio, threading, re
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

session = PromptSession()
sio = socketio.Client()

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

client_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
client_public_key = client_private_key.public_key()

@sio.event
def connect():
    print('Connected to server.')
    sio.emit('client_key', client_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

@sio.event
def server_public_key(public_key_pem):
    global server_public_key
    server_public_key = serialization.load_pem_public_key(public_key_pem)

    global username
    while True: 
        with patch_stdout():
            username = session.prompt("Username: ")
        if not username:
            continue
        if re.match("^[A-Za-z0-9_]{1,20}$", username) is not None:
            sio.emit('set_username', username)
            threading.Thread(target=send_message, daemon=True).start()
            break
        print("Invalid username")

@sio.event
def message(encrypted_message):
    try:
        message = rsa_decrypt(client_private_key, encrypted_message)
        print(message) if not message.startswith(f"[{username}]") else None
    except Exception as e:
        print(f"Error decrypting message: {e}")

@sio.event
def error(data):
    print(data)
    sio.disconnect()

@sio.event
def kick(data):
    print(data)
    sio.disconnect()

@sio.event
def disconnect():
    print("Disconnected from server.")

def send_message():
    while True:
        try:
            # patch_stdout makes sure other prints get buffered and the prompt is redrawn
            with patch_stdout():
                message = session.prompt("> ")
            if not message:
                continue
            if message.strip() == "/leave":
                print("Leaving.")
                sio.disconnect()
                break
            encrypted = rsa_encrypt(server_public_key, message)
            sio.emit('message', encrypted)
        except KeyboardInterrupt:
            sio.disconnect()
            print("KeyboardInterrupt")
            exit(1)

if __name__ == '__main__':
    link = input("Enter link: ")
    sio.connect(link)
    sio.wait()