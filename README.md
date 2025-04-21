## Basic Encrypted Chat

A simple encrypted chat application built with Flask, Flask-SocketIO, and RSA encryption. The server handles connections via a public ngrok URL and the client allows for users to connect, send, and receive encrypted messages.

---

### Features

- **End-to-end encryption** using RSA (2048-bit keys) for messages exchanged between clients and server.
- **Optional logging**: Persist chat logs to disk if enabled at startup.
- **Ngrok integration**: Exposes local server on a public URL automatically. This makes it easy to just send a link and get a private chat
- **Password locked rooms**: Not implimented yet, but the goal is to make it so you can lock these rooms with a password that is properly encrypted in transit both ways (if needed) but I have no ideas in my brain right now.

---

### Requirements

- Python 3.9+
- Pip
- Dependencies listed in `requirements.txt` idk exact versions but:
  ```text
  Flask
  flask-socketio
  pyngrok
  cryptography
  python-dotenv (optional)
  prompt_toolkit
  python-socketio
  ```
- The ngrok client. Install [here](https://ngrok.com/) or run `choco install ngrok` and create an account.
---


### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/gamerjamer43/encryptedchat
   cd secure-chat
   ```

2. **Create & activate a virtual environment (if you want)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # on Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

### Configuration

- **Environment variables** (optional):
  - `NGROK_AUTH_TOKEN`: Your ngrok auth token for stable tunnels.
  - `SECRET_KEY`: (Production) You could set a fixed SECRET_KEY to persist sessions across restarts. Not sure if you want to tho.

---

### Usage

#### Running the Server

1. Start the server:
   ```bash
   python server.py
   ```
2. Follow the prompt to enable logging:
   ```text
   Would you like to store chat logs? (Y/N)
   ```
3. The server will display a public URL via ngrok, e.g.:
   ```text
   URL: https://abcdef1234.ngrok-free.app
   ```
4. Share this link with clients.

#### Running the CLI Client

1. Launch the client:
   ```bash
   python cli.py
   ```
2. Enter the server link (from ngrok):
   ```text
   Enter link: https://abcdef1234.ngrok-free.app
   ```
3. Choose a username (alphanumeric and underscores, 1–20 chars).
4. Send messages. Type `/leave` to disconnect.

---

### Security Considerations

- **Key exchange**: Public keys are exchanged in plaintext; vulnerable to MitM attacks.
- **Logging**: Logs are stored unencrypted in `logs/chat_log.txt` if enabled.

To improve security:
- Deploy over HTTPS and secure ngrok tunnels.
- Use authenticated key exchange (e.g., Diffie-Hellman) or TLS.
- Store private keys and logs in secure, access-controlled storage.

---

### Project Structure

```
secure-chat/
├── server.py         # Flask & Socket.IO server
├── cli.py            # Command-line chat client
├── requirements.txt  # Python dependencies
└── logs/             # Chat logs (if enabled)
```